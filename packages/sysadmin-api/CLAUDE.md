# packages/sysadmin-api - System Administration API (Proprietary)

**Purpose**: FastAPI service for system-administrator-only operations. Multi-tenant management lives here. Runs as a
separate Docker image on `sysadmin.${DOMAIN}/api/v1/*`.

**License**: Proprietary — All Rights Reserved (`LicenseRef-Proprietary`). No use granted; commercial license required
for any use. The package's `LICENSE` is the authoritative source for terms.

## Scope responsibility

`sysadmin-{api,web}` is a self-contained product slice: it is supposed to be runnable WITHOUT `packages/api` /
`packages/web` running side-by-side. The SDK composability rule is — pick the UI components you want from
`@swiss-ai-hub/web` (via Nuxt Layer extension), then mount the API controllers backing them on sysadmin-api. Expand the
runner's lifespan if those controllers need more infra.

### Code ownership rules

Code that lives in this package (must require sysadmin role + be sysadmin-only):

- Tenant lifecycle management (`TenantAdminController` — list / get / create / update / delete tenant metadata).

Code that does NOT live here (lives in `packages/api`):

- Anything reused by main API too — including controllers that sysadmin-api also mounts.
- Agent / process runtime, knowledge, threads, events — platform runtime stays in `packages/api`.

### Runtime mount policy

`main.py` mounts a curated subset of `packages/api` controllers (imported via the public `swiss_ai_hub.api` interface)
so sysadmin-web's inherited `@swiss-ai-hub/web` composables resolve same-origin against sysadmin-api. Currently:

| Controller                                   | Powers (inherited composables / pages)                               |
| -------------------------------------------- | -------------------------------------------------------------------- |
| `MyAccountController.get_my_identity()` only | `sysadmin.global.ts` role gate (replaces the old `WhoamiController`) |
| `UserController`                             | `useUsers`, `useUser`                                                |
| `RoleController`                             | `useRoles`, `useCreateRole`, `useUpdateRole`, `useDeleteRole`        |
| `AuthProviderController`                     | `useAuthProviders` on inherited `/auth/login`                        |

The controllers' own permission templates (`user_with_permission(aihub.admin.service.X)`) plus the sysadmin
short-circuit (ADR `2026_04_15_sysadmin_implicit_admin_access`) keep the auth model coherent — sysadmins implicitly hold
`ACCESS_ADMIN` in every tenant, so they can hit these endpoints on sysadmin-api just like on main API.

`MyAccountController.get_my_account()` is deliberately NOT registered here: it returns an access matrix enumerated from
`runner.controllers`, which on sysadmin-api would be a misleadingly narrow slice of the platform surface. The
`is_sys_admin` field the middleware needs is on the identity DTO already (`get_my_identity` split).

Extend the mount list when adding inherited composables that hit endpoints not in the table above; extend the lifespan
(below) if those controllers depend on infra sysadmin-api doesn't yet wire.

## Folder structure

```
packages/sysadmin-api/
├── pyproject.toml
├── LICENSE                       # Proprietary — All Rights Reserved
├── README.md
├── Makefile                      # lint, format, test, run-dev, run-prod
├── Dockerfile                    # Multi-stage uv-based build
├── swiss_ai_hub/sysadmin_api/
│   ├── __init__.py
│   ├── main.py                   # Production ASGI entry (swiss_ai_hub.sysadmin_api.main:app)
│   ├── sysadmin_runner.py        # Standalone runner (does NOT inherit ApiRunner)
│   └── routes/
│       ├── __init__.py           # Lazy public-interface exports
│       └── tenant_admin/         # Controller + service + DTOs (moved from packages/api)
│           ├── tenant_admin_controller.py
│           ├── tenant_admin_service.py
│           └── dto/
└── tests/
    ├── conftest.py               # Mirrors packages/api conftest (db isolation, mocks)
    └── tenant_admin/             # Mirrors moved test files
        ├── test_sysadmin_gate.py
        ├── test_create_tenant_metadata.py
        ├── test_delete_tenant_metadata.py
        └── test_tenant_request_validation.py
```

## The standalone runner

