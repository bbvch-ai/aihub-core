# deployment - Docker Compose Infrastructure-as-Code

**Purpose**: Jinja2 template system that generates all Docker Compose files and service configurations. A single
template (`docker-compose.yml.j2`) + a single config file (`compose-config.yml`) produce 10 docker-compose variants (5
stages x 2 GPU modes) plus ~80 service config files. **NEVER edit generated files directly** — edit the templates and
run `make generate-compose`.

## Folder Structure

```
deployment/
├── compose-config.yml                  # Image tags + stage-specific values (SINGLE SOURCE OF TRUTH)
├── generate_compose.py                 # Jinja2 renderer (5 stages × 2 GPU modes)
├── Makefile                            # Image mirroring utilities only (not generation)
├── templates/
│   ├── docker-compose.yml.j2          # Main compose template (~3000 lines)
│   └── configs/                       # Service config templates
│       ├── nats-config.conf.j2        # NATS server config (auth, limits, JetStream)
│       ├── litellm-config.yml.j2      # LLM router (models, guardrails, fallbacks)
│       ├── dagster-config.yml.j2      # Dagster orchestrator (DB, concurrency, timeouts)
│       ├── workspace.yml.j2           # Dagster workspace (pipeline gRPC servers)
│       ├── otel-config.yml.j2         # OTEL Collector (receivers, exporters, filtering)
│       ├── traefik-config.yml.j2      # Traefik static config (entrypoints, providers, ACME)
│       ├── traefik-middlewares.yml.j2  # Security headers middleware
│       ├── traefik-tls.yml.j2         # Self-signed cert config (local/build only)
│       ├── milvus-config.yml.j2       # Milvus vector DB config
│       ├── clickhouse-backup.xml.j2   # ClickHouse S3 named disk for BACKUP TO Disk()
│       ├── backup-dagster.yml.j2      # Backup Dagster instance config (SQLite, logging)
│       ├── backup-workspace.yml.j2    # Backup Dagster workspace (gRPC code server)
│       ├── init.Dockerfile.j2         # etcd init container
│       ├── init_etcd.sh.j2            # etcd auth setup (idempotent)
│       ├── s3-entrypoint.sh.j2        # SeaweedFS S3 gateway startup
│       ├── s3-init-buckets.sh.j2      # S3 bucket creation + CORS
│       ├── pg-init-multiple-dbs.sh.j2 # PostgreSQL multi-database init
│       ├── openwebui-init-openwebui.sh.j2  # OpenWebUI init (functions + service account)
│       └── keycloak/                  # Realm config (standalone JSON templates, see Keycloak section)
│           ├── bootstrap/             # First-start-only seeds: realm-settings, components, groups, users-superuser,
│           │                          #   identity-providers
│           └── managed/               # Reconciled every start by keycloak-config-cli: 10-roles, 20-client-scopes,
│                                      #   30-clients, 40-auth-flows, 60-service-accounts
└── templates/openwebui_functions/      # OpenWebUI Python functions (copied to configs/)
    ├── aihub_pipeline.py               # Agent connector pipe (relays title/follow-ups, tags conversations)
    ├── aihub_title_filter.py           # Outlet filter: restores agent title after OpenWebUI's first-turn fallback
    ├── openai_pipeline.py
    ├── memory_action.py
    ├── source_action.py
    └── tracing_action.py
```

**Generated outputs** (under `infra/` — NEVER edit directly):

- `infra/docker-compose.{stage}{.gpu}.yml` — 10 compose files
- `infra/configs/{service}/{config}.{stage}{.gpu}.{ext}` — ~80 stage-variant config files
- `infra/configs/{service}/{static-scripts}` — ~6 stage-independent scripts (etcd, seaweedfs, postgres, openwebui)

## Generation Pipeline

```
make generate-compose  →  uv run python deployment/generate_compose.py
```

1. Loads `compose-config.yml` as Jinja2 context
2. Renders each template across 5 stages x 2 GPU modes = 10 variants
3. Writes compose files to repo root, config files to `configs/` subdirs
4. Copies OpenWebUI Python functions from templates to `configs/openwebui/functions/`

