#!/usr/bin/env python3
"""Single-host installer. All system mutations live in main(); helpers are testable."""
import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import pwd
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MARKER = "# Managed by KOT7K installer"


def run(*args, **kwargs):
    return subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def domain_name(value):
    value = value.strip().lower().rstrip(".")
    if len(value) > 253 or "." not in value or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
        for part in value.split(".")
    ) or value.replace(".", "").isdigit():
        raise ValueError("Introdueix un domini DNS, sense https://, port ni ruta.")
    return value


def instance_id(root):
    return "kot7k-" + hashlib.sha256(str(root).encode()).hexdigest()[:12]


def write_atomic(path, content, mode=0o644):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".install-tmp")
    with temporary.open("w") as stream:
        os.chmod(temporary, mode)
        stream.write(content)
    temporary.replace(path)


def unit(root, account, instance):
    return f"""{MARKER}
[Unit]
Description=KOT7K ({root})
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User={account}
Group=www-data
WorkingDirectory={root}/api
RuntimeDirectory={instance}
RuntimeDirectoryMode=0750
UMask=0007
ExecStart={root}/api/.venv/bin/gunicorn --workers 3 --bind unix:/run/{instance}/app.sock --access-logfile - --error-logfile - config.wsgi:application
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""


def nginx_config(root, domain, instance, tls=False):
    challenge = f"""    location ^~ /.well-known/acme-challenge/ {{
        root /var/lib/letsencrypt;
    }}
"""
    http = f"""{MARKER}
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
{challenge}    location / {{ {'return 301 https://' + domain + '$request_uri;' if tls else 'return 503;'} }}
}}
"""
    if not tls:
        return http
    return http + f"""
