# Logout central de KOT7K

La sessió del navegador té un `sid` compartit entre els tokens de la UI i els tokens OIDC de les apps. Sortir de KOT7K revoca aquesta sessió; no totes les sessions de l'usuari en altres navegadors o dispositius. No es crida cap endpoint de logout de Microsoft.

## Integració a cada app (pendent a Talaia i Lynkr)

1. Desa `iss`, `sub` i `sid` de l'ID token validat amb la sessió local de l'app.
2. Implementa un endpoint POST de back-channel logout. Valida la signatura RS256 amb el JWKS de KOT7K, `iss`, `aud` igual al teu client ID, `iat`, `exp`, `jti`, `sid` i l'esdeveniment `http://schemas.openid.net/event/backchannel-logout`. Rebutja tokens amb `nonce` i tokens normals d'accés/ID. Rebutja repeticions de `jti` sense repetir efectes; retorna 200 si la sessió ja està tancada.
3. Invalida al servidor totes les sessions locals d'aquest emissor i `sid`, així com qualsevol ús posterior de tokens associats. Cada petició de l'app ha de comprovar que la sessió local continuï activa. Comprovar només la signatura d'un JWT no detecta una revocació abans de la seva caducitat.
4. Per sortir de tot l'ecosistema, redirigeix el navegador a l'`end_session_endpoint` publicat a `/.well-known/openid-configuration`, amb `id_token_hint`, `post_logout_redirect_uri` i `state`. KOT7K demana confirmació protegida per CSRF i retorna al destí registrat. L'app ha de verificar el `state` de retorn.
5. Si ofereixes «Sortir només d'aquesta app», invalida només la sessió local i revoca el seu refresh token via `/oauth/revoke/`. KOT7K continuarà obert i un altre intent d'entrada pot autenticar automàticament l'usuari.

L'endpoint local de sortida central és `http://localhost:10001/oauth/logout/`. Els endpoints d'API/UI han d'utilitzar consistentment el mateix hostname configurat per compartir la sessió del navegador; `localhost` i `127.0.0.1` tenen cookies diferents.

## Registrar endpoints

Des de `api`, usa `manage.py configure_oidc_client <application_key>` amb els valors reals de `--redirect-uri`, `--backchannel-logout-uri` i `--post-logout-redirect-uri`. Conserva el tipus de client existent (`--public` només per a clients públics). No cal girar el secret. La URI de retorn es compara exactament amb la llista registrada. Els endpoints s'han de configurar només per administradors de confiança.

Producció exigeix HTTPS; DEBUG permet HTTP exclusivament en loopback. La clau RSA de desenvolupament ja està configurada a `api/.env` (no es publica). En producció configura una clau pròpia estable amb la gestió de secrets del servidor. Registra un endpoint de back-channel només quan l'app el tingui implementat. Les apps sense endpoint també perden els tokens a KOT7K, però la seva sessió local no es pot invalidar remotament.

## Avisos i reintents

La revocació queda desada abans d'enviar els avisos. Els errors no recuperen la sessió. Els avisos pendents es guarden a `LogoutDelivery` amb nombre d'intents i tipus d'error, sense tokens ni respostes del receptor.

Executa periòdicament `python manage.py retry_logout_notifications` amb el teu supervisor de producció. Aquest canvi no instal·la cap tasca programada. El receptor ha de ser idempotent: els reintents porten el mateix `sid` i un `jti` nou. Es processen fins a 100 avisos per execució. Fins que l'app rep l'avís, pot conservar la seva sessió local.

## Microsoft → KOT7K

En producció, registra `https://<domini-ui>/authentication/front-channel-logout` a Entra. La notificació comprova l'origen de la sessió: només una sessió iniciada amb Microsoft es revoca, propagant després els avisos a les apps. Una sessió Django, LDAP o d'un altre proveïdor no es tanca.

No és una garantia universal: Entra ha d'enviar l'avís i el navegador ha de permetre accedir a l'emmagatzematge de KOT7K des de l'iframe. No es configura a desenvolupament HTTP. Sortir de KOT7K no tanca Microsoft.

## Actualització i proves

Aplica les migracions authentication 0008 i applications 0005. Els JWT antics sense `sid` deixen d'autenticar-se; cal tornar a entrar. No es modifica el proveïdor Django ni les contrasenyes.

Backend: `python manage.py test kot7k.authentication kot7k.applications kot7k.organizations --settings=config.test_settings` (base SQLite aïllada). UI: `node --test tests/*.test.mjs`, `npm run lint`, `npx tsc --noEmit`.
