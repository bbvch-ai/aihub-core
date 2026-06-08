<div align="center">

# swiss-ai-hub-bot

**The bot integration SDK for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — bring your agents to users in MS
Teams, Slack, and web chat.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-bot?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-bot/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-bot?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-bot/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/bot/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers — LLM gateway (LiteLLM), vector search (Milvus), data pipelines
(Dagster), SSO (Keycloak), observability (Langfuse), a chat UI (Open-WebUI), and more. You build agents with the Python
SDK; **this package puts them in the chat tools your users already live in.**

## What is this package?

`swiss-ai-hub-bot` is a [Bot Framework](https://dev.botframework.com/) application (built on the `microsoft-agents-*`
SDK) that connects collaboration channels to Swiss AI Hub. It receives messages from **MS Teams, Slack, and web chat**,
handles the channel-specific quirks (threads, mentions, file attachments, markdown, typing indicators, streaming), and
routes each conversation to its destination:

- **`AgentChatBot`** — routes a conversation to a Swiss AI Hub **agent** over NATS, streaming the agent's response back
  into the channel.
- **`OpenaiChatBot`** — talks **directly to an LLM** through the platform's LiteLLM gateway (no agent), for simple
  chat-with-a-model endpoints.
- **Bot-in-the-loop (BITL)** — when an agent needs a human, the bot delivers the question to a Slack/Teams channel and
  feeds the human's reply back into the agent's workflow.

