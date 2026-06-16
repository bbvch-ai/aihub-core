---
title: Keycloak Configuration
description: High-level overview of the aihub realm — clients, scopes, roles, tenant groups, identity brokering, and how the configuration reaches running instances
---

# Keycloak Configuration

Keycloak is the identity and access management component of the platform. All of its configuration is code: three Jinja2
templates under `infra/deployment/templates/configs/` are rendered per deployment stage into `infra/configs/keycloak/`
and mounted into the Keycloak container.

| File                                  | Contains                                                         | Applied                                            |
| ------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------- |
| `keycloak-realm.json.j2`              | The `aihub` realm: clients, scopes, roles, flows, …              | First container start only (`--import-realm`)      |
| `keycloak-identity-providers.json.j2` | External IdPs (Azure AD) and their mappers                       | Every container start (`partialImport`, overwrite) |
| `keycloak-entrypoint.sh.j2`           | Env-var substitution, import orchestration, kcadm reconciliation | Every container start                              |

## The `aihub` realm

The realm defines the platform's login behavior: users sign in with their e-mail address
(`registrationEmailAsUsername`), self-registration is disabled (users come from the identity provider or are created by
an admin), brute-force protection and "remember me" are enabled, and the custom `aihub` login theme is applied. TLS is
required for external requests on all stages except `dev`. The realm binds a custom browser flow (`browser-aihub`, see
[Langfuse Sysadmin Gate](1_langfuse_sysadmin_gate/)).

## Realm roles

Only two realm roles exist — everything fine-grained is handled by tenant-scoped roles *inside* the platform, not in
Keycloak:

| Role            | Effect                                                                                                                                       |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `AIHubAccess`   | Required to log in at all. Users without it are denied at the IdP post-login check.                                                          |
| `AIHubSysAdmin` | Platform administrator: gates the oauth2-proxy admin tools (Dagster, Attu, SeaweedFS, Backup) and Langfuse, and marks superusers in the API. |

## Tenant groups

Tenant membership is modeled as Keycloak groups under `/tenants/<tenant-id>`. The startup tenant group is created by the
realm import and set as a default group, so every new user lands in it. The `tenants` client scope exposes the group
paths as a token claim, which the API uses to resolve a user's tenants (see ADR
`2026_02_20_keycloak_tenant_assignment_via_groups`).

## Clients

| Client                                                     | Type                 | Used by                                                                                                          |
| ---------------------------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `aihub-frontend`                                           | Public, PKCE         | Main web UI **and** sysadmin web UI (same realm cookie → shared SSO)                                             |
| `openwebui`                                                | Confidential         | Open WebUI chat interface (OIDC login, receives the `roles` claim)                                               |
| `oauth2-proxy-dagster` / `-datalake` / `-attu` / `-backup` | Confidential         | The oauth2-proxy sidecars in front of the admin UIs; access restricted via the `roles` claim (`AIHubSysAdmin`)   |
| `langfuse`                                                 | Confidential, PKCE   | Langfuse native Keycloak SSO; carries the `langfuse-sysadmin-gate` marker scope                                  |
| `aihub-api-service`                                        | Service account only | The API backend; holds `realm-management` roles (`manage-users`, `view-groups`, …) for user/group administration |

## Client scopes

Besides the standard `openid` / `profile` / `email` scopes, the realm defines:

| Scope                    | Mapper                                    | Purpose                                                      |
| ------------------------ | ----------------------------------------- | ------------------------------------------------------------ |
| `roles`                  | Realm-role mapper → `roles` claim         | Lets clients (frontend, oauth2-proxies, …) see realm roles   |
| `tenants`                | Group-membership mapper → `tenants` claim | Tenant resolution from `/tenants/...` group paths            |
| `langfuse-sysadmin-gate` | *none* (marker scope)                     | Activates the Langfuse deny gate in the authentication flows |

## Identity brokering (Azure AD)

The realm acts as an identity broker (see ADR `2026_02_28_keycloak_as_identity_broker`): the `azure-ad` provider logs
users in against Microsoft Entra ID (PKCE, `syncMode: FORCE`). Its mappers copy e-mail, first/last name and username
from the Azure token, and two role mappers translate the Azure app-role claims `AIHubAccess` and `AIHubSysAdmin` into
the realm roles of the same name. Because the sync mode is FORCE, the roles are **re-synced on every broker login** —
removing an app role in Azure removes the realm role at the user's next login (and vice versa); manually assigned realm
roles do not survive for brokered users. The provider's post-login flow denies any user whose token lacks `AIHubAccess`.

## Seeded users

The realm import creates one superuser (credentials and roles from the `SUPERUSER_*` environment variables — by default
carrying `AIHubAccess` and `AIHubSysAdmin`) and the service-account user backing `aihub-api-service`.

## Authentication flows

Two custom mechanisms extend the built-in flows:

- **`Post Broker Login - AIHubAccess Check`** — runs after every Azure AD login and denies users without the
  `AIHubAccess` realm role.
- **`browser-aihub` + the Langfuse sysadmin gate** — the realm's browser flow with a conditional deny that restricts
  Langfuse logins to `AIHubSysAdmin`. The mechanism, the reasons for replicating the built-in browser flow, and the
  structural pitfalls are documented in [Langfuse Sysadmin Gate](1_langfuse_sysadmin_gate/).

## How configuration reaches running instances

The entrypoint script substitutes environment variables into the JSON templates (pure-bash `envsubst`; the Keycloak
image ships no template tooling), then applies three layers with different lifecycles:

1. **Realm JSON** — imported via `--import-realm` on the *first* start only. Keycloak never re-imports an existing
   realm, so realm-file changes do not reach already-initialized databases by themselves.
2. **Identity providers** — applied on *every* start via the admin API (`partialImport` with overwrite), so IdP and
   mapper changes roll out with a container restart.
3. **Langfuse sysadmin gate** — authentication flows are not supported by `partialImport`, so the entrypoint reconciles
   the gate idempotently via `kcadm` on every start (details in [Langfuse Sysadmin Gate](1_langfuse_sysadmin_gate/)).
