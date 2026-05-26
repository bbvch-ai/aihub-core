# Make `sysadmin-{api,web}` a Self-Contained Product Slice

## Context

ADR [`2026_05_19_split-sysadmin-into-proprietary-packages`](./2026_05_19_split-sysadmin-into-proprietary-packages.md)
extracted the sysadmin plane into `packages/sysadmin-{api,web}`. The initial extraction was minimal: `sysadmin-api`
owned only `TenantAdminController` + a tiny `WhoamiController` (for the role gate), and its `_sysadmin_lifespan`
connected MongoDB only. `sysadmin-web` inherited every page and composable from `@swiss-ai-hub/web` via Nuxt Layer
extension.

In practice this left `sysadmin-web` dependent on the main API to function. The inherited composables it uses
(`useUsers`, `useRoles`, `useCreateRole`, `useUpdateRole`, `useDeleteRole`, `useAuthProviders`) all call
`@core/sdk/client.*`, which is configured with a single base URL via `apiBaseUrl`. To make them resolve, we either had
to:

1. Point `apiBaseUrl` cross-origin at the main API — coupling the sysadmin product to the main API origin, breaking the
   "independently deployable" property recorded in the earlier ADR, and inconsistent between dev and prod (dev was
   cross-origin, prod was same-origin).
2. Or expose those endpoints on `sysadmin-api` itself, same-origin under `sysadmin.${DOMAIN}/api/v1`.

The composability model behind the Nuxt layer + SDK split is: **pick the UI components you need from
`@swiss-ai-hub/web`, then mount the API controllers backing those components on the API runner you ship next to it.** We
chose to honor that model — `sysadmin-{api,web}` should be runnable standalone, with no main API alongside.

## Decision Drivers

- _Independent deployability (carried over from `2026_05_19`)_\
  Sysadmin slice must work with `sysadmin-api` as its only backend.
- _SDK composability_\
  The `pick UI + mount matching API` pattern is the central design promise of how downstream consumers will assemble
  their own products from the swiss-ai-hub building blocks. Sysadmin-web is the first in-repo consumer that exercises
  it; the pattern must hold for sysadmin first.
- _Avoid cross-origin coupling_\
  Cross-origin token forwarding, audience mismatches, preflight overhead, and dev/prod config divergence are all real
  costs.
- _Avoid invented `sysadmin-api`-only endpoints when an existing `packages/api` controller fits_\
  The earlier draft added a bespoke `WhoamiController` instead of reusing `MyAccountController`. That was wrong — it
  duplicated purpose without good reason.

## Decision

### Lifespan expansion

`SysadminApiRunner._sysadmin_lifespan` is widened from "MongoDB-only" to **MongoDB + NATS + Redis**, plus
`I18nMiddleware` is attached to the FastAPI app so `use_locale` resolves. This is intentionally a *medium* lifespan: it
does NOT pull in Milvus, S3, Neo4j, WebSocket plumbing, discovery services, provisioners, RPC responders, or event
subscribers — those remain main-API-only.

### Controller mount list

`sysadmin-api/main.py` mounts a curated subset of `packages/api` controllers, picked to cover every endpoint
`sysadmin-web`'s confined surface (`/auth/*` + `/tenants/*`) hits:

| Controller                                   | Reason                                                                                        |
| -------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `MyAccountController.get_my_identity()` only | Role gate (`is_sys_admin`) for `sysadmin.global.ts`. Replaces the removed `WhoamiController`. |
| `UserController`                             | Inherited `useUsers`, `useUser`.                                                              |
| `RoleController`                             | Inherited `useRoles`, `useCreateRole`, `useUpdateRole`, `useDeleteRole`.                      |
| `AuthProviderController`                     | Inherited `useAuthProviders` on `/auth/login`.                                                |

Code ownership stays in `packages/api`; `sysadmin-api` only re-mounts via the public `swiss_ai_hub.api` interface.

### MyAccount split

`MyAccountController.get_my_account()` conflated two concerns: user identity (`is_sys_admin`, roles, dashboard) and a
runtime-discovered access matrix (which services / agents / processes the user can use). The access-matrix path needs
NATS + locale, and on `sysadmin-api` would produce a misleadingly narrow matrix anyway (because `runner.controllers`
there reflects only sysadmin-api's surface).

We split it: a new `MyAccountController.get_my_identity()` returns the identity portion only (`UserDTO`, no access
field), depending on nothing beyond `Security(authenticated_user())` + MongoDB. The existing `get_my_account()` stays
unchanged on main API. `sysadmin-api` mounts only `get_my_identity()`.

### Deleted

- `WhoamiController` + its DTO + sysadmin-api's `routes/whoami/` package.
- The dev-only cross-origin `MAIN_API_URL` branch in `packages/sysadmin-web/.app/nuxt.config.ts`. `apiBaseUrl` is now
  `/api/v1` same-origin in both dev (Nitro proxy → `:8001`) and prod (`sysadmin.${DOMAIN}/api/v1` → `sysadmin-api`).

## Consequences

### Positive

- **Standalone product:** `sysadmin-api` + `sysadmin-web` is runnable with no main API on the wire. Token flow, role
  gate, tenant CRUD, user list, role CRUD, auth providers all land same-origin.
- **No dev/prod divergence:** `apiBaseUrl` is the same value in both environments.
- **Composability pattern proven:** the "pick UI + mount matching API" model is honored end-to-end with sysadmin as the
  first concrete instance — downstream consumers building on `@swiss-ai-hub/web` have a worked example to copy.
- **API surface cleaner:** the identity-vs-access conflation in `MyAccountController` is named and split.

### Negative

- **`sysadmin-api` startup is heavier:** still under 1s in dev, but it now needs NATS + Redis reachable. Deploy order
  matters — sysadmin-api will fail to start if either is down.
- **`sysadmin-api` OpenAPI surface is larger:** 4 controllers re-mounted vs. the original 2 owned. Anyone scanning the
  spec will see tenant-scoped routes there.
- **Compose ENV needs updating:** sysadmin-api's compose entry now needs `NATS_URL` and `REDIS_URL` (or equivalent
  derived from existing settings). Tracked separately under deploy/infra changes.

### Reversibility

The decision is fully reversible — controllers can be unmounted and the lifespan can be re-narrowed without touching
code in `packages/api`. The reverse direction (cross-origin to main API) requires changing one config value in
`sysadmin-web/.app/nuxt.config.ts`. We do not expect to reverse this, but the option exists.

## References

- ADR [`2026_05_19_split-sysadmin-into-proprietary-packages`](./2026_05_19_split-sysadmin-into-proprietary-packages.md)
  — original extraction.
- ADR [`2026_04_15_sysadmin_implicit_admin_access`](./2026_04_15_sysadmin_implicit_admin_access.md) — sysadmin
  short-circuit that keeps the auth model coherent when the same controllers are mounted on both APIs.
- PR #1304 — the open-source rollout PR this change ships in.
