# Instal·lació de KOT7K

## Instal·lació nova

En Debian/Ubuntu amb systemd i accés sudo (recomanat Ubuntu 24.04+ o Debian 13+):

```bash
git clone <URL-del-repositori> /opt/kot7k
/opt/kot7k/devops/scripts/install.sh
```

Si `/opt/kot7k` ja existeix, utilitza un altre directori:

```bash
git clone <URL-del-repositori> /opt/kot7k-nou
/opt/kot7k-nou/devops/scripts/install.sh
```

No cal executar-lo des d'un directori concret. `install.sh` i `build-ui.sh`
calculen l'arrel a partir de la seva ubicació. No es trasllada ni s'esborra
l'altra instal·lació. El directori no pot contenir espais ni caràcters especials.
Es recomana `/opt/`: Nginx ha de poder travessar els directoris pare per servir
els estàtics de Django.

L'instal·lador demana el domini, l'email, el nom complet i la contrasenya de
l'administrador inicial. La contrasenya es demana dues vegades, no es mostra
ni es passa a la línia de comandes i es valida amb les regles de Django.
Certbot també demana el correu de registre i l'acceptació de les condicions
de Let's Encrypt si encara no hi ha cap compte registrat.

## Requisits de xarxa

L'instal·lador pregunta si vols configurar el certificat local:

- **Sí**: Nginx i TLS en aquest servidor. El DNS A/AAAA i els ports 80/443 han
  d'arribar-hi. Certbot emet el certificat i configura la renovació.
- **No**: TLS en un proxy extern. No comprova DNS, no instal·la ni executa Certbot
  i no exigeix port 443 local. Demana la IP o xarxa del proxy (separades per comes),
  i Nginx només accepta aquest origen i localhost pel port 80. L'origen públic
  de l'app continua sent `https://<domini>`; cookies i redireccions segueixen sent HTTPS.

