<div align="center">

# swiss-ai-hub-agent

**The agent SDK for [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) — build transparent, workflow-based AI agents
that run as independent, event-driven services.**

[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-agent?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-agent/)
[![Python](https://img.shields.io/pypi/pyversions/swiss-ai-hub-agent?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/swiss-ai-hub-agent/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/packages/agent/LICENSE)

</div>

______________________________________________________________________

## What is Swiss AI Hub?

[Swiss AI Hub](https://github.com/bbvch-ai/aihub-core) is an open-source, self-hosted AI platform for enterprises. One
`docker compose up` starts ~30 integrated containers — LLM gateway (LiteLLM), vector search (Milvus), data pipelines
(Dagster), SSO (Keycloak), observability (Langfuse), a chat UI (Open-WebUI), and more. The platform handles auth,
multi-tenancy, cost control, LLM routing, and vector storage. **You build the agents.**

## What is this package?

`swiss-ai-hub-agent` is the SDK for writing those agents. An agent is a small, stateless Python class: you define a few
**steps**, each consuming and producing typed **events**, and the SDK runs them as an independent service that talks to
the rest of the platform over NATS. You don't write any networking, persistence, or API glue — you describe the
workflow, and the platform provides the runtime:

- **Workflow as typed steps** — a step's inputs and outputs are inferred from its type annotations. The engine routes
  events between steps for you.
- **Transparent & traceable** — every step and LLM call emits display events, so the whole reasoning process is visible
  in the admin UI and traced in Langfuse.
- **Stateless & horizontally scalable** — no in-memory state; everything lives in Valkey (`RunContext`/`ThreadContext`)
  and the JetStream event history, so you can run many replicas behind a NATS queue group.
- **Auto-discovered** — when your agent comes online it announces itself; the API exposes HTTP/WebSocket endpoints for
  it and it appears in the admin UI and chat — no registration code.

It builds on [`swiss-ai-hub-core`](https://pypi.org/project/swiss-ai-hub-core/) (installed automatically). To expose
agents over REST/WebSocket use [`swiss-ai-hub-api`](https://pypi.org/project/swiss-ai-hub-api/); to reach them from
Teams/Slack use [`swiss-ai-hub-bot`](https://pypi.org/project/swiss-ai-hub-bot/).

## Installation

```bash
pip install swiss-ai-hub-agent
# or
uv add swiss-ai-hub-agent
```

Requires **Python 3.13**.

______________________________________________________________________

## Quick start

### Run a pre-built agent

The SDK ships ready-made agents. Here's the simplest — an LLM chat passthrough — running as a service in five lines:

```python
import asyncio
from swiss_ai_hub.agent.agents.llm_wrapping_agent import LLMWrappingAgent, LLMWrappingAgentConfig
from swiss_ai_hub.agent.runners import AgentRunner

async def main():
    runner = AgentRunner(agent_type=LLMWrappingAgent, agent_config=LLMWrappingAgentConfig.as_form())
    await runner.run_forever()

asyncio.run(main())
```

With the platform running (see [Development](#development) below), this connects to NATS, comes online, and is
discovered by the API — you can immediately chat with it from the admin UI or Open-WebUI.

### Build your own agent

An agent is an `Agent` subclass with `@step` methods. Each step declares what event it consumes (parameter type) and
what it produces (return type); the engine wires them together. This echo agent answers any chat message:

```python
from typing import ClassVar
from swiss_ai_hub.agent import Agent, AgentLocaleString, step
from swiss_ai_hub.core.events.agent import UserMessageEvent, StopEvent
from swiss_ai_hub.core.displayers import EventDisplayer

class EchoAgent(Agent):
    name: ClassVar[AgentLocaleString] = AgentLocaleString(en="Echo Agent")
    description: ClassVar[AgentLocaleString] = AgentLocaleString(en="Repeats the user's message back.")
    icon: ClassVar[str] = "mage:message"

    @step()
    async def echo(self, event: UserMessageEvent, displayer: EventDisplayer) -> StopEvent:
        last_message = event.messages[-1].content if event.messages else ""
        await displayer.display_chunk(f"You said: {last_message}")   # streamed to the UI in real time
        return StopEvent()                                           # terminates the run
```

Accepting `UserMessageEvent` as the entry event makes the agent **conversational**. The `displayer` parameter is
injected by the engine — declare what you need (an `AgentConfig`, `RunContext`, `AgentMemory`, an injected event, …) and
the dispatcher provides it. Run it the same way:

```python
import asyncio
from swiss_ai_hub.agent import AgentRunner
from swiss_ai_hub.core.agents import AgentConfig

asyncio.run(AgentRunner(agent_type=EchoAgent, agent_config=AgentConfig.as_form()).run_forever())
```

A real agent splits its work into several steps and produces richer output — see the
[`minimal_workflow` examples](https://github.com/bbvch-ai/aihub-core/tree/main/packages/agent/playground/minimal_workflow)
(20 self-contained patterns) and the
[`LLMWrappingAgent` source](https://github.com/bbvch-ai/aihub-core/tree/main/packages/agent/swiss_ai_hub/agent/agents/llm_wrapping_agent)
for a complete, production-shaped agent.

______________________________________________________________________

## Configuration (blueprint vs profile)

Swiss AI Hub separates **what an agent can do** (your class — the *blueprint*) from **how it's configured** (a *profile*
created in the admin UI). You expose configurable settings by subclassing `AgentConfig`, whose fields use the **Form
duality** pattern — one model that both renders as a UI form and validates as data:

```python
from typing import Annotated, Self
from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form.elements import Textarea
from swiss_ai_hub.core.i18n import LocaleString

class EchoAgentConfig(AgentConfig):
    greeting: Annotated[str | Textarea, Field(description="Prefix for the echo")] = "You said:"

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(**base.model_dump(), greeting=Textarea(label=LocaleString(en="Greeting")))
```

Pass `EchoAgentConfig.as_form()` to the runner, and add `agent_config: EchoAgentConfig` as a step parameter to receive
the merged, per-profile values at runtime. Operators then create one or more configured profiles of your agent in the
admin UI (e.g. `echo-hr`, `echo-legal`) without touching code.

______________________________________________________________________

## Development

The dev stack runs the platform infrastructure (NATS, FerretDB, Valkey, Milvus, LiteLLM, …) in Docker and exposes it on
`localhost`, so you run your agent directly on your host and iterate fast:

```bash
# 1. Start the platform infrastructure (from a Swiss AI Hub checkout)
docker compose --env-file .env -f infra/docker-compose.dev.yml up -d

# 2. Point your agent at the stack. The dev .env uses localhost endpoints:
#    NATS_ENDPOINT=nats://localhost:4222   REDIS_URL=redis://localhost:6379
#    MONGO_CONNECTION_STRING=mongodb://…@localhost:27017/   LITE_LLM_PROXY_BASE_URL=http://localhost:4000
set -a && source .env && set +a

# 3. Run your agent — it connects to the dockerized stack over localhost
python my_agent.py
```

Your agent comes online, registers on NATS, and is discovered by the running API — its endpoints appear in the OpenAPI
spec, it shows up in the admin UI, and it's chat-ready in Open-WebUI. It also serves a health endpoint on **`:8090`**
(`AGENT_HEALTH_PORT`). Edit, restart, repeat — no redeploy.

> **Settings are not auto-loaded from the environment.** The SDK reads connection settings only when constructed, so
> make sure the variables above are exported in the process that runs your agent (`set -a && source .env && set +a`).

## Production

In production the platform runs as Docker images on internal networks, where services reach each other by **container
hostname** (not localhost). Two steps:

**1. Containerize your agent** — install the SDK from PyPI:

```dockerfile
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./        # your project, depending on swiss-ai-hub-agent
RUN uv sync --frozen --no-dev
COPY . .

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
EXPOSE 8090                            # health endpoint
ENTRYPOINT ["python", "my_agent.py"]
```

**2. Run it alongside the platform on the right networks.** Swiss AI Hub isolates services into five network zones
(`proxy`, `backend`, `data`, `storage`, `egress`). An agent reaches NATS + Valkey + FerretDB + Milvus + LiteLLM by
joining **`data`, `backend`, and `storage`**. Deploy it with a small compose file that joins those existing networks and
points at the **internal** endpoints:

```yaml
# docker-compose.my-agent.yml — deployed alongside the platform
services:
  my-agent:
    image: registry.example.com/my-agent:1.0.0
    restart: always
    environment:
      NATS_ENDPOINT: nats://nats:4222
      NATS_TOKEN: ${NATS_TOKEN}
      REDIS_URL: redis://valkey:6379
      REDIS_TOKEN: ${REDIS_TOKEN}
      MONGO_CONNECTION_STRING: mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@ferretdb:27017/
      MILVUS_URL: http://milvus-standalone:19530
      LITE_LLM_PROXY_BASE_URL: http://litellm:4000
      LITE_LLM_PROXY_API_KEY: ${LITELLM_MASTER_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks: [data, backend, storage]

networks:
  data: { external: true }
  backend: { external: true }
  storage: { external: true }
```

```bash
docker compose -f docker-compose.my-agent.yml up -d
# …or merge into one deployment:
# docker compose -f infra/docker-compose.latest.yml -f docker-compose.my-agent.yml up -d
```

The agent lands on the platform's networks, reaches every backing store by hostname, and is auto-discovered by the API —
just like a first-party agent. Reuse the platform's secrets (from its `.env`) for the `${…}` values, and match the
actual network names of your deployment.

> **Network reference.** `data` = NATS, Valkey, FerretDB, Milvus, Neo4j. `backend` = LiteLLM, OTEL collector, app
> services. `storage` = SeaweedFS/S3. In production these three are `internal` (no outbound internet); if your agent
> needs the public internet, also join `egress`.

______________________________________________________________________

## Pre-built agents

Import any of these from `swiss_ai_hub.agent.agents.<name>` and run them as-is, or read them as references:

| Agent                     | Purpose                                                             |
| ------------------------- | ------------------------------------------------------------------- |
| `LLMWrappingAgent`        | Simple LLM chat passthrough (minimal 2-step workflow)               |
| `RAGAgent`                | Knowledge QA — multi-source retrieval + reranking + user/org memory |
| `RetrievalAgent`          | Pure document retrieval, no LLM — returns structured context        |
| `FewShotAgent`            | Pattern-matching with few-shot examples + a suitability guard       |
| `ExpertAskingAgent`       | Human-expert escalation via Teams/Slack (bot-in-the-loop)           |
| `ExpertRAGAgent`          | RAG with human-expert fallback (HITL + agent-in-the-loop)           |
| `NamespaceSelectionAgent` | LLM-driven knowledge routing with HITL approval                     |

## Key building blocks

| Concept                        | What it is                                                                                                                                                                       |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@step`                        | Marks a method as a workflow step; inputs/outputs inferred from type hints. Options: `precondition`, `max_executions_per_run`, `stop_on_error`                                   |
| Events                         | Typed messages between steps — `UserMessageEvent`, `StartEvent`, `StopEvent`, your own `ControlEvent` subclasses, plus `DisplayEvent`s for UI                                    |
| Dependency injection           | Declare a step parameter and the dispatcher provides it: an `AgentConfig`, `RunContext`, `ThreadContext`, `EventDisplayer`, `AgentMemory`, a `LocaleHandler`, or any prior event |
| `RunContext` / `ThreadContext` | Per-run and per-thread state in Valkey (the only place to keep state — steps are stateless)                                                                                      |
| `EventDisplayer`               | Streams chunks, thoughts, and LLM output to the UI in real time                                                                                                                  |
| `AgentRunner`                  | Connects your agent to the platform and runs it; `AgentTestRunner` runs it sandboxed for tests                                                                                   |

See the [documentation](https://bbvch-ai.github.io/aihub-core/) for the full guide, and
[`playground/minimal_workflow`](https://github.com/bbvch-ai/aihub-core/tree/main/packages/agent/playground/minimal_workflow)
for runnable patterns (conditionals, loops, human-in-the-loop, fan-out, memory, MCP tools, …).

## Links

- **Source & issues**: https://github.com/bbvch-ai/aihub-core
- **Documentation**: https://bbvch-ai.github.io/aihub-core/
- **The full SDK** (meta package): https://pypi.org/project/swiss-ai-hub/

## License

Apache-2.0 — see [packages/agent/LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/packages/agent/LICENSE). For
the full per-package license matrix, see [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md).

______________________________________________________________________

<div align="center">

Part of [Swiss AI Hub](https://github.com/bbvch-ai/aihub-core). Built in Switzerland by
[bbv Software Services](https://www.bbv.ch).

</div>
