---
name: docker-dev
description: Manage the Docker Compose development stack (start, stop, health, logs,
  restart, status, ports). Use when user says 'start docker', 'stop containers',
  'check service health', 'show logs', 'restart service', 'docker status',
  'which ports are used', or 'is the API running'. Pass action as argument.
allowed-tools: Bash, Read
---

# Docker Development Environment Manager

Manage the Docker Compose dev stack. The action is passed via `$ARGUMENTS`.

## Available Actions

### 1. `up` — Start the development stack

```bash
docker compose -f docker-compose.dev.yml --env-file .env up -d --build
```

**Pre-check**: Verify `.env` exists at `/home/user/aihub-core/.env`. If missing, copy from `.env.dev`:
```bash
cp /home/user/aihub-core/.env.dev /home/user/aihub-core/.env
```

**Expected output**: All services start. Report service URLs from the ports table below.

### 2. `down` — Stop the development stack

```bash
docker compose -f docker-compose.dev.yml down
```

### 3. `health` — Check all service health statuses

1. Run `docker compose -f docker-compose.dev.yml ps --format json`
2. For each service, report: name, status, health, exposed ports
3. Test connectivity to key endpoints with `curl -s -o /dev/null -w "%{http_code}"`:
   - API: http://localhost:8000
   - OpenWebUI: http://localhost:8080
   - Langfuse: http://localhost:6006
   - NATS: http://localhost:8222
   - SeaweedFS: http://localhost:8889

### 4. `logs <service>` — Tail logs for a specific service

```bash
docker compose -f docker-compose.dev.yml logs --tail 100 -f <service>
```

### 5. `restart <service>` — Restart a specific service

```bash
docker compose -f docker-compose.dev.yml restart <service>
```

### 6. `status` — Show running containers with resource usage

```bash
docker compose -f docker-compose.dev.yml ps
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### 7. `ports` — Show all exposed service URLs

| Service    | URL                   | Purpose            |
|------------|-----------------------|--------------------|
| API        | http://localhost:8000 | REST API + Swagger |
| OpenWebUI  | http://localhost:8080 | Chat interface     |
| Admin UI   | http://localhost:3000 | Nuxt management UI |
| Langfuse   | http://localhost:6006 | LLM observability  |
| NATS       | http://localhost:8222 | NATS dashboard     |
| SeaweedFS  | http://localhost:8889 | Object storage     |

## Examples

- `/docker-dev up` — Start all services
- `/docker-dev down` — Stop all services
- `/docker-dev health` — Check which services are running and healthy
- `/docker-dev logs aihub-api` — Tail the API service logs
- `/docker-dev restart aihub-api` — Restart just the API service
- `/docker-dev status` — Show containers and resource usage
- `/docker-dev ports` — List all service URLs

## Troubleshooting

- **".env file not found"**: Copy `.env.dev` to `.env` at the repo root.
- **Port already in use**: Another process is using the port. Run `lsof -i :<port>` to find it, then stop or change the port.
- **Service keeps restarting**: Check logs with `/docker-dev logs <service>` for error details.
- **"no matching manifest for linux/arm64"**: Some images may not support ARM. Check the compose file for platform overrides.

## Key Files

- Docker Compose (dev): `/home/user/aihub-core/docker-compose.dev.yml`
- Environment config: `/home/user/aihub-core/.env` (copy from `.env.dev`)
- Compose template: `/home/user/aihub-core/deployment/templates/docker-compose.yml.j2`
