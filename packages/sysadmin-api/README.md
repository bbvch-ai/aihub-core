# packages/sysadmin-api — Swiss AI Hub system administration API

**License**: Proprietary — All Rights Reserved (`LicenseRef-Proprietary`). No use granted; commercial license required
for any use. See `LICENSE` for full terms.

System administration plane for Swiss AI Hub. Carries endpoints that operate **above** the per-tenant data plane:
managing tenants, sysadmin role-gated platform actions, and (in future) other AIHubSysAdmin-only operations. Runs as its
own FastAPI service on `sysadmin.${DOMAIN}/api/v1/*`.

## Why a separate package?

The main `packages/api` ships under Apache-2.0. The sysadmin plane is the platform's commercial value-add and ships
under a strict proprietary "All Rights Reserved" notice, so it must be a separately-licensed artifact. Keeping it
physically separate also avoids accidentally pulling proprietary terms onto any Apache-2.0 dependency.

## What's in it

Owned by this package: `TenantAdminController` (six endpoints under `/admin/tenants/*`) — tenant lifecycle management,
sysadmin-gated.

Re-mounted from `packages/api` (Apache-2.0) so sysadmin-web's inherited composables resolve same-origin against
sysadmin-api: `MyAccountController.get_my_identity()`, `UserController` (get/list + role assign/revoke),
`RoleController`, `AuthProviderController`. Code ownership stays in `packages/api`; sysadmin-api only picks the surface
it needs. See `packages/sysadmin-api/CLAUDE.md` for the full mount table.

In future: anything that requires the `AIHubSysAdmin` Keycloak realm role and is not tenant-scoped (platform-wide
sysadmin operations beyond tenant lifecycle).

## Runtime

- Port: `8000` inside the container, exposed as `sysadmin.${DOMAIN}/api/v1` via Traefik path-prefix routing on the
  sysadmin subdomain.
- Auth: Same Keycloak realm + same `aihub-frontend` client as the main `api`. The `AIHubSysAdmin` realm role gate
  applies to every endpoint.
- Runtime infra: MongoDB + NATS + Redis + `AccessChangeHook` (medium lifespan). `SysadminApiRunner` in
  `swiss_ai_hub/sysadmin_api/sysadmin_runner.py` wires the subset of dependencies needed by the controllers it mounts —
  deliberately omits Milvus / S3 / Neo4j / WebSocket / discovery / provisioners / RPC responders. See ADR
  `2026_05_26_sysadmin_api_full_self_contained_lifespan.md`.
- Local dev: `make run-dev` runs the API on port `8001` (so the main `api` on `8000` is unaffected).

## Tests

```
make test          # uv run pytest
make test-cov      # with coverage report
```

The `tests/conftest.py` mirrors `packages/api/playground/testing/tests/conftest.py` — same db-isolation, same auth and
entity mocks, same skip-external-provisioning behaviour. The shared fixtures all live in `swiss_ai_hub.core.testing.*`
and are imported here, not duplicated.

## Adding a new sysadmin endpoint

1. Create the controller and service under `swiss_ai_hub/sysadmin_api/routes/<domain>/` (one file per class). Use
   `Security(self.sys_admin_user())` from the `Controller` base class — every endpoint in this package must be
   sysadmin-gated.
2. Add an i18n entry for `name`/`description` under `swiss_ai_hub/sysadmin_api/i18n/translations/sysadmin/controllers.*`
   using `SysadminApiLocaleString` (the proprietary counterpart of `ApiLocaleString` — keeps proprietary strings out of
   the Apache-2.0 `packages/api`).
3. Register on `runner.mount(...)` in `swiss_ai_hub/sysadmin_api/main.py` using the fluent builder pattern.
4. Add unit + sysadmin-gate tests in `tests/<domain>/`.

## See also

- `docs/arc42/decisions/2026_05_19_split-sysadmin-into-proprietary-packages.md` (ADR for the extraction)
- `docs/arc42/decisions/2026_05_26_sysadmin_api_full_self_contained_lifespan.md` (ADR for the medium lifespan)
- `packages/api/CLAUDE.md` — the parent API package
- `LICENSES.md` (repo root) — the per-package license matrix
