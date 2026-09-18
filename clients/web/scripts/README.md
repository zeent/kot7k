# Static UI build

Run `npm run build` from `clients/web`. Next exports the UI, then
`publish-static-build.mjs` validates it and moves it to `api/ui_dist`, restoring
the previous build if publication fails. `out` is consumed by publication.
The deployment wrapper `devops/scripts/build-ui.sh` uses the same process.

Set `NEXT_PUBLIC_API_BASE_URL` before building for the target environment.
It is embedded in the frontend and both logout pages (default: http://localhost:10001).
Locale selection reads the saved cookie or browser languages after hydration.

The logout GET handlers use `force-static` and preserve their standalone HTML
and existing public scripts. Next exports these two files without extensions.
HTTP response headers are not automatically applied by a static server.
The publisher therefore generates `.nginx/logout.conf` from Next's build metadata,
including the CSP, no-store policy, HTML content type and referrer policy.

## Serving through Django

Django serves `api/ui_dist` through `config.ui`, after the backend URL patterns,
including when `DEBUG=False`. `/api/`, `/oauth/`, `/admin/`, `/static/`, `/media/`
and `/.well-known/` remain reserved for the backend. Missing files return 404.
The publisher also writes `.ui-headers.json`; Django uses it for logout headers
and blocks HTTP access to all dotfiles. Rebuild before starting this version of
Django: logout returns 503 if its header metadata is unavailable.

The existing Nginx reverse proxy to Django can remain as configured. No Nginx
logout include is needed when Django serves the UI. Django admin static files
remain separate from the Next export and need the existing static-file setup.
For a shared frontend/backend domain, build with `NEXT_PUBLIC_API_BASE_URL` set
to that public origin and configure `OIDC_FRONTEND_URL` to the same origin in
Django's environment. Keep `ALLOWED_HOSTS`, `OIDC_ISSUER` and
`EXTERNAL_AUTH_CALLBACK_BASE_URL` aligned with the public deployment.

## Optional direct Nginx serving

In the Nginx server block that serves the UI directly, configure:

```nginx
root /opt/kot7k/api/ui_dist;
include /opt/kot7k/api/ui_dist/.nginx/logout.conf;

location / {
    try_files $uri $uri.html $uri/ =404;
}
location ~ /\. {
    deny all;
}
```

Keep backend locations (`/api/`, `/oauth/`, `/admin/`, `/.well-known/`) routed to
Django. Validate and reload Nginx after publishing, particularly when the API
origin changes. Do not add X-Frame-Options DENY/SAMEORIGIN to the front-channel
logout location: Microsoft needs to embed it. The generated CSP limits framing.
Other static servers need equivalent per-route headers and HTML content types.
This build command publishes local files; it does not modify or reload a running server.