**After ANY change to templates or `compose-config.yml`**: run `make generate-compose` and commit BOTH the template
changes AND the regenerated output files.

Note that `make generate-compose` also runs `make format-yaml`, which is repo-wide: if any YAML outside `infra/` is not
yamlfix-clean on `main`, it gets reformatted into your working tree. Revert that churn before committing so the diff
stays reviewable.

### Applying an OpenWebUI function change to a running stack

`configs/openwebui/functions/*.py` is **not** what OpenWebUI executes. The one-shot `openwebui-init` container reads
those files and upserts each one into the `function` table of the `openwebui` PostgreSQL database (`init-openwebui.sh`,
`ON CONFLICT DO UPDATE`); OpenWebUI runs the row, and `open-webui` does not even mount the functions directory. So
editing a function — or regenerating it — changes nothing about the running pipe, and neither does restarting
`open-webui` on its own, because the stale content is in the database. Re-register, then reload:

```bash
cd infra && docker compose -f docker-compose.dev.yml --env-file ../.env up openwebui-init
docker restart open-webui   # re-imports the function module
```

Verify what is actually live rather than trusting the file:

```bash
docker exec postgres psql -U admin -d openwebui \
  -tAc "select id, updated_at, length(content) from function where id='aihub-pipeline';"
```

## The Stage x Hardware Matrix

| Stage     | Traefik | SSL                | Domain               | 1st-party services | Local inference | Use case                 |
| --------- | ------- | ------------------ | -------------------- | ------------------ | --------------- | ------------------------ |
| `dev`     | None    | None               | localhost            | Not in compose     | CPU models      | Development (infra only) |
| `local`   | Yes     | mkcert self-signed | `*.127.0.0.1.nip.io` | `latest` tag       | None            | Local full-stack testing |
| `build`   | Yes     | mkcert self-signed | `*.127.0.0.1.nip.io` | Built from source  | None            | Source development       |
| `nightly` | Yes     | Let's Encrypt      | `*.${DOMAIN}`        | `nightly` tag      | None\*          | Pre-production           |
| `latest`  | Yes     | Let's Encrypt      | `*.${DOMAIN}`        | `latest` tag       | None\*          | Production               |

Each stage has a `.gpu` variant (e.g., `docker-compose.dev.gpu.yml`) adding NVIDIA GPU support for vLLM and speaches.

\*The current `nightly` and `latest` deployments run the **CPU** compose variants — all inference (chat, embeddings,
transcription) routes to Swiss LLM Cloud endpoints. The `.gpu` variants exist for GPU-capable installs.

## compose-config.yml — The Single Source of Truth

This file drives everything: template rendering, CI/CD service discovery, and image promotion.

- `global.registry_prefix` — container registry path (`ghcr.io/bbvch-ai/aihub-core/`)
- `global.volume_root` — bind mount base (`${VOLUME_ROOT:-./.docker-volumes}`)
- `image_tags` — **flat string** for infrastructure (same across all stages), **dict** for custom services (per-stage):

```yaml
# Infrastructure (flat string — always included):
nats: nats:2.11.4

# Custom service (dict — per-stage tags):
api:
  build: localbuild     # 'localbuild' triggers build: directive instead of image:
  local: api:latest
  nightly: api:nightly
  latest: api:latest
# No 'dev' key → api is excluded from docker-compose.dev.yml

# Postgres is project-managed but published out-of-band: the Dockerfile at
# infra/deployment/docker/postgres/Dockerfile extends pgvector/pgvector:pg17
# with postgresql-17-repack (required by the maintenance subsystem in
# packages/backup). All stages pull the same pinned tag from ghcr; re-publish
# via `make -C infra/deployment build-and-push-postgres-image` after editing
# the Dockerfile.
postgres: pgvector-repack:pg17
```

### Publishing the postgres image