server {{
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name {domain};
    ssl_certificate /etc/letsencrypt/live/{instance}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{instance}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 10m;
    location /static/ {{
        alias {root}/api/static_dist/;
    }}
    location / {{
        proxy_pass http://unix:/run/{instance}/app.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }}
}}
"""


def proxy_networks(value):
    networks = [str(ipaddress.ip_network(part.strip(), strict=False)) for part in value.split(",") if part.strip()]
    if not networks:
        raise ValueError("Indica almenys una IP del proxy HTTPS.")
    if any(ipaddress.ip_network(network).prefixlen == 0 for network in networks):
        raise ValueError("No es permet confiar en totes les IP d’Internet.")
    return networks


def proxy_nginx_config(domain, instance, networks):
    allowed = "\n".join(f"    allow {network};" for network in networks)
    return f"""{MARKER}
# TLS terminates at the trusted upstream proxy. Block direct public access.
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    allow 127.0.0.1;
    allow ::1;
{allowed}
    deny all;
    client_max_body_size 10m;
    location /static/ {{
        alias {ROOT}/api/static_dist/;
    }}
    location / {{
        proxy_pass http://unix:/run/{instance}/app.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 120s;
    }}
}}
"""


def install_nginx(path, content, enabled_directory=Path("/etc/nginx/sites-enabled")):
    """Restore the previous configuration if validation fails."""
    path = Path(path)
    previous = path.read_text() if path.exists() else None
    if previous and not previous.startswith(MARKER):
        raise RuntimeError(f"No sobreescric una configuració aliena: {path}")
    enabled = enabled_directory / path.name
    if enabled.is_symlink() and enabled.resolve() != path.resolve():
        raise RuntimeError(f"Enllaç Nginx ocupat: {enabled}")
    if enabled.exists() and not enabled.is_symlink():
        raise RuntimeError(f"Fitxer Nginx ocupat: {enabled}")
    had_link = enabled.is_symlink()
    write_atomic(path, content)
    if not had_link:
        enabled.symlink_to(path)
    try:
        run("nginx", "-t")
    except subprocess.CalledProcessError:
        if previous is None:
            path.unlink()
        else:
            write_atomic(path, previous)
        if not had_link:
            enabled.unlink()
        raise
    run("systemctl", "reload", "nginx")


def install_node():
    """Private Node 22 runtime, without replacing the system Node installation."""
    arch = {"x86_64": "x64", "aarch64": "arm64"}.get(platform.machine())
    if not arch:
        raise RuntimeError("Arquitectura no suportada; cal x86_64 o aarch64.")
    base = "https://nodejs.org/dist/latest-v22.x/"
    sums = urllib.request.urlopen(base + "SHASUMS256.txt", timeout=60).read().decode()
    candidates = [line.split() for line in sums.splitlines() if line.endswith(f"-linux-{arch}.tar.xz")]
    if len(candidates) != 1:
        raise RuntimeError("No s’ha pogut resoldre el paquet oficial de Node 22.")
    checksum, filename = candidates[0]
    if not re.fullmatch(r"node-v22\.\d+\.\d+-linux-(x64|arm64)\.tar\.xz", filename):
        raise RuntimeError("Nom de paquet Node inesperat.")
    destination = Path("/opt/kot7k-runtimes") / filename.removesuffix(".tar.xz")
    if not (destination / "bin/node").is_file():
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / filename
            with urllib.request.urlopen(base + filename, timeout=120) as source, archive.open("wb") as target:
                shutil.copyfileobj(source, target)
            if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
                raise RuntimeError("Checksum de Node incorrecte.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            run("tar", "-xJf", archive, "-C", destination.parent, "--no-same-owner")
    return destination / "bin"


def main():
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Executa install.sh en un servidor Linux amb sudo.")
    if not (3, 12) <= sys.version_info[:2] < (3, 15):
        raise RuntimeError("Cal Python 3.12–3.14. Executa install.sh perquè el prepari automàticament.")
    if not Path("/run/systemd/system").exists() or not shutil.which("apt-get"):
        raise RuntimeError("Cal Debian/Ubuntu amb systemd i apt-get.")
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", str(ROOT)):
        raise RuntimeError("El directori del clon no pot contenir espais ni caràcters especials.")
    for file in ("api/manage.py", "api/requirements.txt", "clients/web/package-lock.json"):
        if not (ROOT / file).is_file():
            raise RuntimeError(f"Clon incomplet: falta {file}.")
    import fcntl
    lock = open("/run/lock/kot7k-install.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("Ja hi ha un instal·lador KOT7K en execució.") from exc
    instance = instance_id(ROOT)
    state_file = Path("/etc/kot7k") / (instance + ".json")
    state = json.loads(state_file.read_text()) if state_file.exists() else None
    print(f"Instal·lació: {ROOT}\nServei: {instance}", flush=True)
    if state:
        if state["root"] != str(ROOT):
            raise RuntimeError("La instal·lació registrada correspon a un altre directori.")
        domain, account = state["domain"], state["account"]
        print(f"Reprenent {domain}; es conservaran les claus i els usuaris.")
    else:
        if (ROOT / "api/.env").exists():
            raise RuntimeError("Aquest clon ja té api/.env. Per a una instal·lació nova utilitza un clon net; no se sobreescriuran les dades existents.")
        domain = domain_name(input("Domini públic (p. ex. idp.abaqua.cat): "))
        answer = input("Vols configurar el certificat HTTPS amb Let’s Encrypt en aquest servidor? [S/n]: ").strip().lower()
        if answer not in ("", "s", "si", "sí", "n", "no"):
            raise ValueError("Respon s o n.")
        configure_tls = answer not in ("n", "no")
        trusted_proxies = []
        if configure_tls:
            try:
                socket.getaddrinfo(domain, 80)
            except socket.gaierror as exc:
                raise RuntimeError(f"El domini {domain} encara no resol per DNS. Configura el DNS o escull no configurar el certificat local.") from exc
        else:
            trusted_proxies = proxy_networks(input("IP del proxy HTTPS que connectarà a aquest servidor (separades per comes): "))
        account = pwd.getpwuid(ROOT.stat().st_uid).pw_name
        if account == "root":
            account = instance
        # A domain must not be taken over from another checkout or Nginx site.
        for folder in ("/etc/nginx/sites-enabled", "/etc/nginx/conf.d"):
            for file in Path(folder).glob("*"):
                if file.is_file():
                    text = file.read_text()
                    if any(domain in names.split() for names in re.findall(r"server_name\s+([^;]+);", text)):
                        raise RuntimeError(f"El domini ja està configurat a {file}. No el sobreescriuré.")
        state = {"root": str(ROOT), "domain": domain, "account": account, "configure_tls": configure_tls, "trusted_proxies": trusted_proxies}
        write_atomic(state_file, json.dumps(state, indent=2) + "\n", 0o600)
    configure_tls = state.get("configure_tls", True)
    if configure_tls:
        print("Mode: HTTPS local. El DNS i els ports 80/443 han d’arribar a aquest servidor.", flush=True)
    else:
        print("Mode: proxy HTTPS extern. Sense comprovació DNS ni Certbot local.", flush=True)
    environment = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    run("apt-get", "update", env=environment)
    run("apt-get", "install", "-y", "python3-venv", "python3-dev", "build-essential", "libpq-dev",
        "postgresql", "nginx", "ca-certificates", "curl", "xz-utils", "openssl",
        *(["certbot"] if configure_tls else []), env=environment)
    run("systemctl", "enable", "--now", "postgresql", "nginx")
    try:
        user = pwd.getpwnam(account)
    except KeyError:
        run("useradd", "--system", "--create-home", "--shell", "/usr/sbin/nologin", account)
        user = pwd.getpwnam(account)
    if ROOT.stat().st_uid == 0:
        run("chown", "-R", f"{account}:{user.pw_gid}", ROOT)
    node_bin = install_node()
    def app(*args, cwd=None, **kwargs):
        return run("runuser", "-u", account, "--", "env", "-i", f"HOME={user.pw_dir}", "LANG=C.UTF-8", f"PATH={node_bin}:/usr/local/bin:/usr/bin:/bin",
                   *args, cwd=cwd or ROOT / "api", **kwargs)
    python = ROOT / "api/.venv/bin/python"
    if python.exists():
        compatible = subprocess.run([str(python), "-c", "import sys; assert (3, 12) <= sys.version_info[:2] < (3, 15)"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if not compatible:
            raise RuntimeError("api/.venv ja existeix amb un Python incompatible. Conserva’l amb un altre nom i repeteix install.sh; no s’esborrarà automàticament.")
    else:
        app(sys.executable, "-m", "venv", ROOT / "api/.venv")
    app(python, "-m", "pip", "install", "--upgrade", "pip")
    app(python, "-m", "pip", "install", "-r", "requirements.txt")
    env_file = ROOT / "api/.env"
    if not env_file.exists():
        db_password = secrets.token_urlsafe(48)
        private_key = subprocess.check_output(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:3072"], stderr=subprocess.DEVNULL).decode().strip()
        values = {
            "SECRET_KEY": secrets.token_urlsafe(64), "DEBUG": "false", "ALLOWED_HOSTS": domain,
            "DATABASE_ENVIRONMENT": "production", "PROD_POSTGRES_DB": instance.replace("-", "_"),
            "PROD_POSTGRES_USER": instance.replace("-", "_"), "PROD_POSTGRES_PASSWORD": db_password,
            "PROD_POSTGRES_HOST": "127.0.0.1", "PROD_POSTGRES_PORT": "5432", "PROD_POSTGRES_SSLMODE": "prefer",
            "OIDC_ISSUER": f"https://{domain}", "OIDC_FRONTEND_URL": f"https://{domain}",
            "EXTERNAL_AUTH_CALLBACK_BASE_URL": f"https://{domain}",
            "OIDC_PRIVATE_KEY": private_key.replace("\n", "\\n"), "OIDC_KEY_ID": instance,
            "IDENTITY_PROVIDER_ENCRYPTION_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
            "SESSION_COOKIE_SECURE": "true", "CSRF_COOKIE_SECURE": "true", "SECURE_SSL_REDIRECT": "true",
            "CSRF_TRUSTED_ORIGINS": f"https://{domain}",
        }
        write_atomic(env_file, "\n".join(f"{key}='{value}'" for key, value in values.items()) + "\n", 0o600)
        os.chown(env_file, user.pw_uid, user.pw_gid)
    # Read only generated DB values; never source an environment file as shell code.
    result = app(python, "-c", "import json; from dotenv import dotenv_values; v=dotenv_values('.env'); print(json.dumps([v['PROD_POSTGRES_USER'],v['PROD_POSTGRES_PASSWORD'],v['PROD_POSTGRES_DB']]))", capture_output=True, text=True)
    db_user, db_password, db_name = json.loads(result.stdout)
    if not all(re.fullmatch(r"[a-z0-9_]+", value) for value in (db_user, db_name)):
        raise RuntimeError("Nom de base de dades inattendu.")
    literal = db_password.replace("'", "''")
    sql = f"""SELECT format('CREATE ROLE %I LOGIN', '{db_user}') WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname='{db_user}')\\gexec
