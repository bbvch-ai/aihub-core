<div align="center">

# swiss-ai-hub-api

**The REST API, WebSocket gateway, and MCP server for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — the
bridge between clients and the platform, composable from a set of controllers.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-api?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-api/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-api?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-api/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/api/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers — LLM gateway (LiteLLM), vector search (Milvus), data pipelines
(Dagster), SSO (Keycloak), observability (Langfuse), a chat UI (Open-WebUI), and more. Agents, processes, and pipelines
talk to each other over NATS using the Swiss AI Agent Protocol; **this package is how the outside world talks to them.**

## What is this package?

`swiss-ai-hub-api` is a [FastAPI](https://fastapi.tiangolo.com/) application that translates between HTTP/WebSocket and
the platform's internal event protocol. It is assembled from **controllers** (agents, threads, knowledge, models, roles,
…) that you mount on an `ApiRunner`. Its defining feature: it doesn't hardcode agent endpoints — it **discovers online
agents and processes over NATS and registers HTTP + streaming endpoints for them at runtime**.

What you get out of the box:

- **Dynamic agent & process endpoints** — for every online agent, the API auto-registers
  `POST …/agents/classes/<Class>/instances/<id>/UserMessageEvent` (and a `/stream` variant). No code, no redeploy when
  agents come and go.
- **Real-time WebSocket** — clients subscribe to a thread and receive agent display events (chunks, thoughts, LLM
  output) live.
- **OpenAI-compatible endpoints** — `/openai/chat/completions`, `/embeddings`, `/audio/*`, `/images/generations` — point
  any OpenAI client at the platform.
- **MCP server** — `runner.create_app()` also mounts a [Model Context Protocol](https://modelcontextprotocol.io/) server
  at `/mcp`.
- **Management endpoints** — agents, threads, knowledge bases, models, roles, tokens, memory, dashboards — via the
  controllers you choose to mount.

It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/) (installed automatically).

## Should you use this package?

**Probably not directly — most deployments use the pre-built Docker image,** which ships the full API ready to go:

```yaml
# docker-compose.yml
services:
  api:
    image: ghcr.io/bbvch-ai/aihub-core/api:latest
```

**Use this PyPI package when you want to compose your own API** — mount only the controllers you need, add your own
controllers alongside the built-in ones, or embed the gateway inside a larger FastAPI application. It's an SDK for
building a custom backend on top of Swiss AI Hub, not just a standalone server.

## Installation

```bash
pip install swiss-ai-hub-api
# or
uv add swiss-ai-hub-api
```

Requires **Python 3.13**.

______________________________________________________________________

## Quick start

An API is an `ApiRunner` with the controllers you mount. Mount a few — or all of them — and call `create_app()` to get a
standard ASGI app:

```python
# app.py
from swiss_ai_hub.api.runners import ApiRunner
from swiss_ai_hub.api.routes import ApiHealthController, AgentController, ThreadController, EventController
from swiss_ai_hub.core.auth import TokenAndOauth2Handler

runner = ApiRunner()
auth = TokenAndOauth2Handler.from_auth_settings()   # Keycloak/OIDC + static-token auth from env

runner.mount(
    ApiHealthController(auth=auth).get_health().get_ready(),
    AgentController(auth=auth).get_agent_classes().get_agent_class().get_agent_class_instances().create_agent_instance(),
    ThreadController(auth=auth).get_user_threads().create_thread().get_thread(),
    EventController(auth=auth).ws().get_agent_events_in_thread(),  # WebSocket + event history
)

app = runner.create_app()   # ASGI app — also mounts the MCP server at /mcp
```

Serve it like any ASGI app:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API mounts under `/api/v1`. Health is at `/api/v1/health`; the OpenAPI spec and Swagger UI at `/api/v1/openapi.json`
and `/api/v1/docs`. Even with the minimal mount above, the lifetime manager's discovery service registers the dynamic
**agent** endpoints automatically — they appear in the OpenAPI spec the moment an agent is online.

