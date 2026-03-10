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
│       ├── init.Dockerfile.j2         # etcd init container
│       ├── init_etcd.sh.j2            # etcd auth setup (idempotent)
│       ├── s3-entrypoint.sh.j2        # SeaweedFS S3 gateway startup
│       ├── s3-init-buckets.sh.j2      # S3 bucket creation + CORS
│       ├── pg-init-multiple-dbs.sh.j2 # PostgreSQL multi-database init
│       └── openwebui-init-openwebui.sh.j2  # OpenWebUI init (functions + service account)
└── templates/openwebui_functions/      # OpenWebUI Python functions (copied to configs/)
    ├── aihub_pipeline.py
    ├── openai_pipeline.py
    ├── memory_action.py
    ├── source_action.py
    └── tracing_action.py
```

**Generated outputs** (at repo root — NEVER edit directly):

- `docker-compose.{stage}{.gpu}.yml` — 10 compose files
- `configs/{service}/{config}.{stage}{.gpu}.{ext}` — ~70 stage-variant config files
- `configs/{service}/{static-scripts}` — ~6 stage-independent scripts (etcd, seaweedfs, postgres, openwebui)

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

## The Stage x Hardware Matrix

| Stage     | Traefik | SSL                | Domain               | 1st-party services | Local inference | Use case                 |
| --------- | ------- | ------------------ | -------------------- | ------------------ | --------------- | ------------------------ |
| `dev`     | None    | None               | localhost            | Not in compose     | CPU models      | Development (infra only) |
| `local`   | Yes     | mkcert self-signed | `*.127.0.0.1.nip.io` | `latest` tag       | None            | Local full-stack testing |
| `build`   | Yes     | mkcert self-signed | `*.127.0.0.1.nip.io` | Built from source  | None            | Source development       |
| `nightly` | Yes     | Let's Encrypt      | `*.${DOMAIN}`        | `nightly` tag      | GPU models      | Pre-production           |
| `latest`  | Yes     | Let's Encrypt      | `*.${DOMAIN}`        | `latest` tag       | GPU models      | Production               |

Each stage has a `.gpu` variant (e.g., `docker-compose.dev.gpu.yml`) adding NVIDIA GPU support for vLLM and speaches.

## compose-config.yml — The Single Source of Truth

This file drives everything: template rendering, CI/CD service discovery, and image promotion.

- `global.registry_prefix` — container registry path (`ghcr.io/bbvch-ai/aihub-core/`)
- `global.volume_root` — bind mount base (`${VOLUME_ROOT:-./.docker-volumes}`)
- `image_tags` — **flat string** for infrastructure (same across all stages), **dict** for custom services (per-stage):

```yaml
# Infrastructure (flat string — always included):
postgres: pgvector:pg17
nats: nats:2.11.4

# Custom service (dict — per-stage tags):
api:
  build: localbuild     # 'localbuild' triggers build: directive instead of image:
  local: api:latest
  nightly: api:nightly
  latest: api:latest
# No 'dev' key → api is excluded from docker-compose.dev.yml
```

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

## Network Isolation (5 Zones)

| Network   | Purpose                           | Internal | ICC | Key Services                                                  |
| --------- | --------------------------------- | -------- | --- | ------------------------------------------------------------- |
| `proxy`   | External ingress via Traefik      | No       | Yes | traefik, api, web, open-webui, langfuse-web                   |
| `backend` | Application/processing services   | Yes\*    | Yes | litellm, langfuse-\*, mineru-api, vLLM (GPU), jupyter, otel   |
| `data`    | Databases, caches, message broker | Yes\*    | Yes | postgres, ferretdb, milvus, neo4j, valkey, nats, click        |
| `storage` | SeaweedFS cluster                 | Yes\*    | Yes | seaweedfs-\*, etcd                                            |
| `egress`  | Outbound internet only            | No       | No  | playwright (ICC disabled — containers can't reach each other) |

\*Internal in non-dev stages. Dev has all networks non-internal for localhost access.

**Cross-network bridges**: Services needing multiple zones get multiple networks (e.g., `seaweedfs-s3` on
storage+backend, `milvus-standalone` on data+storage, `api` on proxy+backend+data+storage).

**Special**: `open-webui` uses `network_mode: "host"` in dev (to reach services running locally outside Docker).

See ADR: `aihub_doc/arc42/decisions/2025_12_22_docker_network_isolation.md`

## Env Var Conventions

- `.env.dev` — local development template (copy to `.env` to get started)
- `.env.prod` — production template (all secrets as `REPLACE_WITH_RANDOM_STRING` placeholders)
- **No `${VAR:-default}` in templates** — all defaults must be in `.env.dev` / `.env.prod`
- Internal Docker hostnames are hardcoded in the Jinja2 template as variables (e.g.,
  `NATS_ENDPOINT = "nats://nats:4222"`) — never use env vars for Docker-to-Docker communication
- Only external/override endpoints (for services running on the host outside Docker) use env vars

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

## Key Files

- **Config (source of truth)**: `deployment/compose-config.yml`
- **Generator**: `deployment/generate_compose.py`
- **Main template**: `deployment/templates/docker-compose.yml.j2`
- **Config templates**: `deployment/templates/configs/`
- **Generated compose files**: `docker-compose.{stage}{.gpu}.yml` (repo root)
- **Generated service configs**: `configs/` (repo root)
- **Env templates**: `.env.dev`, `.env.prod`
- **ADR (network isolation)**: `aihub_doc/arc42/decisions/2025_12_22_docker_network_isolation.md`
- **ADR (deployment architecture)**: `aihub_doc/arc42/decisions/2025_08_11_containerized_deployment_architecture.md`
