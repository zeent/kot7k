# KOT7K

Identity and access management for applications.

## Scope

- Local and federated authentication: LDAP, OpenID Connect, Google, Microsoft, Apple, X.509 and WebAuthn.
- User directory and identity providers. Microsoft sign-in creates an active local account on first login after provider restrictions are validated, with no local password, administrator privileges or application assignments. Existing active accounts are linked; disabled accounts remain disabled.
- Applications, roles and user assignments.
- OAuth 2.0 / OpenID Connect provider and application access portal.
- Account activity: sign-ins, sign-outs and role assignments/removals.
- Administration and interface in Catalan, Spanish and English.

Asset inventories, incident/ticket management, procurement, document management and general-purpose risk/compliance modules are outside KOT7K's scope. External applications in those areas can still be registered for identity and access management.

## Structure

- `api/kot7k/authentication`: users, authentication and account activity.
- `api/kot7k/applications`: applications, roles, assignments and OAuth clients.
- `api/kot7k/organizations`: identity provider configuration.
- `clients/web`: login, dashboard and IAM administration.

## Installation on a Linux server

Clone the repository into a new directory and run `./devops/scripts/install.sh`.
The installer uses that checkout, requests the public domain and initial administrator,
and configures PostgreSQL, Django/Gunicorn, the static UI, Nginx and Let's Encrypt.
See [the installation guide](devops/scripts/README.md) for requirements and reruns.

## Local development

Configure PostgreSQL in `api/.env`; the default database and role are `kot7k`.
From `api`, activate `.venv`, run `python manage.py migrate`, then `python manage.py runserver 10001`.
From `clients/web`, run `npm ci` and `npm run dev` (port 10000).
PyCharm uses the `kot7k` module, `api/.venv/bin/python`, and `kot7k API` / `kot7k WebUI` configurations.

## Validation

From `api`: `python manage.py test kot7k --settings=config.test_settings`.
From `clients/web`: `npm run lint`, `npx tsc --noEmit --incremental false`, `npm run build`.

## Existing installations

Run migrations to deactivate the old built-in support application when it still points to `/support`. External applications and their assignments are preserved. Removing the old modules from this source tree does not drop their existing database tables; no live database cleanup is performed automatically.

## Central SSO logout

KOT7K tracks a browser session (`sid`) across its UI and OIDC clients. Signing out revokes that session's tokens and sends signed back-channel logout notifications to registered apps. Other browser sessions remain active. KOT7K never initiates logout from Microsoft, Outlook or Teams.

See [the integration guide](docs/sso-logout.md) for app endpoints, redirect registration, notification retries and deployment requirements. Talaia and Lynkr must implement the receiving side before their own sessions can close automatically.

Entra's front-channel URL must use the deployed **HTTPS UI origin**, followed by `/authentication/front-channel-logout`. Leave it unset in HTTP development. This endpoint only revokes sessions started with Microsoft; independent Django sessions stay active. Browser iframe storage restrictions can prevent delivery, so Microsoft logout is not a guaranteed revocation mechanism.