ALTER ROLE "{db_user}" PASSWORD '{literal}';
SELECT format('CREATE DATABASE %I OWNER %I', '{db_name}', '{db_user}') WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname='{db_name}')\\gexec
"""
    run("runuser", "-u", "postgres", "--", "psql", "-v", "ON_ERROR_STOP=1", input=sql, text=True, cwd="/tmp", stdout=subprocess.DEVNULL)
    app(python, "manage.py", "migrate", "--noinput")
    app(python, "manage.py", "bootstrap_admin")
    app(python, "manage.py", "collectstatic", "--noinput")
    run("runuser", "-u", "www-data", "--", "test", "-r", ROOT / "api/static_dist/admin/css/base.css")
    app(python, "manage.py", "check", "--deploy", "--fail-level", "ERROR")
    public_env = ROOT / "clients/web/.env.production.local"
    public_lines = public_env.read_text().splitlines() if public_env.exists() else []
    public_lines = [line for line in public_lines if not line.startswith("NEXT_PUBLIC_API_BASE_URL=")]
    write_atomic(public_env, "\n".join([*public_lines, f"NEXT_PUBLIC_API_BASE_URL=https://{domain}"]) + "\n")
    os.chown(public_env, user.pw_uid, user.pw_gid)
    app("npm", "ci", cwd=ROOT / "clients/web")
    app("env", f"NEXT_PUBLIC_API_BASE_URL=https://{domain}", "npm", "run", "build", cwd=ROOT / "clients/web")
    service_path = Path("/etc/systemd/system") / (instance + ".service")
    if service_path.exists() and not service_path.read_text().startswith(MARKER):
        raise RuntimeError(f"Servei existent no gestionat: {service_path}")
    write_atomic(service_path, unit(ROOT, account, instance))
    retry_service = Path("/etc/systemd/system") / (instance + "-logout.service")
    retry_timer = Path("/etc/systemd/system") / (instance + "-logout.timer")
    for managed in (retry_service, retry_timer):
        if managed.exists() and not managed.read_text().startswith(MARKER):
            raise RuntimeError(f"Servei existent no gestionat: {managed}")
    write_atomic(retry_service, f"""{MARKER}
