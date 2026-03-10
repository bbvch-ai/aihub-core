---
name: docker-dev
description: Manage the Docker Compose development stack and understand the Jinja2 template-based compose generation system. Covers start/stop/health/logs/restart/status/ports for the dev stack, the template-to-generate-to-commit workflow, and documentation lookup via Context7 MCP. Use when user says 'start docker', 'stop containers', 'check service health', 'show logs', 'restart service', 'docker status', 'which ports are used', 'is the API running', 'regenerate compose', or 'how does docker compose generation work'. Pass action as argument. Do NOT use for reviewing Docker Compose changes (use deployment-reviewer agent) or debugging Dagster pipelines (use /debug-pipeline).
allowed-tools: Bash, Read, Grep, Glob
---

# Docker Development Environment Manager

Manage the Docker Compose dev stack and the Jinja2 template generation system. The action is passed via `$ARGUMENTS`.

## Documentation Lookup

For Docker Compose or Traefik questions, use Context7 MCP to fetch up-to-date docs:

- **Docker Compose**: `mcp__context7__resolve-library-id` with query `docker compose`, then `mcp__context7__query-docs`
  with library ID `/docker/compose`
- **Traefik**: `mcp__context7__resolve-library-id` with query `traefik`, then `mcp__context7__query-docs` with library
  ID `/websites/doc_traefik_io_traefik`

## Day-to-Day Actions

### `up` — Start the development stack

```bash
docker compose -f docker-compose.dev.yml --env-file .env up -d --build
```

**Pre-check**: Verify `.env` exists at the repo root. If missing, copy from `.env.dev`:

```bash
cp .env.dev .env
```

### `down` — Stop the development stack

```bash
docker compose -f docker-compose.dev.yml down
```

### `health` — Check all service health statuses

1. Run `docker compose -f docker-compose.dev.yml ps --format json`
2. For each service, report: name, status, health, exposed ports
3. Test connectivity to key endpoints with `curl -s -o /dev/null -w "%{http_code}"`:
   - API: http://localhost:8000
   - OpenWebUI: http://localhost:8080
   - Langfuse: http://localhost:6006
   - LiteLLM: http://localhost:4000
   - Dagster: http://localhost:3000
   - SeaweedFS: http://localhost:8889
   - NATS: http://localhost:8222

### `logs <service>` — Tail logs for a specific service

```bash
docker compose -f docker-compose.dev.yml logs --tail 100 -f <service>
```

### `restart <service>` — Restart a specific service

```bash
docker compose -f docker-compose.dev.yml restart <service>
```

### `status` — Show running containers with resource usage