It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/) (installed automatically) and pairs with
[`swiss-ai-hub-agent`](https://pypi.org/project/swiss-ai-hub-agent/) (the agents it surfaces).

## Should you use this package?

**Probably not directly — most deployments use the pre-built Docker image**, which ships the bot ready to go:

```yaml
# docker-compose.yml
services:
  bot:
    image: ghcr.io/bbvch-ai/aihub-core/bot:latest
```

**Use this PyPI package when you want to compose a custom bot** — mount only the handlers you need, add your own channel
handler, or change how conversations are routed. It's an SDK for building a custom chat front-end on top of Swiss AI
Hub, not just a standalone server.

## Installation

```bash
pip install swiss-ai-hub-bot
# or
uv add swiss-ai-hub-bot
```

Requires **Python 3.13**.

______________________________________________________________________

## Quick start

A bot is a `BotRunner` with the channel controllers you mount — the same shape as the production entry point:

```python
# app.py
from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.routes import HealthController
from swiss_ai_hub.bot.routes import AgentChatController, OpenaiChatController, BotInTheLoopController
from swiss_ai_hub.bot.runners import BotRunner

runner = BotRunner()
auth = KeycloakAuthHandler()   # a fail-closed safety net; channel authenticity is verified per-endpoint (see below)

runner.mount(
    HealthController(auth=auth).get_health(),
    AgentChatController(auth=auth).completions_json().completions_stream(),     # chat → agent (NATS)
    OpenaiChatController(auth=auth).json_chat_completion().stream_chat_completion(),  # chat → LLM (direct)
    BotInTheLoopController(auth=auth).bot_in_the_loop_response(),               # human replies → agent
)

app = runner.create_app()
```

Serve it like any ASGI app (the platform ships it on port `8001`):

```bash
uvicorn app:app --host 0.0.0.0 --port 8001
```

This exposes the Bot Framework messaging endpoints — `/api/v1/agent/chat/completions/{agent_class}/{agent_id}/json` (and
`/stream`), the OpenAI-style `/api/v1/openai/chat/completions/json`, and `/api/v1/bot_in_the_loop/response`. Health is
at `/api/v1/health`.

## Connecting a channel

Each bot endpoint is keyed by its **URL path** in MongoDB via a `PathEntity`, which holds that endpoint's Azure Bot
credentials (`APP_ID`, `APP_PASSWORD`, tenant), an optional system message, and a Slack token. To wire up a real
channel:

1. **Register a bot** in Azure Bot Service (the SDK's `setup_azure_bot` helper creates the AD app registration + Bot
   resource and stores the credentials), then add the **Teams** or **Slack** channel in the Azure portal.
2. Point the channel's messaging endpoint at your bot's public URL.
3. The `PathEntity` for that path is seeded automatically by `setup_azure_bot` (or manually via `add_path_entity` for
   local development).

`RoutesService.get_adapter(path)` then loads the credentials, builds a cached Bot Framework adapter per endpoint, and
verifies the authenticity of every incoming activity.

______________________________________________________________________

## Development

The dev stack runs the platform infrastructure (NATS, FerretDB, Valkey, LiteLLM, …) in Docker and exposes it on
`localhost`; the bot runs on your host:

```bash
# 1. Start the platform infrastructure (from a Swiss AI Hub checkout)
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# 2. Load the dev connection settings into your shell
set -a && source .env && set +a

# 3. Run the bot — it connects to NATS + MongoDB and serves on :8001
uvicorn app:app --host 0.0.0.0 --port 8001
```

The bot connects to NATS and MongoDB, subscribes for bot-in-the-loop requests, and is ready to receive activities. Two
ways to drive messages locally:

- **Bot Framework Emulator** — connect it to `http://localhost:8001/api/v1/messages` (leave App ID/Password empty).
- **Real channels** — expose your local bot to the internet with a tunnel (Azure Dev Tunnels, ngrok, …) and set that URL
  as the channel's messaging endpoint, so Teams/Slack can reach it.

> **Settings are not auto-loaded from the environment.** The SDK reads connection settings only when constructed, so
> make sure the variables above are exported in the process that runs the bot (`set -a && source .env && set +a`).

## Production

In production the bot runs as a container behind Traefik (so channels can reach its webhook), reaching other services by
**container hostname**.

**1. Containerize it** — install the SDK from PyPI and serve with Gunicorn + Uvicorn workers:

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./        # your project, depending on swiss-ai-hub-bot
RUN uv sync --frozen --no-dev
COPY . .

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 8001
ENTRYPOINT ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", \
            "--forwarded-allow-ips=*", "-b", "0.0.0.0:8001", "app:app"]
```

**2. Run it alongside the platform on the right networks.** The bot receives channel webhooks (Traefik → **`proxy`**),
routes conversations to agents over NATS and keeps conversation state in MongoDB (**`data`**), and reaches the LLM
gateway (**`backend`**):

```yaml
# docker-compose.my-bot.yml — deployed alongside the platform
services:
  my-bot:
    image: registry.example.com/my-bot:1.0.0
    restart: always
    environment:
      NATS_ENDPOINT: nats://nats:4222
      NATS_TOKEN: ${NATS_TOKEN}
      MONGO_CONNECTION_STRING: mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@ferretdb:27017/
      LITE_LLM_PROXY_BASE_URL: http://litellm:4000
      LITE_LLM_PROXY_API_KEY: ${LITELLM_MASTER_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    labels:                              # expose the messaging endpoint through the platform's Traefik
      - "traefik.enable=true"
      - "traefik.http.services.my-bot.loadbalancer.server.port=8001"
    networks: [proxy, backend, data]

networks:
  proxy: { external: true }
  backend: { external: true }
  data: { external: true }
```

```bash
docker compose -f docker-compose.my-bot.yml up -d
```

Reuse the platform's secrets (from its `.env`) for the `${…}` values, and match the actual network names of your
deployment.

> **Network reference.** `proxy` = external ingress via Traefik (where channel webhooks arrive). `data` = NATS,
> FerretDB. `backend` = LiteLLM. The bot needs no `storage` network.

______________________________________________________________________

## What you get

| Capability             | Detail                                                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Channels**           | MS Teams, Slack, and web chat — with channel-specific thread/mention/file/markdown handling                       |
| **Agent chat**         | `AgentChatBot` routes a conversation to an agent over NATS and streams the reply back                             |
| **Direct LLM**         | `OpenaiChatBot` talks straight to LiteLLM for simple chat-with-a-model endpoints                                  |
| **Streaming**          | Token-by-token updates in the channel (falls back to non-streaming where the channel can't update messages)       |
| **Bot-in-the-loop**    | Delivers an agent's question to a human in Slack/Teams and feeds the reply back into the workflow                 |
| **Conversation state** | Per-endpoint config + conversation history in MongoDB, with a configurable TTL                                    |
| **Testing**            | `BotTestRunner` and `SimulatedAgentBotTestRunner` for capturing outbound activities and faking an agent over NATS |

See the [documentation](https://bbvch-ai.github.io/aihub-core/) for the full handler/streaming/BITL reference.

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/
- **The full SDK** (meta package): https://pypi.org/project/swiss-ai-hub/

## License

Apache-2.0 — see [packages/bot/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/bot/LICENSE). For the
full per-package license matrix, see [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