[Unit]
Description=KOT7K pending SSO logout notifications
After=postgresql.service
[Service]
Type=oneshot
User={account}
WorkingDirectory={ROOT}/api
ExecStart={python} manage.py retry_logout_notifications
NoNewPrivileges=true
PrivateTmp=true
""")
    write_atomic(retry_timer, f"""{MARKER}
[Unit]
Description=Retry KOT7K SSO logout every minute
[Timer]
OnBootSec=60
OnUnitInactiveSec=60
[Install]
WantedBy=timers.target
""")
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "--now", instance + "-logout.timer")
    run("systemctl", "enable", instance)
    run("systemctl", "restart", instance)
    for attempt in range(30):
        check = subprocess.run(["curl", "--silent", "--fail", "--unix-socket", f"/run/{instance}/app.sock",
                                "-H", f"Host: {domain}", "-H", "X-Forwarded-Proto: https", "http://localhost/api/identity-providers/discovery/"], stdout=subprocess.DEVNULL)
        if check.returncode == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError(f"L’API no respon. Consulta journalctl -u {instance}.")
    site = Path("/etc/nginx/sites-available") / instance
    if configure_tls:
        certificate = Path(f"/etc/letsencrypt/live/{instance}/fullchain.pem")
        Path("/var/lib/letsencrypt/.well-known/acme-challenge").mkdir(parents=True, exist_ok=True)
        install_nginx(site, nginx_config(ROOT, domain, instance, tls=certificate.exists()))
        # Certbot asks for its registration email and acceptance of Let's Encrypt terms.
        run("certbot", "certonly", "--webroot", "-w", "/var/lib/letsencrypt", "--cert-name", instance,
            "-d", domain, "--keep-until-expiring")
        install_nginx(site, nginx_config(ROOT, domain, instance, tls=True))
        write_atomic(Path("/etc/letsencrypt/renewal-hooks/deploy/kot7k-nginx"), "#!/bin/sh\nnginx -t && systemctl reload nginx\n", 0o755)
        run("systemctl", "enable", "--now", "certbot.timer")
        run("curl", "--fail", "--silent", "--show-error", "--resolve", f"{domain}:443:127.0.0.1", f"https://{domain}/authentication/login", "-o", "/dev/null")
    else:
        install_nginx(site, proxy_nginx_config(domain, instance, state["trusted_proxies"]))
        run("curl", "--fail", "--silent", "--show-error", "--max-time", "15", "-H", f"Host: {domain}",
            "http://127.0.0.1/authentication/login", "-o", "/dev/null")
        print(f"Configura el proxy extern per enviar https://{domain} a HTTP port 80 d’aquest servidor, conservant Host.")
    print(f"\nKOT7K instal·lat: https://{domain}\nServei: {instance}\nClon: {ROOT}\n")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        # Avoid printing subprocess arguments: secrets may be supplied over stdin.
        print(f"\nInstal·lació interrompuda: {error}\nCorregeix l’error i torna a executar install.sh des del mateix clon.", file=sys.stderr)
        sys.exit(1)