The postgres image is project-managed. Unlike upstream-mirrored images (`make mirror-image`), it's built from our own
Dockerfile and published manually via `make -C infra/deployment build-and-push-postgres-image` (requires
`docker login ghcr.io`). Re-publish whenever:

- The base pgvector tag in `docker/postgres/Dockerfile` changes (Postgres major bump, e.g. `pg17` → `pg18`)
- The `postgresql-17-repack` package needs upgrading (security or bugfix)

After publishing, non-build stages pick up the new image automatically via `docker compose pull`. The `build` stage
continues to build locally so developers test Dockerfile edits without round-tripping through the registry.

### Publishing the open-terminal image

The open-terminal image is project-managed. It extends `ghcr.io/open-webui/open-terminal:0.11.34` with additional Python
libraries (reportlab, fpdf2 — the base already ships pandas/openpyxl/python-docx/weasyprint/matplotlib/xlsxwriter) and
is published manually via `make -C infra/deployment build-and-push-open-terminal-image` (requires
`docker login ghcr.io`). Re-publish whenever:

- The upstream `open-terminal` base tag in `docker/open-terminal/Dockerfile` needs bumping
- A new Python library dependency must be baked into the image

After publishing, all stages pull the new image automatically via `docker compose pull`. See ADR:
`docs/arc42/decisions/2026_06_22_openwebui_code_execution_open_terminal.md`.

> **Deployment checklist:** Publish `open-terminal-office:0.11.34` to ghcr **before any non-dev stage pulls it**.
> Non-dev stages (`local`/`build` build locally, but `nightly`/`latest` pull from the registry) reference this exact
> tag; if it is not yet published, `open-webui` fails its `depends_on: open-terminal (service_healthy)` gate and the
> stack will not come up. Run `make -C infra/deployment build-and-push-open-terminal-image` first.

**CI/CD integration**: GitHub Actions workflows (`build-agents.yml`, `set-latest.yml`) parse `compose-config.yml` at
runtime to dynamically discover which services to build and promote. Adding a new agent here is all you need for CI.

## Service Inclusion Logic

The template conditionally includes services based on stage and GPU mode:

- **Infrastructure** (postgres, milvus, nats, valkey, etcd, etc.) — always included
- **AI inference** (speaches, vLLM) — vLLM only when `gpu_enabled`, speaches in all stages
- **1st-party services** (api, web, agents, bot, dagster, pipelines) — only when `image_tags.{service}[stage]` exists
- **Traefik + docker-socket-proxy** — all stages except `dev`
- **oauth2proxy sidecars** (for Attu, Dagster, SeaweedFS admin UIs) — all stages except `dev`
- **PgBouncer** — all stages except `dev` (dev connects directly to PostgreSQL)
- **vLLM** — only when `gpu_enabled`

Port exposure: direct localhost ports (`8080:8080`) only in `dev`, `local`, `build`. In `nightly`/`latest`, all traffic
routes through Traefik.

## Network Isolation (6 Zones)

