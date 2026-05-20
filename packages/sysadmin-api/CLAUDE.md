# packages/sysadmin-api - System Administration API (Proprietary)

**Purpose**: FastAPI service for system-administrator-only operations. Multi-tenant management lives here. Runs as a
separate Docker image on `sysadmin.${DOMAIN}/api/v1/*`.

**License**: Proprietary — All Rights Reserved (`LicenseRef-Proprietary`). No use granted; commercial license required
for any use. The package's `LICENSE` is the authoritative source for terms.

## Scope responsibility

Anything that requires the `AIHubSysAdmin` Keycloak realm role and is **not tenant-scoped**. Today:

- Tenant lifecycle management (`TenantAdminController` — list / get / create / update / delete tenant metadata).

NOT here:

- Anything tenant-scoped (those endpoints belong in `packages/api`, mounted at `/api/v1/{tenant_id}/...`).
- `MyTenantController` (user-facing "list my tenants" / "switch active tenant") — stays in `packages/api` because every
  user needs it, not just sysadmins.
- Agent/process runtime, knowledge, threads, events — those are the platform runtime, stay in `packages/api`.

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
│   ├── asgi.py                   # Production ASGI entry (swiss_ai_hub.sysadmin_api.asgi:app)
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

`SysadminApiRunner` is ~90 lines: a plain `FastAPI` app mounted under `/api/v1` via Starlette, CORS middleware, a
MongoDB-only lifespan, and a `mount()` that matches `Controller.mount(app, runner)`. It does **not**:

- build an MCP server (sysadmin-api has no MCP need)
- add the i18n middleware (sysadmin endpoints don't consume request locale; `ApiLocaleString` class attributes load
  their YAML at import time, which needs no middleware)
- inject `tenant_id` into the OpenAPI schema (sysadmin-api has no tenant-prefixed routes — `{tenant_id}` is an explicit
  path parameter on the endpoints that take it)

**The entire lifespan** is: connect to MongoDB on startup, disconnect on shutdown. There is no "full" variant and no
NATS/Milvus/Redis/S3/Neo4j/WebSocket/discovery/provisioner wiring anywhere. If a future sysadmin operation needs another
resource, add it explicitly to `_sysadmin_lifespan` in `sysadmin_runner.py`.

When #1203 (the `aihub-daemon` extraction that thins the main API's `lifetime_manager`) lands, **nothing here needs to
change** — sysadmin-api never depended on the API's lifespan in the first place.

## Entry point

`swiss_ai_hub.sysadmin_api.asgi:app` (gunicorn target). Deliberately a fully-qualified module path, **not** `app.main` —
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

- Production entry: `swiss_ai_hub/sysadmin_api/asgi.py` (`swiss_ai_hub.sysadmin_api.asgi:app`)
- Standalone runner: `swiss_ai_hub/sysadmin_api/sysadmin_runner.py`
- Controller(s): `swiss_ai_hub/sysadmin_api/routes/tenant_admin/`
- Tests: `tests/tenant_admin/`
- Proprietary terms: `LICENSE`
- Repo-wide license matrix: `LICENSES.md` (root)