En el segon mode, configura el proxy extern per acabar TLS, redirigir HTTP públic
cap a HTTPS i enviar les peticions al port 80 del servidor de l'app, conservant
la capçalera Host. El certificat i la renovació són responsabilitat del proxy.
La IP que cal introduir és la que Nginx veu com a origen de la connexió (després de
NAT, si n'hi ha). No es confien capçaleres de qualsevol origen d'Internet.

No es modifiquen DNS, tallafocs, NAT ni el proxy extern. Cal accés a Internet per
instal·lar paquets. Si el domini ja figura en Nginx, o un clon nou té `api/.env`,
l'instal·lador s'atura abans de substituir configuracions existents.
L'elecció queda guardada i es reutilitza en reexecucions i en `update.sh`.

## Què configura

- Paquets del sistema, PostgreSQL local, Nginx i Certbot.
- Node 22 x64/arm64 en `/opt/kot7k-runtimes`, descarregat de nodejs.org i verificat
  amb SHA-256, sense substituir el Node d'altres projectes.
- Entorn Python a `api/.venv`, dependències i migracions.
- Base de dades i rol propis, amb contrasenya aleatòria.
- `api/.env` privat (0600): clau Django, clau RSA OIDC, xifratge dels secrets,
  domini públic, connexió PostgreSQL i cookies HTTPS.
- Administrador inicial actiu amb permisos de plataforma i Django admin.
- `collectstatic` a `api/static_dist` i build Next a `api/ui_dist`, amb l'API HTTPS
  del domini introduït. No s'utilitza `next start` en producció.
- Servei Gunicorn no root amb socket Unix privat compartit amb Nginx.
- Nginx: HTTP redirigeix a HTTPS, `/static/` serveix els recursos de Django i la
  resta va a Django, inclosa la UI i les capçaleres específiques de logout.
- En mode TLS local: certificat Let's Encrypt, renovació automàtica i recàrrega de Nginx.
- Timer cada minut per reintentar notificacions pendents de logout SSO.
- Comprovacions de Django, salut de l'API, sintaxi Nginx i resposta HTTPS local.

Si el clon pertany a un usuari no root, aquest és l'usuari del servei i dels
builds. Si pertany a root, es crea un usuari de sistema propi i se li transfereix
la propietat del clon. En aquest últim cas les actualitzacions Git s'han de fer
com aquest usuari (o amb sudo). No s'executen pip ni npm com a root.

## Reexecució i actualitzacions

El servei es diu `kot7k-<hash-del-directori>`; el nom exacte es mostra en executar
l'instal·lador. Cada clon té també la seva base de dades, socket, lloc Nginx i timer.
L'estat queda a `/etc/kot7k/kot7k-<hash>.json`, llegible només per root.

Si una fase falla, corregeix-ne la causa i torna a executar el mateix script des
del mateix clon. Es preserven les claus i les contrasenyes; si ja existeix un
administrador actiu no se'n crea un altre ni se'n canvia la contrasenya. Una
configuració Nginx que no passa `nginx -t` es restaura a la versió anterior.

No hi ha rollback global dels paquets ni de les migracions. Fes còpia de seguretat
de PostgreSQL i `api/.env` abans d'actualitzar una instal·lació amb dades.
L'instal·lador no executa `git pull`: actualitza el clon i torna a executar-lo.
No canviïs el nom o la ubicació del clon després de la instal·lació.

Per reconstruir només la UI:

```bash
/opt/kot7k-nou/devops/scripts/build-ui.sh
```

`clients/web/.env.production.local` conserva l'origen de l'API. No afegeixis
un `.env.local` de desenvolupament al clon de producció.

Diagnòstic (substitueix el nom pel servei mostrat):

```bash
sudo systemctl status kot7k-<hash>
sudo journalctl -u kot7k-<hash> -n 100 --no-pager
sudo nginx -t
sudo certbot certificates
sudo systemctl status certbot.timer
```

La ruta antiga `devops/systemd/kot7k.service` és una configuració manual anterior;
l'instal·lador no la fa servir ni la modifica.

## Validació dels scripts

```bash
python3 -m unittest discover -s devops/scripts/tests -v
bash -n devops/scripts/install.sh devops/scripts/build-ui.sh
cd api
.venv/bin/python manage.py test kot7k.authentication.tests.test_commands config.test_ui --settings=config.test_settings
```

Les proves automatitzades cobreixen generació, validació, aïllament, restauració
Nginx i bootstrap d'usuaris. La instal·lació completa de paquets, systemd i un
certificat real s'ha de validar en un servidor Linux amb el DNS i els ports preparats.

## Actualització automàtica

Per a una instal·lació registrada pel nou `install.sh`:

```bash
/opt/kot7k/devops/scripts/update.sh
# O, si el clon és en un altre directori:
/opt/kot7k-nou/devops/scripts/update.sh
```

L'script demana sudo si cal i obté domini, usuari i serveis de l'estat guardat.
No torna a preguntar credencials ni modifica `.env`, el certificat o Nginx.

1. Rebutja canvis locals, fitxers sense versionar, detached HEAD o commits locals.
2. Fa `git fetch` i avança la branca actual cap al seu upstream amb `--ff-only`.
3. Atura l'API i els reintents SSO durant la instal·lació de dependències, el build,
   les migracions i `collectstatic`. Hi ha una finestra de manteniment.
4. Reinicia l'API, activa PostgreSQL, Nginx i els timers, i recarrega Nginx.
5. Executa un reintent SSO, verifica els serveis i comprova l'API pel socket Unix
   i el login, l'API i el logout per HTTPS amb validació del certificat.

Encara que no hi hagi commits nous, repeteix el desplegament i les comprovacions:
així es pot reprendre una actualització parcial. No executa actualitzacions apt,
no emet certificats nous i no regenera claus ni usuaris. Els fitxers d'unitats i
Nginx no es regeneren; canvis futurs d'infraestructura necessiten revisió separada.

Git s'executa com l'usuari propietari de la instal·lació, que ha de tenir accés
al repositori remot (p. ex. clau SSH pròpia per a repositoris privats). No s'utilitzen
les credencials Git de root ni es fan `reset --hard` o `stash` automàtics.

Si falla una fase després de l'aturada, intenta tornar a arrencar l'API i el timer,
però retorna error. **Això no és un rollback**: les dependències, el codi i les
migracions poden haver canviat. Conserva una còpia de PostgreSQL i `api/.env`
abans d'actualitzar. Corregeix l'error i repeteix `update.sh`.

La comprovació HTTPS es fa contra el Nginx local amb el domini i el certificat
reals. No substitueix una comprovació externa del DNS, el tallafoc o un altre proxy.
Les instal·lacions manuals antigues sense `/etc/kot7k/kot7k-<hash>.json` es rebutgen
abans de tocar Git o serveis; no creïs aquest fitxer a mà per forçar-ne l'ús.

## Python automàtic

`install.sh` busca Python 3.12–3.14 al venv del clon, al PATH, a `/usr/local/bin`
i als runtimes privats. Si no el troba, instal·la uv en un entorn aïllat i descarrega
Python 3.13 a `/opt/kot7k-runtimes/python`. No canvia `/usr/bin/python3`.
No cal activar cap entorn. `update.sh` reutilitza el runtime instal·lat.

Això també permet preparar Python en sistemes com Ubuntu 22.04 o Debian 12;
la compatibilitat de la resta de paquets s'ha de validar en el servidor concret.
Cal accés a PyPI i als repositoris de binaris d'Astral/GitHub.
Si ja hi ha un `api/.venv` incompatible, es rebutja sense esborrar-lo: cal conservar-lo
amb un altre nom abans de repetir la instal·lació. Un runtime instal·lat sota
`/root` pot no ser accessible per l'usuari del servei; utilitza el runtime compartit.

En mode proxy extern, `update.sh` no exigeix `certbot.timer` i verifica el Nginx
local per HTTP amb la capçalera Host. No valida el certificat del proxy extern.
Els estats antics sense l'opció `configure_tls` conserven el mode TLS local.
