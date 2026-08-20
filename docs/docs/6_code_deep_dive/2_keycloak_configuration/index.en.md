---
title: Keycloak Configuration
description: High-level overview of the aihub realm — clients, scopes, roles, tenant groups, identity brokering, and how the configuration reaches running instances
---

# Keycloak Configuration

Keycloak is the identity and access management component of the platform. All of its configuration is code: Jinja2
templates under `infra/deployment/templates/configs/keycloak/` are rendered per deployment stage into
`infra/configs/keycloak/` and applied to the Keycloak container through **two distinct lifecycles**. Understanding which
lifecycle a piece of config belongs to is the single most important thing before changing it, because it determines
whether an edit reaches an *already-running* deployment on the next AI-Hub upgrade or only a *freshly-initialized* one.

| Lifecycle     | Template folder       | Applied                                                                                                                                                      | Reaches existing deployments on upgrade?                                                                                                                                                        |
| ------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bootstrap** | `keycloak/bootstrap/` | First container start only — merged into `aihub-realm.{stage}.json` and imported via `--import-realm`                                                        | **No.** Keycloak skips already-existing realms by design. Operator/admin-console edits survive; file changes reach an existing deployment only via the admin console or a fresh realm database. |
| **Managed**   | `keycloak/managed/`   | Every container start — by the one-shot `keycloak-config` service ([keycloak-config-cli](https://github.com/adorsys/keycloak-config-cli)) over the admin API | **Yes.** File wins, including deletions; admin-console drift on these objects is reverted on the next restart.                                                                                  |

`keycloak-entrypoint.sh.j2` orchestrates the first-start import (env-var substitution + `--import-realm`) and applies
the session-lifespan migration via `kcadm`; it no longer reconciles clients, flows, or identity providers — that is the
`keycloak-config` service's job. The decision and mechanics are recorded in ADR
`2026_06_12_declarative_keycloak_realm_reconciliation`.

### What lives in each lifecycle

| Lifecycle     | Realm objects                                                                                                                                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Bootstrap** | Realm-level settings (login theme, brute-force protection, token and session lifespans, SMTP), the user-profile component, the startup **tenant group** seed, the **superuser** seed, and the **identity providers** (Azure AD + mappers). |
| **Managed**   | Realm **roles**, **client scopes**, **clients**, custom **authentication flows** (incl. the Langfuse sysadmin gate and its `browserFlow` binding), and the `aihub-api-service` **service account**.                                        |

::: tip Rule of thumb
If you change something in `bootstrap/` and need it on an existing deployment, you must apply it manually (admin
console) or reset the realm database. If you change something in `managed/`, a stack restart rolls it out automatically.
Runtime data — real users, tenant-group memberships, and operator-tuned identity-provider edits — is never touched by
either path.
:::

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

The `generate_compose.py` renderer produces two outputs from the templates: it JSON-merges **all** documents (bootstrap

- managed) into a single `aihub-realm.{stage}.json` for the first-start import, and it renders each **managed** document
  separately as an input file for the `keycloak-config` service. At runtime the two lifecycles apply as follows:

1. **First start (bootstrap + managed seed).** The Keycloak entrypoint substitutes environment variables into the merged
   realm JSON (pure-bash `envsubst`; the Keycloak image ships no template tooling) and imports it via `--import-realm`.
   This creates the complete realm in one shot — realm settings, tenant group, superuser, identity providers, roles,
   scopes, clients, and flows — so dependent services (oauth2-proxies, Open WebUI, Langfuse) come up without waiting for
   the reconciler. Keycloak **never re-imports an existing realm**, so on later starts this step is a no-op.
2. **Every start (managed reconcile = the upgrade path).** Once Keycloak is healthy, the one-shot `keycloak-config`
   service reconciles the `managed/` documents over the admin API: roles, client scopes, clients, authentication flows
   (including the Langfuse gate and the `browserFlow` binding), and the API service account. **This is what an AI-Hub
   version upgrade updates** — file wins, deletions included, admin-console drift reverted. It adopts the entities the
   first-start import already created, so fresh and existing deployments converge to the same state.

What this means in practice when upgrading AI-Hub:

- **Managed** changes (a new client, a changed redirect URI, a new realm role, an altered auth flow) **roll out
  automatically** on the next stack start.
- **Bootstrap** changes (realm settings, the tenant-group seed, the superuser, **identity providers**) do **not** reach
  an already-initialized realm. Apply them in the Keycloak admin console, or re-seed by resetting the realm database.
  Conversely, this is exactly why operator edits to those objects (e.g. rotating an Azure client secret in the console,
  tuning token or session lifespans) survive upgrades.

The Langfuse sysadmin gate follows the managed path (its flows live in `managed/40-auth-flows.json.j2`); details in
[Langfuse Sysadmin Gate](1_langfuse_sysadmin_gate/).