| Network        | Purpose                           | Internal | ICC | Key Services                                                  |
| -------------- | --------------------------------- | -------- | --- | ------------------------------------------------------------- |
| `proxy`        | External ingress via Traefik      | No       | Yes | traefik, api, web, open-webui, langfuse-web                   |
| `backend`      | Application/processing services   | Yes\*    | Yes | litellm, langfuse-\*, mineru-api, vLLM (GPU), jupyter, otel   |
| `data`         | Databases, caches, message broker | Yes\*    | Yes | postgres, ferretdb, milvus, neo4j, valkey, nats, click        |
| `storage`      | SeaweedFS cluster                 | Yes\*    | Yes | seaweedfs-\*, etcd                                            |
| `egress`       | Outbound internet only            | No       | No  | playwright (ICC disabled — containers can't reach each other) |
| `code-sandbox` | Code-execution sandbox + callers  | Yes\*    | Yes | open-terminal (+ open-webui as caller; agents as a follow-up) |

\*Internal in non-dev stages. Dev has all networks non-internal for localhost access.

**Cross-network bridges**: Services needing multiple zones get multiple networks (e.g., `seaweedfs-s3` on
storage+backend, `milvus-standalone` on data+storage, `api` on proxy+backend+data+storage, `open-webui` on
proxy+backend+data+storage+code-sandbox).

**`code-sandbox` rationale**: `open-terminal` runs arbitrary user code, so it lives **alone** in `code-sandbox` (not
`backend`). Docker networks are bidirectional — sharing `backend` would let a sandbox breakout reach every backend
service. Callers (open-webui now, agents later) opt in by adding `code-sandbox` to their own network list; the sandbox
itself never joins another zone, so it can reach only its callers. `internal: true` in non-dev also denies it outbound
internet.

**Special**: `open-webui` uses `network_mode: "host"` in dev (to reach services running locally outside Docker).

See ADR: `docs/arc42/decisions/2025_12_22_docker_network_isolation.md`

## Keycloak Realm Configuration (Operator Notes)

The realm config lives in standalone JSON templates under `templates/configs/keycloak/`, split by lifecycle (see ADR
`2026_06_12_declarative_keycloak_realm_reconciliation`):

- **`bootstrap/`** — applied via `--import-realm` on **first start only**, never reconciled: realm-level settings
  (themes, brute force, token and session lifespans, SMTP), the user-profile component, the startup tenant group seed,
  the superuser seed, and the **identity providers** (Azure Entra ID + its mappers). Operator changes to these in the
  admin console survive restarts — and updating identity-provider config on an already-initialized deployment requires
  the admin console (or a fresh realm DB), since they do not reconcile automatically.
- **`managed/`** — reconciled on **every stack start** by the one-shot `keycloak-config` service
  (adorsys/keycloak-config-cli): realm roles, client scopes, clients, custom auth flows, and the `aihub-api-service`
  service account. **File wins**: admin-console edits to these objects are overwritten, and objects removed from config
  are deleted from running realms. Users, tenant groups, and identity providers are never touched
  (`IMPORT_MANAGED_IDENTITYPROVIDER`/`IMPORT_MANAGED_GROUP` are set to `no-delete` as defense in depth).

Rules when editing:

- All entities of one type MUST stay in their single managed file — keycloak-config-cli processes each file as a
  separate full-managed import, so a second file containing e.g. `clients` would delete the first file's clients. The
  numeric prefixes encode the import order (roles → scopes → clients → flows → service accounts).
- Placeholders use keycloak-config-cli syntax: `$(env:VAR)` inside JSON strings, and the quoted `"$(envjson:VAR)"`
  sentinel for raw JSON injection (superuser roles). The entrypoint's bash envsubst handles the same syntax for the
  first-start import. Never use `${VAR}` — it collides with Keycloak-internal placeholders.
- `generate_compose.py` renders the managed templates 1:1 as keycloak-config-cli inputs AND JSON-merges bootstrap +
  managed into `aihub-realm.{stage}.json` for `--import-realm` (fresh boots come up complete without waiting for the
  reconciler). Run `make generate-compose` after any edit and commit the regenerated files.
- The `keycloak-config-cli` image tag in `compose-config.yml` must be bumped together with the Keycloak image (tag
  scheme `{cli-version}-{keycloak-version}`, mirrored via `make mirror-image`).

The `aihub-api-service` service account (`managed/60-service-accounts.json.j2`) carries a fixed set of
`realm-management` client roles. The current minimum required for the API to function correctly is:

```
view-identity-providers, manage-users, view-users, query-users,
query-groups, view-groups, view-realm, view-clients
```

`view-realm` and `view-clients` are required by the realm-role-members endpoint
(`GET /admin/realms/{realm}/roles/{role}/users`) used to resolve sysadmin status. Role changes here now reach running
deployments on the next start.

**Langfuse sysadmin gate**: the `langfuse` client carries the marker client scope `langfuse-sysadmin-gate` (default
scope, no mappers). It activates a conditional deny sub-flow — deny unless the user has `AIHubSysAdmin` — in the custom
`browser-aihub` flow (bound as the realm browser flow) and in the `Post Broker Login - AIHubAccess Check` flow. The
whole gate is **managed** config: the flows, the authenticator configs and the realm `browserFlow` binding live in
`managed/40-auth-flows.json.j2`, the marker scope in `managed/20-client-scopes.json.j2`, and its attachment to the
`langfuse` client in `managed/30-clients.json.j2`. keycloak-config-cli reconciles them on every start (no `kcadm` in the
entrypoint), so already-running instances converge on the next restart. The `browserFlow` binding lives in the managed
auth-flows file (not bootstrap realm settings) precisely so kcc rebinds it every start — activating the gate on existing
deployments, not just on the first `--import-realm`. See ADR
`docs/arc42/decisions/2026_06_11_langfuse_access_restricted_to_sysadmins.md`. The `browser-aihub` flow replicates the
built-in browser flow and must be reviewed on Keycloak major upgrades. Structural caveat: the authentication
alternatives (cookie, IdP redirector, forms) are nested in a REQUIRED sub-flow — never place a CONDITIONAL sub-flow at
the same level as ALTERNATIVE executions, or Keycloak ignores the alternatives and login breaks for all clients.

## Env Var Conventions

- `.env.dev` — local development template (copy to `.env` to get started)
- `.env.prod` — production template (all secrets as `REPLACE_WITH_RANDOM_STRING` placeholders)
- **No `${VAR:-default}` in templates** — all defaults must be in `.env.dev` / `.env.prod`
- Internal Docker hostnames are hardcoded in the Jinja2 template as variables (e.g.,
  `NATS_ENDPOINT = "nats://nats:4222"`) — never use env vars for Docker-to-Docker communication
- Only external/override endpoints (for services running on the host outside Docker) use env vars
- **`OTEL_DEPLOYMENT_ENVIRONMENT` / `OTEL_HOST_NAME` are the one sanctioned `${VAR:-default}`.** The
  collector's `resource/deployment` processor stamps them onto every pipeline, and an *empty* value
  makes that processor fail to build — which exits the collector. Every service that exports OTLP
  now declares `depends_on: otel-collector`, so an unset var no longer merely drops telemetry: it
  holds up the app plane. Values are written per-VM into the stage's environment file by
  `aihub-playbook`'s `env.j2`; the stage-name fallback is what keeps a non-Ansible deploy starting
  at all. Do not "fix" it by moving the default to `.env.prod`.

### Which collector owns which signal

Two collectors run on a deployed VM and it matters which one you change:

| Collector                              | Owner           | Handles                                                                    |
| -------------------------------------- | --------------- | -------------------------------------------------------------------------- |
| `otel-collector` (this compose)        | aihub-core      | OTLP from the instrumented Python services → SigNoz + Langfuse             |
| `otel-collector-docker`                | aihub-playbook  | `docker_stats`, health events, and **third-party container stdout/stderr** |

App services export to `http://otel-collector:4317`, so the playbook's collector never sees their
telemetry — that is why `resource/deployment` has to exist here too. Conversely, **do not add a
`filelog` receiver for container logs here**: the playbook already tails them (via
`/var/log/docker-logs/*` symlinks, so records carry the container *name* and the VM's real
`host.name`), and a second tailer would ingest every line twice into a paid backend.

## Traefik Configuration

**Priority hierarchy** (defined in template header):

| Range      | Purpose                                          |
| ---------- | ------------------------------------------------ |
| 10000-9000 | System/infrastructure (ACME challenges)          |
| 8000-7000  | Security/auth (OAuth callbacks, auth APIs)       |
| 6000-5000  | API routes (specific APIs at 6000, general 5000) |
| 4000-3000  | Application features (admin UIs, management)     |
| 2500-1500  | Static content/assets                            |
| 1000-500   | Service-specific catch-alls, subdomain routing   |
| 400-1      | Fallback (domain catch-all, HTTP→HTTPS redirect) |

- Docker provider via `docker-socket-proxy` (never direct Docker socket access)
- `local`/`build`: mkcert self-signed certs — generate with `make local-cert`
- `nightly`/`latest`: Let's Encrypt ACME auto-renewal
- Admin tools use `oauth2proxy-{service}` sidecar between Traefik and the service for OIDC auth

## Adding a New Service

1. Add image tag to `compose-config.yml` (dict with per-stage tags, or flat string for infra)
2. Add service definition to `templates/docker-compose.yml.j2` with appropriate `{% if %}` stage guards
3. Assign to correct network zone(s) based on what the service needs to reach
4. Add a healthcheck (all services must have one)
5. Add logging config: `logging: { driver: json-file, options: { max-size: "10m", max-file: "2" } }`
6. If the service needs config: create a template in `templates/configs/`, register output in `generate_compose.py`
7. If admin UI: add `oauth2proxy-{service}` sidecar + Traefik labels (copy existing pattern)
8. Run `make generate-compose`
9. Commit template changes + config changes + ALL regenerated files

## Adding a New Agent or Pipeline

Streamlined workflow — CI auto-discovers from `compose-config.yml`:

1. Add entry to `image_tags` in `compose-config.yml`:
   ```yaml
   my_new_agent:
     build: localbuild
     local: my_new_agent:latest
     nightly: my_new_agent:nightly
     latest: my_new_agent:latest
   ```
2. Add service block in `templates/docker-compose.yml.j2` (copy an existing agent service block)
3. Run `make generate-compose`
4. CI (`build-agents.yml`) automatically discovers and builds the new service

## Sysadmin Subdomain

The system-administration plane (`packages/sysadmin-api`, `packages/sysadmin-web` — AGPL-3.0-or-later) is served on its
**own subdomain** `sysadmin.${DOMAIN}`, separate from the main app on `${DOMAIN}`. Routing is **path-split** via
Traefik: `sysadmin-web` (static SPA) serves `/` and `sysadmin-api` serves `/api/v1` (priority 6000, above the web
catch-alls, mirroring the main `api`/`web` priority pattern). Both share the **same Keycloak realm and `aihub-frontend`
client** as the main app, so the realm SSO cookie spans `${DOMAIN}` and `sysadmin.${DOMAIN}` — the realm import (see
Keycloak Operator Notes) adds the `sysadmin.${DOMAIN}` redirect URIs / web origins. Let's Encrypt SANs must include
`sysadmin.${DOMAIN}` before the first prod deploy.

`compose-config.yml` keys are **hyphenated** (`sysadmin-api`, `sysadmin-web`) — not `sysadmin_api`. The key must equal
the published image name because `set-latest.yml` auto-discovery requires `image_tags[k].latest == "{k}:latest"` and
retags `ghcr.io/.../{k}`. Because the hyphen is not a valid Jinja attribute identifier, the template uses bracket access
(`image_tags['sysadmin-api'][stage]`); `get_service_version` already uses bracket access.

To add another management plane in future, follow the same recipe: hyphenated `compose-config.yml` key (== image ==
package dir), a service block on the `sysadmin.${DOMAIN}` host (or a new subdomain) with bracket-access image tags, the
per-package `LICENSE` + `LICENSES.md` row, and the `build-sysadmin.yml` matrix / `lint-pr.yml` matrices extended.

## Key Files

- **Config (source of truth)**: `deployment/compose-config.yml`
- **Generator**: `deployment/generate_compose.py`
- **Main template**: `deployment/templates/docker-compose.yml.j2`
- **Config templates**: `deployment/templates/configs/`
- **Generated compose files**: `infra/docker-compose.{stage}{.gpu}.yml`
- **Generated service configs**: `infra/configs/`
- **Env templates**: `.env.dev`, `.env.prod`
- **ADR (network isolation)**: `docs/arc42/decisions/2025_12_22_docker_network_isolation.md`
- **ADR (deployment architecture)**: `docs/arc42/decisions/2025_08_11_containerized_deployment_architecture.md`