`sysadmin_runner.py` defines `SysadminApiRunner`. It deliberately **does NOT inherit `swiss_ai_hub.api.ApiRunner`**. An
earlier attempt subclassed `ApiRunner` and overrode just the `lifetime_manager` property ("lite vs full lifespan"); that
proved fragile — the inherited `create_app` builds an MCP server and the override behaved differently under gunicorn
than in isolation. Inheriting a runner whose entire lifespan exists to wire
NATS/Milvus/Redis/S3/WebSocket/discovery/provisioners, only to suppress all of it, was the wrong abstraction.

`SysadminApiRunner` builds a plain `FastAPI` app mounted under `/api/v1` via Starlette, with CORS + `I18nMiddleware`,
and a `mount()` that matches `Controller.mount(app, runner)`. It does **not**:

- build an MCP server (sysadmin-api has no MCP need)
- inject `tenant_id` into the OpenAPI schema (sysadmin-api inherits route shapes from re-mounted controllers — both
  tenant-scoped routes from `packages/api` and global routes from `sysadmin-api` itself coexist)

**Lifespan:** MongoDB + NATS + Redis. The closure in `create_app()` captures the inner FastAPI app and stores
`app.state.nc` + `app.state.redis` so the standard FastAPI deps (`use_nats`, `use_redis`) resolve at request time. This
is intentionally a *medium* lifespan — enough to satisfy every controller currently mounted (some declare `use_nats` /
`use_redis` even if their hot path doesn't touch the clients, since FastAPI resolves dependencies eagerly), but it
deliberately omits Milvus / S3 / Neo4j / WebSocket / discovery services / provisioners / RPC responders / event
subscribers. Extend it if a future mounted controller needs one of those — match the source pattern in
`packages/api/.../lifetime_manager.py`.

When #1203 (the `aihub-daemon` extraction that thins the main API's `lifetime_manager`) lands, **nothing here needs to
change** — sysadmin-api never depended on the API's lifespan in the first place.

## Entry point

`swiss_ai_hub.sysadmin_api.main:app` (gunicorn target). Deliberately a fully-qualified module path, **not** `app.main` —
`packages/api` ships its own `app/main.py`, and this image bundles `swiss-ai-hub-api`, so a bare `app.main` target is a
module-name collision footgun.

## Auth

Same Keycloak realm + same `aihub-frontend` client as `packages/api`. Every endpoint must use
`Security(self.sys_admin_user())` from the `Controller` base class — this is the realm-role gate that returns 403 for
anyone without the `AIHubSysAdmin` Keycloak realm role. There is no per-tenant authorization on this plane — sysadmin
short-circuit (see `docs/arc42/decisions/2026_04_15_sysadmin_implicit_admin_access.md`) grants `ACCESS_ADMIN` to
sysadmins unconditionally.

## Cross-package imports

This package depends on:

- `swiss-ai-hub-core` (Apache-2.0) — `AuthHandler`, `UserIdentity`, `Controller`, `KeycloakAdminService`,
  `TenantMetadataEntity`, `trace_fn`, infrastructure settings.
- `swiss-ai-hub-api` (Apache-2.0) — `ApiRunner`, `ApiLocaleString`, `ApiTestRunner` (for tests),
  `initialize_default_roles_for_tenant` (used during tenant creation to seed default roles).

Both dependencies are workspace deps. Cross-package imports go through the public `swiss_ai_hub.api` /
`swiss_ai_hub.core` interfaces (NOT deep paths) — same convention as every other cross-package import in this repo.

**Apache-2.0 → proprietary is one-way compatible**: Apache code can be embedded in this proprietary package, but the
resulting artifact remains proprietary. Proprietary code may NOT be embedded back into Apache packages. Do not let
`sysadmin_api` symbols leak into `core` or `api`.

## Commands

| Command         | What it does                                                     |
| --------------- | ---------------------------------------------------------------- |
| `make run-dev`  | uvicorn with hot reload on **:8001** (avoiding main api on 8000) |
| `make run-prod` | gunicorn multi-worker on :8000 (production / Docker)             |
| `make test`     | uv run pytest                                                    |
| `make pr-ready` | format + lint                                                    |

## Essential files

- Production entry: `swiss_ai_hub/sysadmin_api/main.py` (`swiss_ai_hub.sysadmin_api.main:app`)
- Standalone runner: `swiss_ai_hub/sysadmin_api/sysadmin_runner.py`
- Controller(s): `swiss_ai_hub/sysadmin_api/routes/tenant_admin/`
- Tests: `tests/tenant_admin/`
- Proprietary terms: `LICENSE`
- Repo-wide license matrix: `LICENSES.md` (root)
