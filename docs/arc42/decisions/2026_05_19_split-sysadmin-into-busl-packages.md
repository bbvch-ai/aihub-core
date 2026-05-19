# Split the Sysadmin Plane into Separately-Licensed BSL Packages

## Context

The repository is being open-sourced under a **mixed-license model**: Apache-2.0 for the platform runtime and shared
code, AGPL-3.0-or-later for the frontend and backup service, and the Business Source License 1.1 (BUSL-1.1) for
multi-tenant management. The full per-package matrix lives in `LICENSES.md`.

Before this change, multi-tenant administration was **intermingled inside permissively-licensed packages**:
tenant-lifecycle endpoints lived in the Apache-2.0 `packages/api` (`routes/tenant_admin/`), and the sysadmin UI lived in
the AGPL-bound `packages/web` (`pages/sysadmin/**`). Each Python package and the Nuxt app publishes as a single artifact
with a single license string. A published artifact cannot carry two licenses, so commercially-protected (BSL) code
cannot share a package with Apache/AGPL code. The license model was therefore unenforceable as long as the sysadmin
plane stayed embedded.

The web frontend is also a deliberate **product surface**: it is shipped as a Nuxt _layer_ (`@swiss-ai-hub/web`) so
customers can build their own UI on top of it. We needed a real, in-repo consumer of that layer to keep it honestly
extensible rather than only theoretically so.

## Decision Drivers

- _Per-artifact license integrity_\
  Every published Docker image / npm / PyPI artifact must carry exactly one, correct license. Mixing is not viable.
- _Commercial protection of multi-tenant management_\
  Multi-tenant administration is the commercially differentiating surface; it must be BSL (non-production use until the
  Change Date) while the rest of the platform stays permissive.
- _Dogfooding the web layer_\
  `sysadmin-web` must consume `@swiss-ai-hub/web` as a Nuxt layer via a workspace dependency + `extends` — not a fork,
  not a copy. Layer defects must be fixed in the layer so the extension contract is real.
- _Independent deployability_\
  The sysadmin plane gets its own images, its own subdomain, and its own release/CI path, deployable and upgradable
  without touching the platform.
- _Shared identity_\
  A user logging in once must reach both planes; no second realm or second login.
- _Future scope_\
  Naming is `sysadmin-*` (not `tenant-*`) because more system-administration features beyond tenant management are
  anticipated.

## Decision

Extract the sysadmin plane into two new packages:

- **`packages/sysadmin-api`** (BUSL-1.1) — FastAPI service holding the sysadmin-gated tenant-lifecycle endpoints
  (`TenantAdminController` + service + DTOs, moved out of `packages/api`). It depends on `swiss-ai-hub-core` and
  `swiss-ai-hub-api` (both Apache-2.0; one-way compatible — Apache may be embedded in BSL, never the reverse). It runs a
  **standalone `SysadminApiRunner`** that does _not_ inherit `ApiRunner`: a MongoDB-only lifespan, no MCP, no
  NATS/Milvus/Redis/S3/WebSocket wiring. Inheriting the heavy runner and suppressing it produced a fragile "lite vs full
  lifespan" override; a purpose-built ~90-line runner is the correct abstraction. BSL display strings moved to a
  package-local `SysadminApiLocaleString` so no proprietary string resides in the Apache `packages/api`.
- **`packages/sysadmin-web`** (BUSL-1.1) — a thin Nuxt layer that `extends: ['@swiss-ai-hub/web']` via `workspace:*`. It
  adds only the sysadmin pages/composables/layout/middleware and a confinement guard; everything else is inherited from
  the layer.

`MyTenantController` (every user needs "list my tenants") stays in the open-source `packages/api`.

Both are served at **`sysadmin.${DOMAIN}`** (path-split: web at `/`, api at `/api/v1`) and share the **same Keycloak
realm and `aihub-frontend` client** as the main app, so the realm SSO cookie makes login transparent across `${DOMAIN}`
and `sysadmin.${DOMAIN}`. The two origins differ in dev (web UI `:3333`, API `:8000`, sysadmin web `:3334`, sysadmin api
`:8001`) but collapse onto `${DOMAIN}` in production behind Traefik; runtime config therefore distinguishes the main
**API** origin (`mainApi.url`, for the cross-origin `is_sys_admin` check) from the main **UI** origin (`mainApp.url`,
for cross-origin browser redirects).

BSL parameters (authoritative copy: `packages/sysadmin-{api,web}/LICENSE`): Licensor bbv Software Services AG; no
Additional Use Grant (non-production use only, the BSL default); **Change Date 2030-05-13**; **Change License
Apache-2.0**. After the Change Date the packages auto-convert to Apache-2.0.

The monorepo is bootstrapped as proper **pnpm + uv workspaces** so `sysadmin-web` can depend on `@swiss-ai-hub/web` and
`sysadmin-api` on `swiss-ai-hub-{core,api}` as workspace members.

## Consequences

- Each package's own `LICENSE` is authoritative for its subtree; `LICENSES.md` is the matrix. License integrity is now
  mechanically enforceable per artifact, and `make license-check` treats `sysadmin-api` as an internal package and its
  images as own-images.
- CI/CD, sonar, dependabot, version-bump, and `set-latest` auto-discovery were extended to the two packages; a dedicated
  `build-sysadmin.yml` builds both images on the shared `release-ready` dispatch. `sysadmin` is an allowed PR scope.
- Hardening the web layer to be a true extension point produced reusable improvements that benefit _all_ layer
  consumers, not just `sysadmin-web`: SDK client moved from `app.vue` into a plugin, single-Vue enforcement, runtime
  config delivered synchronously via `window.__AIHUB_CONFIG__` (`/config.js`) instead of three `config.json` fetches,
  and a documented extension contract (declare own `imports.dirs`, own `i18n.locales`, pin Vue, provide `index.vue` +
  confinement for a focused UI).
- A thin extender must re-declare some layer config (nested `imports.dirs`, `i18n.locales`) and owns cross-origin
  navigation back to the main app. This is intrinsic to being a focused layer consumer and is documented in
  `packages/sysadmin-web/CLAUDE.md`.
- Apache → BSL is one-way. `sysadmin_api` symbols must never leak back into `core`/`api`. New system-administration
  features belong in the `sysadmin-*` packages.

## Exit Criterion

On the **Change Date (2030-05-13)** the BSL packages convert to Apache-2.0 automatically per the BSL instrument; the
per-package `LICENSE` files and `LICENSES.md` should then be updated to reflect the conversion and this ADR marked
"Superseded by conversion".
