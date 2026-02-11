---
name: docker-dev
description: Manage the Docker development environment. Start, stop, check health,
  view logs, and troubleshoot services. Use when working with the Docker stack.
disable-model-invocation: true
allowed-tools: Bash, Read
---

# Docker Development Environment Manager

Manage the Docker Compose dev stack. Action via `$ARGUMENTS`.

## Available Actions

### `up` — Start the development stack
```bash
docker compose -f docker-compose.dev.yml --env-file .env up -d --build
```
Verify `.env` exists (copy from `.env.dev` if missing). Report service URLs when done.

### `down` — Stop the development stack
```bash
docker compose -f docker-compose.dev.yml down
```

### `health` — Check all service health statuses
Run `docker compose -f docker-compose.dev.yml ps --format json`. For each service report: name, status, health, ports. Check connectivity to key endpoints: API (8000), OpenWebUI (8080), Phoenix (6006), NATS (8222), SeaweedFS (8889).

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

| Service    | URL                   | Purpose            |
|------------|-----------------------|--------------------|
| API        | http://localhost:8000 | REST API + Swagger |
| OpenWebUI  | http://localhost:8080 | Chat interface     |
| Admin UI   | http://localhost:3000 | Nuxt management UI |
| Phoenix    | http://localhost:6006 | AI observability   |
| NATS       | http://localhost:8222 | NATS dashboard     |
| SeaweedFS  | http://localhost:8889 | Object storage     |

## Key Files

- Docker Compose (dev): `/home/user/aihub-core/docker-compose.dev.yml`
- Environment config: `/home/user/aihub-core/.env` (from `.env.dev`)
- Compose template: `/home/user/aihub-core/deployment/templates/docker-compose.yml.j2`