```bash
docker compose -f docker-compose.dev.yml ps
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### `ports` — Show all exposed service URLs

| Service        | Port   | Purpose                         |
| -------------- | ------ | ------------------------------- |
| API            | :8000  | REST API + WebSocket (local)    |
| OpenWebUI      | :8080  | Chat interface                  |
| Admin UI       | :3333  | Nuxt management UI (local)      |
| Dagster        | :3000  | Pipeline orchestrator (local)   |
| LiteLLM        | :4000  | LLM proxy                       |
| Langfuse       | :6006  | LLM observability               |
| MinerU         | :5001  | Document parsing                |
| PostgreSQL     | :5432  | Relational DB (4 databases)     |
| FerretDB       | :27017 | MongoDB-compatible              |
| Milvus         | :19530 | Vector DB                       |
| Neo4j          | :7474  | Graph DB (web), :7687 (bolt)    |
| Valkey         | :6379  | Redis-compatible cache          |
| NATS           | :4222  | Message broker, :8222 (monitor) |
| SeaweedFS      | :8889  | Filer UI, :9000 (S3 gateway)    |
| Rclone         | :5572  | Cloud sync RC API               |
| Speaches       | :8185  | STT/TTS                         |
| Jupyter        | :8888  | Code execution sandbox          |
| Playwright     | :3036  | Browser automation              |
| Attu           | :3003  | Milvus admin UI                 |
| OTEL Collector | :4317  | gRPC receiver, :4318 (HTTP)     |

Note: API (:8000), Admin UI (:3333), and Dagster (:3000) run **locally outside Docker** in dev — they're not in
`docker-compose.dev.yml`.

### `generate` — Regenerate compose files from templates

```bash
make generate-compose
```

Run this after editing any template in `deployment/templates/` or `deployment/compose-config.yml`. Commit both the
template changes and the regenerated output files.

## Compose Generation System

Read `deployment/CLAUDE.md` for full details. Quick overview:

**Architecture**: A single Jinja2 template (`deployment/templates/docker-compose.yml.j2`) + a single config file
(`deployment/compose-config.yml`) produce 10 docker-compose variants (5 stages x 2 GPU modes).

**Key files**:

- `deployment/compose-config.yml` — image tags + stage-specific values (SINGLE SOURCE OF TRUTH)
- `deployment/generate_compose.py` — Jinja2 renderer
- `deployment/templates/docker-compose.yml.j2` — main template (~3000 lines)
- `deployment/templates/configs/` — 15 service config templates (NATS, LiteLLM, Traefik, Milvus, etc.)

**5 Stages**:

| Stage     | Traefik | 1st-party services | Use case           |
| --------- | ------- | ------------------ | ------------------ |
| `dev`     | No      | Not in compose     | Development        |
| `local`   | Yes     | `latest` tag       | Local full-stack   |
| `build`   | Yes     | Built from source  | Source development |
| `nightly` | Yes     | `nightly` tag      | Pre-production     |
| `latest`  | Yes     | `latest` tag       | Production         |

Each stage has a `.gpu` variant adding NVIDIA GPU support.

**Generated outputs** (at repo root — NEVER edit directly):

- `docker-compose.{stage}{.gpu}.yml` — 10 compose files
- `configs/{service}/{config}` — ~80 service config files

**Workflow for template changes**: Edit template → `make generate-compose` → commit templates + generated files.

## Network Zones

5 isolated Docker networks (see `docs/arc42/decisions/2025_12_22_docker_network_isolation.md`):

| Network   | Purpose                      | Key Services                              |
| --------- | ---------------------------- | ----------------------------------------- |
| `proxy`   | External ingress via Traefik | traefik, api, web, open-webui, langfuse   |
| `backend` | Application services         | litellm, langfuse, mineru-api, vLLM (GPU) |
| `data`    | Databases, caches, broker    | postgres, ferretdb, milvus, nats, valkey  |
| `storage` | SeaweedFS cluster            | seaweedfs-\*, etcd                        |
| `egress`  | Outbound internet (no ICC)   | playwright                                |

Dev stage has all networks non-internal for localhost access.

## Examples

- `/docker-dev up` — Start all services
- `/docker-dev down` — Stop all services
- `/docker-dev health` — Check which services are running and healthy
- `/docker-dev logs nats` — Tail NATS logs
- `/docker-dev restart litellm` — Restart LiteLLM proxy
- `/docker-dev status` — Show containers and resource usage
- `/docker-dev ports` — List all service URLs
- `/docker-dev generate` — Regenerate compose files from templates

## Troubleshooting

| Problem                         | Solution                                                           |
| ------------------------------- | ------------------------------------------------------------------ |
| `.env` file not found           | Copy `.env.dev` to `.env` at the repo root                         |
| Port already in use             | Run `lsof -i :<port>` to find the process, then stop it            |
| Service keeps restarting        | Check logs with `/docker-dev logs <service>`                       |
| Need Docker Compose docs        | Use Context7: library ID `/docker/compose`                         |
| Need Traefik docs               | Use Context7: library ID `/websites/doc_traefik_io_traefik`        |
| Template change not reflected   | Run `make generate-compose` and commit regenerated files           |
| Edited a generated compose file | Revert — edit `deployment/templates/docker-compose.yml.j2` instead |
| Service missing from compose    | Add image tag to `deployment/compose-config.yml` for target stage  |
