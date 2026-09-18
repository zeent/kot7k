#!/usr/bin/env python3
"""Update an existing managed checkout, without recreating its configuration."""
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import time

from install import ROOT, domain_name, instance_id, run


def update_git(app, root):
    def git(*args):
        return app("git", *args, cwd=root, capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise RuntimeError("El clon té canvis locals o fitxers sense versionar. Desa’ls abans d’actualitzar; no es descartaran.")
    if not git("branch", "--show-current"):
        raise RuntimeError("El clon està en detached HEAD; selecciona una branca amb upstream.")
    git("rev-parse", "--abbrev-ref", "@{upstream}")
    before = git("rev-parse", "HEAD")
    # Fetch only the configured upstream; no guessed origin or branch names.
    git("fetch", "--prune")
    ahead, behind = map(int, git("rev-list", "--left-right", "--count", "HEAD...@{upstream}").split())
    if ahead:
        raise RuntimeError("La branca té commits locals o ha divergit. No es farà cap reset ni merge automàtic.")
    if behind:
        git("merge", "--ff-only", "@{upstream}")
    return before, git("rev-parse", "HEAD")


def node_runtime():
    candidates = []
    for directory in Path("/opt/kot7k-runtimes").glob("node-v22.*-linux-*"):
        match = re.fullmatch(r"node-v(22)\.(\d+)\.(\d+)-linux-(?:x64|arm64)", directory.name)
        if match and (directory / "bin/node").is_file():
            candidates.append((tuple(map(int, match.groups())), directory / "bin"))
    if not candidates:
        raise RuntimeError("Falta el runtime Node de la instal·lació. Revisa install.sh.")
    return max(candidates)[1]


def verify_http(domain, instance, configure_tls=True):
    for attempt in range(15):
        response = subprocess.run([
            "curl", "--silent", "--show-error", "--fail", "--max-time", "5",
            "--unix-socket", f"/run/{instance}/app.sock", "-H", f"Host: {domain}",
            "-H", "X-Forwarded-Proto: https", "http://localhost/api/identity-providers/discovery/",
        ], capture_output=True, text=True)
        if response.returncode == 0:
            try:
                if isinstance(json.loads(response.stdout), list):
                    break
            except ValueError:
                pass
        time.sleep(1)
    else:
        raise RuntimeError("L’API no respon correctament després del reinici.")
    for path in ("/authentication/login", "/api/identity-providers/discovery/", "/authentication/front-channel-logout"):
        target = ["--resolve", f"{domain}:443:127.0.0.1", f"https://{domain}{path}"] if configure_tls else ["-H", f"Host: {domain}", f"http://127.0.0.1{path}"]
        result = run("curl", "--silent", "--show-error", "--fail", "--max-time", "15",
                     "-o", "/dev/null", "-w", "%{http_code}", *target, capture_output=True, text=True)
        if result.stdout != "200":
            raise RuntimeError(f"HTTPS {path}: s’esperava 200, rebut {result.stdout}.")


def deploy(app, root, instance, domain, configure_tls=True):
    python = root / "api/.venv/bin/python"
    # Validate Nginx before stopping any application process.
    run("nginx", "-t")
    run("systemctl", "enable", "--now", "postgresql")
    timer = instance + "-logout.timer"
    try:
        run("systemctl", "stop", timer, instance + "-logout.service", instance)
        app(python, "-m", "pip", "install", "-r", "requirements.txt")
        app("npm", "ci", cwd=root / "clients/web")
        app("env", f"NEXT_PUBLIC_API_BASE_URL=https://{domain}", "npm", "run", "build", cwd=root / "clients/web")
        app(python, "manage.py", "check", "--deploy", "--fail-level", "ERROR")
        app(python, "manage.py", "migrate", "--noinput")
        app(python, "manage.py", "collectstatic", "--noinput")
    finally:
        # Even a failed build must not silently leave the app and retry timer stopped.
        # This is service recovery, not a rollback of code, dependencies or schema.
        for service in (instance, timer):
            result = subprocess.run(["systemctl", "start", service])
            if result.returncode:
                print(f"No s’ha pogut recuperar {service}; consulta journalctl -u {service}.", file=sys.stderr)
    run("systemctl", "daemon-reload")
    run("systemctl", "restart", instance)
    certificate_services = ["certbot.timer"] if configure_tls else []
    run("systemctl", "enable", "--now", instance, "nginx", timer, *certificate_services)
    run("systemctl", "reload", "nginx")
    # Run the oneshot job once to detect errors hidden behind an active timer.
    run("systemctl", "start", instance + "-logout.service")
    for service in ("postgresql", instance, "nginx", timer, *certificate_services):
        run("systemctl", "is-active", "--quiet", service)
    verify_http(domain, instance, configure_tls=configure_tls)


def main():
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Executa update.sh en Linux amb sudo.")
    import fcntl
    lock = open("/run/lock/kot7k-install.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError("Ja hi ha una instal·lació o actualització en curs.") from exc
    instance = instance_id(ROOT)
    state_file = Path("/etc/kot7k") / (instance + ".json")
    if not state_file.is_file():
        raise RuntimeError("Aquest clon no està registrat per install.sh. No es modificaran els serveis d’una instal·lació manual.")
    state = json.loads(state_file.read_text())
    if state["root"] != str(ROOT):
        raise RuntimeError("El directori no coincideix amb la instal·lació registrada.")
    domain = domain_name(state["domain"])
    user = pwd.getpwnam(state["account"])
    node_bin = node_runtime()
    for file in (ROOT / "api/.env", ROOT / "api/.venv/bin/python",
                 Path("/etc/systemd/system") / (instance + ".service"),
                 Path("/etc/systemd/system") / (instance + "-logout.timer"),
                 Path("/etc/nginx/sites-enabled") / instance):
        if not file.exists():
            raise RuntimeError(f"Instal·lació incompleta: falta {file}. Reprèn install.sh.")
    def app(*args, cwd=None, **kwargs):
        return run("runuser", "-u", user.pw_name, "--", "env", "-i", f"HOME={user.pw_dir}",
                   "LANG=C.UTF-8", f"PATH={node_bin}:/usr/local/bin:/usr/bin:/bin",
                   *args, cwd=cwd or ROOT / "api", **kwargs)
    print(f"Actualitzant {ROOT} ({domain})…", flush=True)
    before, after = update_git(app, ROOT)
    print(f"Git: {before[:12]} → {after[:12]}", flush=True)
    deploy(app, ROOT, instance, domain, configure_tls=state.get("configure_tls", True))
    print(f"Actualització completada: https://{domain}\nAPI, Nginx, PostgreSQL, timers i connexió local verificats.")


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print(f"Actualització fallida: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr, file=sys.stderr)
        print("No s’ha fet rollback automàtic. Revisa l’error i torna a executar update.sh.", file=sys.stderr)
        sys.exit(1)
