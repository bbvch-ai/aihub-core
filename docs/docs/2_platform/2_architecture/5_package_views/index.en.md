---
title: Package-Centered Views
description: Developer-onboarding architecture views — one per first-party package, with plain-language explanation of what it does and the L2 surface it touches.
---

# Package-Centered Views

This page is the starting point for a developer about to work **inside** a Swiss AI Hub package. For each first-party
package it pairs two things:

1. **Plain-language prose** — what the package does, why it exists, the problem it solves, and what it contains.
2. **A centered architecture diagram** — the package in the middle, with every L2 container and external system it talks
   to (inbound *and* outbound). It answers: *"If I touch this package, what else will I be interacting with?"*

These views are deliberately separate from the [Code Deep Dive](../../../6_code_deep_dive/) section, which mirrors each
package's `README.md` — the end-user document that also appears on PyPI and npm. That audience installs the package;
this audience builds it. For the layered platform story (what lives in the Data tier, the LLM tier, and so on) see
[Containers](../2_containers/).

## API Gateway

**`packages/api`** is the bridge between the outside world and the platform. Everything a client does — a browser
loading the Admin UI, OpenWebUI streaming a chat, a script calling REST — enters the platform through here. Inside the
platform, agents, processes, and pipelines speak to each other over NATS using the Swiss AI Agent Protocol; the API
translates that event-driven world into the request/response and WebSocket idioms that HTTP clients expect.

**Why it exists.** The platform's internal communication is asynchronous and event-sourced, which is powerful for agents
but awkward for a frontend. The API absorbs that mismatch: it publishes Control Events, subscribes to the resulting
Display Events, and streams them back over a WebSocket so the UI can render an agent's reasoning live. It also owns the
relational concerns that don't belong in any single agent — tenants, users, roles, knowledge-base metadata.

**What it contains.** A set of composable FastAPI controllers following a strict Controller → Service → Entity layering,
plus an embedded **Process Engine** (`packages/process` runs in-process here, not as its own container), a dynamic
endpoint-discovery mechanism that surfaces online agents as REST routes, and the WebSocket display-event sender.

Because the API is the most-connected first-party container, its view is split into outbound and inbound for legibility.

### Outbound — what the API calls

<likec4-view view-id="centered_api_outbound" style="display:block;height:560px"></likec4-view>

### Inbound — who calls the API

<likec4-view view-id="centered_api_inbound" style="display:block;height:480px"></likec4-view>

## Sysadmin API

**`packages/sysadmin-api`** is the system-administration plane — the endpoints that operate *above* any single tenant:
creating and deleting tenants, assigning platform-level roles, and other `AIHubSysAdmin`-gated operations. It runs as
its own FastAPI service on `sysadmin.${DOMAIN}/api/v1/*`.

**Why it's a separate package.** The main API ships under Apache-2.0; the sysadmin plane ships under AGPL-3.0-or-later
(network-copyleft). Keeping it a physically separate, separately-licensed artifact prevents AGPL terms from leaking onto
the Apache-2.0 code. It also enforces a hard security boundary — every endpoint requires the `AIHubSysAdmin` realm role.

**What it contains.** Its own `TenantAdminController` (tenant lifecycle), plus a curated set of controllers *re-mounted*
from `packages/api` (user, role, account, auth-provider) so the Sysadmin UI's inherited composables resolve same-origin.
Code ownership stays in `packages/api`; this package only picks the surface it needs and gates it.

<likec4-view view-id="centered_sysadmin_api" style="display:block;height:480px"></likec4-view>

## Admin UI

**`packages/web`** is the admin and management interface — where administrators configure agents, manage knowledge
bases, monitor processes, inspect conversation threads, assign roles, and track costs. It is a Nuxt 3 SPA published as a
reusable Nuxt layer.

**Why it exists.** The platform exposes a large, evolving surface; OpenWebUI covers end-user chat, but configuring and
operating the platform needs a purpose-built management console. The UI consumes the API entirely through a generated
TypeScript SDK, so backend contract changes surface as type errors at build time rather than runtime surprises.

**What it contains.** Domain-scoped pages (agents, processes, threads, knowledge, models, roles, users, costs,
evaluations), Pinia-Colada query/mutation composables, a WebSocket bridge that streams agent display events straight
into the cache, an event-display component system that renders each agent event type, and a PrimeVue + Tailwind design
system.

<likec4-view view-id="centered_web" style="display:block;height:480px"></likec4-view>

## Sysadmin UI

**`packages/sysadmin-web`** is the system-administration console — today, the multi-tenant management UI. It is a Nuxt 3
Layer that *extends* `@swiss-ai-hub/web`, reusing its components, composables, and design system while adding
sysadmin-only pages. It is hosted at `sysadmin.${DOMAIN}/*`.

**Why it's a separate package.** Same reasoning as the Sysadmin API: it is a separate deploy artifact with its own
security boundary on the `sysadmin.${DOMAIN}` subdomain. Both `packages/web` and the sysadmin plane ship under
AGPL-3.0-or-later, so the separation is architectural rather than a licensing boundary. The Nuxt Layer mechanism lets it
inherit nearly everything from the open-source UI without copying code.

**What it contains.** Tenant CRUD pages and the sysadmin route guard, layered on top of the inherited Admin UI. Its SDK
and most API calls resolve same-origin against the Sysadmin API; the only cross-origin call is the role check that
bounces a non-sysadmin user back to the main app.

<likec4-view view-id="centered_sysadmin_web" style="display:block;height:480px"></likec4-view>

