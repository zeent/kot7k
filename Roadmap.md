# Kot7k API Roadmap — V1 Checklist

## V1.0 — Base funcional i contracte API

### Authentication
- [x] Serializer request/response `POST /api/authentication/login/` (20260323)
- [x] Serializer `POST /api/authentication/logout/` (20260323)
- [x] Serializer `GET /api/authentication/me/` (20260323)
- [x] Serializer `POST /api/authentication/refresh/` (20260323)
- [x] Serializer `POST /api/authentication/change-password/` (20260323)
- [x] Serializer `POST /api/authentication/request-password-reset/` (20260323)
- [x] Serializer `POST /api/authentication/reset-password/` (20260323)
- [ ] Serializer `GET /api/authentication/sessions/`
- [ ] Serializer `POST /api/authentication/sessions/revoke/`
- [ ] Serializer `POST /api/authentication/request-email-verification/`
- [ ] Serializer `POST /api/authentication/verify-email/`
- [ ] Afegir examples OpenAPI
- [ ] Unificar format d’errors

### Audit
- [ ] Serializer `GET /api/audit/events/`
- [ ] Filtres: `user`, `event_type`, `status`, `date_from`, `date_to`
- [ ] Paginació
- [ ] Ordenació per defecte (`-created_at`)
- [ ] Examples de resposta

### Tenants
- [ ] `POST /api/tenants/`
- [ ] `PATCH /api/tenants/{id}/`
- [ ] `DELETE /api/tenants/{id}/` (o soft delete)
- [ ] Serializer `GET /api/tenants/`
- [ ] Serializer `GET /api/tenants/{id}/`
- [ ] Serializer memberships:
  - [ ] `GET /api/tenants/{id}/memberships/`
  - [ ] `POST /api/tenants/{id}/memberships/`
  - [ ] `PATCH /api/tenants/{id}/memberships/{id}/`
  - [ ] `DELETE /api/tenants/{id}/memberships/{id}/`
- [ ] Filtre per `status`
- [ ] Excloure `REMOVED` per defecte
- [ ] Roles per tenant:
  - [ ] `GET /api/tenants/{id}/roles/`
  - [ ] `POST /api/tenants/{id}/roles/`
  - [ ] `PATCH /api/tenants/{id}/roles/{id}/`
  - [ ] `DELETE /api/tenants/{id}/roles/{id}/`

### Users
- [ ] `GET /api/users/{id}/`
- [ ] `POST /api/users/`
- [ ] `PATCH /api/users/{id}/`
- [ ] `DELETE /api/users/{id}/` (o desactivació)
- [ ] Serializer amb tenants i memberships
- [ ] Filtres (actiu, verificat, etc.)

### Applications
- [ ] Validar paths:
  - [ ] `/api/applications/`
  - [ ] `/api/applications/{id}/`
  - [ ] `/api/applications/roles/`
  - [ ] `/api/applications/roles/{id}/`
  - [ ] `/api/applications/memberships/`
  - [ ] `/api/applications/memberships/{id}/`
- [ ] Filtres per tenant
- [ ] Filtres per application
- [ ] Filtres per memberships (user, status)
- [ ] Validacions de coherència (tenant/app/role)
- [ ] Decidir visibilitat de `client_secret`
- [ ] Examples de resposta

---

## V1.1 — OAuth 2.0 Provider

### Core endpoints
- [ ] `GET /oauth/authorize/`
- [ ] `POST /oauth/token/`
- [ ] `POST /oauth/revoke/`
- [ ] `POST /oauth/introspect/`

### Flows
- [ ] `authorization_code`
- [ ] `refresh_token`
- [ ] `client_credentials`
- [ ] Decidir `password` grant
- [ ] Excloure o no `implicit`

### Validació
- [ ] Validar `redirect_uri`
- [ ] Validar `client_type`
- [ ] Validar `authorization_grant_type`
- [ ] Expiració tokens
- [ ] Revocació refresh tokens

### Audit OAuth
- [ ] Log authorization
- [ ] Log token issue
- [ ] Log revoke
- [ ] Log introspect

### Consent
- [ ] Sistema de consentiment
- [ ] Persistència consentiment
- [ ] Revocació consentiment

---

## V1.2 — OpenID Connect

### Discovery
- [ ] `GET /.well-known/openid-configuration`
- [ ] `GET /oauth/jwks/`

### User info
- [ ] `GET /oauth/userinfo/`
- [ ] Claims:
  - [ ] `sub`
  - [ ] `email`
  - [ ] `email_verified`
  - [ ] `name`

### Claims avançats
- [ ] `tenant_id`
- [ ] `tenant_code`
- [ ] `roles`
- [ ] `applications`

### PKCE
- [ ] Implementar PKCE
- [ ] Obligar PKCE per clients públics

---

## V1.3 — Authorization real

### Application roles
- [ ] Resolver rols per usuari/app
- [ ] Endpoint o servei de permisos
- [ ] Integrar amb tokens (claims)

### Coherència
- [ ] Validar user ↔ tenant ↔ application
- [ ] Validar role ↔ application
- [ ] Evitar inconsistències multi-tenant

---

## V1.4 — Qualitat i contracte

### OpenAPI
- [ ] Eliminar `No response body`
- [ ] Afegir `serializer_class` a totes les views
- [ ] `operationId` únics
- [ ] Tags coherents
- [ ] Descriptions completes
- [ ] request/response definits

### Errors
- [ ] Format uniforme:
  - [ ] 400
  - [ ] 401
  - [ ] 403
  - [ ] 404
  - [ ] 409

### Paginació i filtres
- [ ] Paginació users
- [ ] Paginació audit
- [ ] Paginació applications
- [ ] Query params documentats

### Seguretat
- [ ] Throttle login
- [ ] Throttle password reset
- [ ] Throttle verify email
- [ ] Throttle OAuth token
- [ ] Throttle introspect/revoke

---

## Definition of Done — V1

### Mínim
- [ ] Authentication complet
- [ ] Users CRUD
- [ ] Tenants CRUD
- [ ] Memberships CRUD
- [ ] Applications CRUD
- [ ] ApplicationRoles CRUD
- [ ] ApplicationMemberships CRUD
- [ ] Audit funcional
- [ ] OAuth core endpoints
- [ ] OpenAPI sense warnings

### Recomanat
- [ ] OIDC discovery
- [ ] JWKS
- [ ] UserInfo
- [ ] PKCE
- [ ] Rate limiting
- [ ] Errors uniformes

---

## Sprints suggerits

### Sprint 1
- [ ] Authentication serializers
- [ ] Audit serializers
- [ ] Tenants CRUD
- [ ] Users CRUD

### Sprint 2
- [ ] Applications refinament
- [ ] Roles i memberships coherents

### Sprint 3
- [ ] OAuth endpoints
- [ ] Tokens i flows

### Sprint 4
- [ ] OIDC
- [ ] Claims
- [ ] PKCE

### Sprint 5
- [ ] Schema final
- [ ] Rate limiting
- [ ] QA final