> The full production API mounts ~25 controllers — see
> [`app/main.py`](https://github.com/bbvch-ai/aihub-core/blob/main/packages/api/app/main.py) for the complete list,
> which doubles as the canonical example.

### Talking to an agent

With an agent online and an instance configured, the chat round-trip is a single POST:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/default/agents/classes/LLMWrappingAgent/instances/my-agent/UserMessageEvent \
  -d '{"messages":[{"role":"user","blocks":[{"block_type":"text","text":"Hello!"}]}]}'
```

The API publishes a `StartEvent` to the agent over NATS, the agent runs, and the response streams back (use the
`/stream` variant for token-by-token SSE, or subscribe over the WebSocket for the full event timeline).

______________________________________________________________________

## Development

The dev stack runs the platform infrastructure (NATS, FerretDB, Valkey, Milvus, LiteLLM, …) in Docker and exposes it on
`localhost`, so you run the API directly on your host:

```bash
# 1. Start the platform infrastructure (from a Swiss AI Hub checkout)
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# 2. Load the dev connection settings (localhost endpoints) into your shell
set -a && source .env && set +a

# 3. Run your API — it connects to the dockerized stack and serves on :8000
uvicorn app:app --host 0.0.0.0 --port 8000
```

The API starts, connects to all backing stores, and its discovery service finds any online agents — their endpoints show
up in the served OpenAPI spec, and the admin UI and chat work against your locally-running gateway.

> **Settings are not auto-loaded from the environment.** The SDK reads connection settings only when constructed, so
> make sure the variables above are exported in the process that runs the API (`set -a && source .env && set +a`).

## Production

In production the API runs as a container behind Traefik, reaching other services by **container hostname**.

**1. Containerize it** — install the SDK from PyPI and serve with Gunicorn + Uvicorn workers (how the platform ships
it):

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./        # your project, depending on swiss-ai-hub-api
RUN uv sync --frozen --no-dev
COPY . .

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 8000
ENTRYPOINT ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
            "--forwarded-allow-ips=*", "-b", "0.0.0.0:8000", "app:app"]
```

**2. Run it alongside the platform on the right networks.** The API is the externally-facing gateway, so it joins
**`proxy`** (Traefik ingress) plus the three internal zones **`backend`, `data`, `storage`** to reach LiteLLM, NATS, the
databases, and S3:

```yaml
# docker-compose.my-api.yml — deployed alongside the platform
services:
  my-api:
    image: registry.example.com/my-api:1.0.0
    restart: always
    environment:
      NATS_ENDPOINT: nats://nats:4222
      NATS_TOKEN: ${NATS_TOKEN}
      REDIS_URL: redis://valkey:6379
      REDIS_TOKEN: ${REDIS_TOKEN}
      MONGO_CONNECTION_STRING: mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@ferretdb:27017/
      MILVUS_URL: http://milvus-standalone:19530
      S3_STORAGE_ENDPOINT: http://seaweedfs-s3:9000
      LITE_LLM_PROXY_BASE_URL: http://litellm:4000
      LITE_LLM_PROXY_API_KEY: ${LITELLM_MASTER_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:                              # expose through the platform's Traefik (optional)
      - "traefik.enable=true"
      - "traefik.http.services.my-api.loadbalancer.server.port=8000"
    networks: [proxy, backend, data, storage]

networks:
  proxy: { external: true }
  backend: { external: true }
  data: { external: true }
  storage: { external: true }
```

```bash
docker compose -f docker-compose.my-api.yml up -d
```

Reuse the platform's secrets (from its `.env`) for the `${…}` values, and match the actual network names of your
deployment. Drop the `proxy` network and Traefik labels if you front the API with your own ingress instead.

> **Network reference.** `proxy` = external ingress via Traefik. `data` = NATS, Valkey, FerretDB, Milvus, Neo4j.
> `backend` = LiteLLM, OTEL collector. `storage` = SeaweedFS/S3.

______________________________________________________________________

## Building your own endpoints

Endpoints follow a **Controller → Service → DTO → Entity** separation:

- **Controller** — extends `Controller` (global) or `TenantScopedController` (mounted under `/api/v1/{tenant_id}/`).
  Defines `name`/`description`/`icon` class attributes and exposes each route through a fluent method that returns
  `self`. Auth, permission checks (`user_with_permission("aihub.user.<resource>.{path_param}")`), OpenTelemetry spans,
  and tenant scoping all come from the base class.
- **Service** — stateless `@staticmethod` business logic; calls entities for persistence.
- **DTO** — Pydantic v2 models with `from_entity()` factories and `in_locale(t)` localization.

You then mount it next to the built-ins, exactly like the production `app/main.py`:

```python
runner.mount(MyController(auth=auth).list_items().create_item().delete_item())
```

[`AgentController`](https://github.com/bbvch-ai/aihub-core/blob/main/packages/api/swiss_ai_hub/api/routes/agent/agent_controller.py)
is the canonical reference, and the [documentation](https://bbvch-ai.github.io/aihub-core/) walks through the full
new-endpoint workflow (DTOs → service → controller → mount). Every controller's HTTP dependencies (NATS client, S3,
Milvus, the event distributors, the WebSocket manager) are injected via FastAPI `Depends`/`Security`.

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/
- **The full SDK** (meta package): https://pypi.org/project/swiss-ai-hub/

## License

Apache-2.0 — see [packages/api/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/api/LICENSE). For the
full per-package license matrix, see [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