## Agent Runtime

**`packages/agent`** is the SDK for building agents — the transparent, workflow-based AI workers that are the reason the
platform exists. An agent is a small, stateless Python class: you declare a few `@step` methods and the events that
trigger them, and the runtime handles the rest.

**Why it exists.** Most agent frameworks are opaque — a prompt goes in, an answer comes out, and the reasoning is a
black box. Swiss AI Hub agents are auditable by construction: every step is an event on NATS JetStream, so a run can be
replayed, traced, and inspected. The runtime makes agents horizontally scalable and independently deployable — each
agent class runs as its own container, subscribing to its own subjects.

**What it contains.** The dispatcher that replays event history to decide which steps to run, the `@step` decorator and
step registry, a dependency injector that resolves step parameters by type, the precondition evaluator, and the durable
`RunContext` / `ThreadContext` state stores (in Valkey). At runtime an agent reaches RAG (Milvus), memory (Neo4j), the
LLM gateway (LiteLLM), and any external MCP tools it's configured with.

<likec4-view view-id="centered_agent" style="display:block;height:560px"></likec4-view>

## Pipeline Orchestrator

**`packages/pipeline`** is the data-ingestion SDK — it turns an organization's documents into the RAG-ready vectors that
agents search. If the Agent Runtime is how the platform *answers* questions, the pipeline is how the knowledge to answer
them *gets in*.

**Why it exists.** Useful enterprise agents need organizational context, and that context lives in scattered, messy
document stores — SharePoint, OneDrive, S3, network drives. Getting it into a vector store is a multi-stage problem:
discover changes, download, parse (OCR, layout extraction), chunk semantically, embed, and index — with lineage from
every vector back to its source. The pipeline models this as a Dagster asset graph, so every stage is observable and
re-runnable.

**What it contains.** A two-stage factory pattern: source connectors (Rclone for 70+ backends, plus direct MS Graph for
SharePoint) feed a unified processing graph (MinerU for parsing, LiteLLM for embeddings, Milvus for storage). It emits
`SourceUpdatedEvent` to NATS on ingest and posts failure alerts to notification targets via Apprise.

<likec4-view view-id="centered_pipeline" style="display:block;height:560px"></likec4-view>

## Bot Service

**`packages/bot`** brings agents to users where they already work — Microsoft Teams, Slack, and web chat — instead of
requiring them to visit a dedicated UI. It is built on the `microsoft-agents-*` SDK (the successor to the Microsoft Bot
Framework).

**Why it exists.** Adoption friction is real: a dedicated AI interface is one more tool to switch to. Meeting users
inside their existing collaboration platform removes that friction. The bot also supports *bot-in-the-loop* (BITL) — an
agent mid-workflow can ask the user a clarifying question directly in their Slack thread and resume when they answer.

**What it contains.** A `BaseChatBot` + `CompletionHandler` strategy pattern that keeps channel-specific logic (Slack,
Teams, Webex, email) separate from conversation logic, NATS bridges for agent chat and BITL, per-message identity
resolution against Keycloak, and a direct LiteLLM path for simple non-agent completions. Conversation state is held in
FerretDB with a TTL.

<likec4-view view-id="centered_bot" style="display:block;height:560px"></likec4-view>

## Backup Service

**`packages/backup`** is the platform's backup, restore, and PostgreSQL-maintenance plane — a self-contained Dagster
instance (independent of the ingestion pipeline) that snapshots every stateful store to S3.

**Why it exists.** The platform spreads state across seven very different stores — PostgreSQL, FerretDB, Milvus, Neo4j,
ClickHouse, Valkey, and NATS JetStream — each with its own backup mechanism. A single, scheduled, auditable service that
knows how to snapshot and restore each one is far safer than ad-hoc per-store scripts. Running it as its own Dagster
instance keeps backup scheduling independent of pipeline workloads.

**What it contains.** Three parallel asset graphs (backup, restore, maintenance), one handler per stateful store, an S3
manager for writing artifacts to SeaweedFS, and container-discovery logic. It talks to the Docker socket *directly* (not
through the OIDC-tier socket proxy, which is Traefik-only) to quiesce and control containers during backup. It
deliberately excludes etcd, which is treated as ephemeral.

<likec4-view view-id="centered_backup" style="display:block;height:560px"></likec4-view>

## OpenWebUI

**OpenWebUI** is the open-source chat interface — the primary end-user surface for conversational interaction with
agents. It is a third-party application we ship and integrate, not a package we author, but its integration is deep
enough to warrant its own onboarding view.

**Why it matters architecturally.** OpenWebUI is where most users actually talk to the platform, and its connection to
our API is more than a simple OpenAI-compatible endpoint. A **custom `aihub-pipeline`** (a Python function mounted into
OpenWebUI) bridges chat to the Swiss AI Agent Protocol over SSE — preserving rich agent events (reasoning, tool calls,
retrieval, human-in-the-loop) as structured UI blocks rather than flat token streams.

**What to know.** The custom pipeline path is distinct from the OpenAI-compatible fallback, which OpenWebUI uses for
non-agent tasks (image generation, speech, embeddings, document parsing — all proxied through our API). OpenWebUI also
calls Milvus directly for its own built-in RAG feature, stores state in PostgreSQL, files in SeaweedFS, and
authenticates via Keycloak. The API, in turn, provisions agent models and access into OpenWebUI via SCIM.

<likec4-view view-id="centered_openwebui" style="display:block;height:560px"></likec4-view>
