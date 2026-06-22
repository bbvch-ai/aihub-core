<div align="center">

<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/logo.png" alt="Swiss AI-Hub" width="120">

# Swiss AI-Hub

**The open-source AI infrastructure stack for Swiss enterprises.**

Connect, orchestrate, and monitor best-in-class open-source tools to deliver\
what cloud AI platforms promise, but where you own every layer.

[![GitHub Release](https://img.shields.io/github/v/release/bbvch-ai/aihub-core?style=flat-square)](https://github.com/bbvch-ai/aihub-core/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0%20%2F%20AGPL-blue?style=flat-square)](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyPI](https://img.shields.io/pypi/v/swiss-ai-hub-core?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/swiss-ai-hub-core/)
[![npm](https://img.shields.io/npm/v/@swiss-ai-hub/web?style=flat-square&logo=npm&logoColor=white)](https://www.npmjs.com/package/@swiss-ai-hub/web)

[Get started](#quick-start) · [Documentation](https://bbvch-ai.github.io/aihub-core/) ·
[Discord](https://discord.gg/wArT8zDB) · [Releases](https://github.com/bbvch-ai/aihub-core/releases)

</div>

______________________________________________________________________

## Why this exists

Over the past years we have met dozens of Swiss companies building remarkably similar stacks: a vector database here, an
ingestion pipeline there, an LLM gateway, some kind of chat UI. Small teams doing impressive work, and consistently
underestimating the day-two problems. Authentication across services. Cost tracking per department. PII filtering before
data crosses a border. Observability that connects a user's question to the exact document chunk that answered it.
Secret rotation. Upgrading 30 interdependent containers without downtime. The prototype is 10 % of the work; running it
in production, securely, at scale, is the other 90 %.

A Swiss KMU with 100 employees should not be building and maintaining its own AI infrastructure, just as it would not
write its own database or email server.

**Our thesis:** the best AI platform is one you do not build from scratch. Open-WebUI ships a better chat interface than
we could build, and it improves every week. Milvus handles vector search at scale. Dagster solved pipeline orchestration
and data lineage. Rclone connects 70+ cloud storage providers. Keycloak handles every SSO scenario. LiteLLM unifies
every LLM provider behind one API. Langfuse gives observability that most platforms charge a premium for. When these
projects ship new features, you get them. No vendor approval, no license upgrade.

**Our job is to make them work together.** We wire these tools into an opinionated, production-ready stack (integrated
auth, unified observability, secure networking, cost tracking, and a shared event protocol) then give you SDKs to extend
it, because every out-of-the-box platform eventually limits you.

> [!IMPORTANT]\
> **Why this matters in Switzerland.** Professionals bound by Art. 321 StGB and organizations subject to the nDSG cannot
> send client data to US-headquartered cloud providers without confronting the CLOUD Act. "Region Switzerland" hosting
> from hyperscalers does not resolve this; operational access often originates outside Switzerland. Swiss AI-Hub
> eliminates the risk: deploy on your own servers, run local models, keep every byte under Swiss jurisdiction.

**Where competition belongs:** your domain expertise, your specialized agents, your proprietary data. Not authentication
systems or vector databases. The platform handles the commodity layer so you can focus on what differentiates you.

______________________________________________________________________

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash
cd swiss-ai-hub
# Edit .env: set DOMAIN, OAuth credentials, and LLM provider keys
docker compose up -d
```

The installer downloads the latest release, auto-detects GPU hardware, extracts the bundle, and generates all secrets.
On a GPU machine this starts ~35 containers including local inference (vLLM, Whisper, MinerU). Without a GPU it routes
inference to Swiss LLM Cloud or any OpenAI-compatible endpoint.

______________________________________________________________________

## What you get

### Infrastructure stack

One `docker compose up` starts ~30 containers, fully integrated. Every component below is included, configured, and
wired together.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/architecture/low_level/tier_2.png" width="100%" alt="Architecture overview">
<em>Tier 2 architecture: every component connected, from LLM providers to data sources</em><br><br>
</p>

<details>
<summary><strong>LLM gateway & inference</strong></summary>

| Component                                     | Powered by                                          | Role                                                                                                                                         |
| --------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| LLM proxy                                     | [LiteLLM](https://github.com/BerriAI/litellm)       | Unified OpenAI-compatible gateway routing to any provider (local vLLM, Swiss LLM Cloud, Azure OpenAI) with per-user/team/model cost tracking |
| Local inference (chat, embeddings, reranking) | [vLLM](https://github.com/vllm-project/vllm)        | High-throughput OpenAI-compatible server running chat, embedding, and reranker models on GPU. No data leaves the network                     |
| Speech-to-text & text-to-speech               | [Speaches](https://github.com/speaches-ai/speaches) | OpenAI-compatible audio server (Faster Whisper STT, Piper/Kokoro TTS) enabling voice I/O without cloud APIs                                  |

</details>

<details>
<summary><strong>Agent memory</strong></summary>

| Component        | Powered by                                                           | Role                                                                                                                         |
| ---------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Long-term memory | [Mem0](https://github.com/mem0ai/mem0) + [Neo4j](https://neo4j.com/) | Extracts and retrieves facts across sessions; Neo4j graph backend captures entity relationships (people, projects, concepts) |

</details>

<details>
<summary><strong>Document processing</strong></summary>

| Component               | Powered by                                            | Role                                                                                                    |
| ----------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| PDF & image parsing     | [MinerU](https://github.com/opendatalab/MinerU)       | Converts complex PDFs into clean markdown: tables, formulas, multi-column layouts, OCR in 109 languages |
| Office document parsing | [MarkItDown](https://github.com/microsoft/markitdown) | Converts DOCX, PPTX, XLSX, and Outlook messages into markdown with embedded image extraction            |

</details>

<details>
<summary><strong>Data pipelines</strong></summary>

| Component              | Powered by                                       | Role                                                                                                                    |
| ---------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Pipeline orchestration | [Dagster](https://github.com/dagster-io/dagster) | Asset-based orchestration with scheduling, lineage from source document to vector embedding, and monitoring UI          |
| Cloud storage sync     | [Rclone](https://rclone.org/)                    | Pulls documents from 70+ backends (SharePoint, OneDrive, Google Drive, S3, Azure Blob, SFTP, Dropbox) into the pipeline |

</details>

<details>
<summary><strong>Vector & semantic search</strong></summary>

| Component       | Powered by                                                                                 | Role                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Vector database | [Milvus](https://github.com/milvus-io/milvus) + [Attu](https://github.com/zilliztech/attu) | Stores embeddings, serves low-latency ANN queries for RAG; Attu provides a web UI for inspection and debugging |

</details>

<details>
<summary><strong>Databases & storage</strong></summary>

| Component           | Powered by                                                                                   | Role                                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Relational database | [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) | Four instances (OpenWebUI, Langfuse, Dagster, LiteLLM) with vector extension for hybrid relational + similarity queries       |
| Document database   | [FerretDB](https://www.ferretdb.com/)                                                        | MongoDB-compatible API over PostgreSQL. Stores conversations, agent configs, and app data without a separate Mongo deployment |
| Object storage      | [SeaweedFS](https://github.com/seaweedfs/seaweedfs)                                          | S3-compatible distributed filesystem for documents, pipeline artifacts, and parsed outputs                                    |
| Metadata consensus  | [etcd](https://etcd.io/)                                                                     | Distributed KV store backing Milvus collection metadata and SeaweedFS filer metadata                                          |

</details>

<details>
<summary><strong>Caching & messaging</strong></summary>

| Component       | Powered by                   | Role                                                                                                                              |
| --------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Message broker  | [NATS](https://nats.io/)     | Central event bus with JetStream persistence for agent workflow events, process orchestration, discovery, and real-time streaming |
| Ephemeral cache | [Valkey](https://valkey.io/) | Redis-compatible in-memory store for transient agent state and workflow step tracking                                             |

</details>

<details>
<summary><strong>Observability & tracing</strong></summary>

| Component           | Powered by                                                                                                          | Role                                                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| AI observability    | [Langfuse](https://github.com/langfuse/langfuse) + [ClickHouse](https://clickhouse.com/)                            | Full prompt/response capture, per-trace cost tracking, RAG analysis, evaluation datasets; ClickHouse powers sub-second analytics |
| Distributed tracing | [OpenTelemetry](https://opentelemetry.io/) + [Collector](https://github.com/open-telemetry/opentelemetry-collector) | Propagates trace context across all services; forwards traces to Langfuse and optionally to external backends                    |

</details>

<details>
<summary><strong>Security & networking</strong></summary>

| Component                     | Powered by                                                | Role                                                                                                          |
| ----------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| SSO & identity                | [Keycloak](https://www.keycloak.org/) / any OIDC provider | Single sign-on via OpenID Connect supporting Azure AD, Google, Okta, or any compliant IdP                     |
| PII detection & anonymization | [Presidio](https://github.com/microsoft/presidio)         | Scans and redacts PII (emails, phone numbers, passports, credit cards) before text reaches external providers |
| Reverse proxy                 | [Traefik](https://traefik.io/)                            | TLS termination, automatic Let's Encrypt, route prioritization, security headers                              |
| Connection pooling            | [PgBouncer](https://www.pgbouncer.org/)                   | Multiplexes PostgreSQL connections across all services to prevent connection exhaustion                       |

</details>

<details>
<summary><strong>Integrations & utilities</strong></summary>

| Component               | Powered by                                                             | Role                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| MS Teams & Slack bots   | [Microsoft Agents SDK](https://github.com/microsoft/Agents-for-python) | Connects agents to Teams, Slack, and web chat channels                                                                 |
| Code execution sandbox  | [Open Terminal](https://github.com/open-webui/open-terminal)           | Sandboxed Python runtime for OpenWebUI code execution (plain LLM models); per-user isolation, downloadable file output |
| Code execution (legacy) | [Jupyter](https://jupyter.org/)                                        | Retained in the stack but no longer used by OpenWebUI for code execution                                               |
| Browser automation      | [Playwright](https://playwright.dev/)                                  | Headless browser for agent web search and page parsing                                                                 |
| Docker socket proxy     | [Tecnativa](https://github.com/Tecnativa/docker-socket-proxy)          | Read-only Docker API access for Traefik, preventing container escape                                                   |

</details>

### SDKs

Every turnkey platform eventually limits you. Swiss AI-Hub ships SDKs so you are never blocked:

| SDK              | Purpose                                                                                                                                               |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent SDK**    | Build custom agents with decorated workflow steps, dependency injection, and automatic platform integration (streaming, tracing, auth, cost tracking) |
| **Pipeline SDK** | Create Dagster data pipelines with source templates for any Rclone-supported provider                                                                 |
| **Process SDK**  | Orchestrate multi-step workflows across agents, humans, and external systems                                                                          |

Your code inherits SSO, observability, the chat UI, admin dashboards, cost tracking, and the event protocol. No REST
endpoints to build, no WebSocket plumbing, no auth logic to write.

______________________________________________________________________

## Platform tour

Five demos showing the platform end-to-end: from ingesting documents to chatting with an agent to controlling costs.
Each runs out of the box after `docker compose up`.

### Upload documents to the knowledge base

Drag files into the admin UI. The platform parses, chunks, embeds, and indexes them automatically. Supports PDF, DOCX,
PPTX, XLSX, and plain text. For production, connect SharePoint, OneDrive, Google Drive, or any of 70+ providers via
Rclone for continuous sync.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/demos/aihub-knowledge-demo.webp" width="80%" alt="Knowledge ingestion demo">
</p>

### Track every step of the data pipeline

Dagster provides full lineage from source document to vector embedding: which files were processed, how they were
chunked, when embeddings were created, what ended up in Milvus. Automatic retry and failure handling included.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/demos/aihub-dagster-demo.webp" width="80%" alt="Dagster pipeline demo">
</p>

### Create agents without writing code

Developers publish agent blueprints (workflow logic, form schema, default config). Administrators create agent profiles
through a no-code configurator: pick a blueprint, fill in the form (knowledge base, model, temperature, system prompt),
and the agent goes live. One blueprint powers many profiles. An "Expert RAG Agent" blueprint becomes your HR policy
agent, legal FAQ agent, and IT support agent, each with different knowledge bases and instructions.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/demos/aihub-create-agent-demo.webp" width="80%" alt="Agent configurator demo">
</p>

### Ask questions grounded in your data

Agents retrieve relevant documents, generate answers with full source attribution, and stream responses in real-time.
Every interaction is traced end-to-end in Langfuse, from the user's question through retrieval, reranking, and
generation.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/demos/aihub-agent-interaction-demo.webp" width="80%" alt="Agent interaction demo">
</p>

### Control costs and model routing

LiteLLM provides a unified dashboard for all LLM usage. Set spending limits per user, team, or model. Route requests
between local and cloud models. Monitor token consumption, latency, and cost per request from a single pane.

<p align="center" width="100%">
<img src="https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docs/media/demos/aihub-litellm-demo.webp" width="80%" alt="LiteLLM cost control demo">
</p>

______________________________________________________________________

## Build with the SDK

You write an agent class, start it, and the platform does the rest. On startup the agent connects to NATS, registers
itself with the API, and becomes discoverable: it appears in the chat UI for users, gets a configuration form in the
admin panel for administrators, and receives full distributed tracing in Langfuse. No REST endpoints to build, no
WebSocket plumbing, no service discovery to configure.

Because agents communicate through the Swiss AI Agent Protocol, every typed event you emit (retrieval results, guard
decisions, LLM chunks) is rendered as a live, rich update in the chat UI. Users see exactly what the agent is doing:
which documents were retrieved, whether context was sufficient, how confident the answer is. And when your workflow
requires human judgment, `BotInTheLoop` sends the question to a Teams or Slack channel and pauses the agent until the
expert responds — native human-in-the-loop without building a single integration.

```bash
pip install swiss-ai-hub-agent    # Agent development
pip install swiss-ai-hub-pipeline # Data pipelines (Dagster)
pip install swiss-ai-hub-process  # Process orchestration
```

### Agents

An agent is a stateless, event-driven workflow. Each `@step` declares what it consumes and produces. The runtime handles
dispatch, dependency injection, state persistence, and horizontal scaling. Steps communicate through typed events, not
function calls.

This agent retrieves documents from the knowledge base, answers with an LLM when context is found, and escalates to a
human expert via Teams or Slack when it is not, pausing the workflow until the expert responds:

```python
from swiss_ai_hub.agent import Agent, AgentConfig, AgentRunner, step
from swiss_ai_hub.core.events import UserMessageEvent, LLMStopEvent, StopEvent
from swiss_ai_hub.core.events.semantic import RetrieverEvent
from swiss_ai_hub.core.events.guard import ContextSufficientEvent, ContextInsufficientEvent
from swiss_ai_hub.core.events.botl import BotInTheLoop
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.retrievers import KnowledgeRetriever
from swiss_ai_hub.core.i18n import LocaleString, LocaleHandler

class ExpertQAAgent(Agent):
    name = LocaleString(en="Expert QA")
    description = LocaleString(en="Answers from documents or escalates to a human expert")
    icon = "mage:user-check" 

    # Step 1: triggered when a user sends a message
    # config, t, and other dependencies are injected automatically — just declare what you need
    @step()
    async def retrieve(self, event: UserMessageEvent, config: AgentConfig, t: LocaleHandler) -> RetrieverEvent:
        retriever = KnowledgeRetriever(config.retriever)  # connect to the Milvus vector store
        nodes = await retriever.retrieve(query=event.user_query, t=t)  # semantic search
        return RetrieverEvent(nodes=nodes)  # pass retrieved documents to the next step

    # Step 2: emit a guard event — the runtime routes each type to a different step
    @step()
    async def check_context(self, event: RetrieverEvent) -> ContextSufficientEvent | ContextInsufficientEvent:
        if event.nodes:
            return ContextSufficientEvent()  # documents found → routes to respond()
        return ContextInsufficientEvent()  # no documents → routes to escalate()

    # Step 3a: only triggered by ContextSufficientEvent
    # the runtime also injects RetrieverEvent and UserMessageEvent from earlier in the run
    @step()
    async def respond(
        self, _: ContextSufficientEvent, retrieval: RetrieverEvent, start: UserMessageEvent,
        config: AgentConfig, displayer: EventDisplayer,
    ) -> LLMStopEvent:
        context = "\n\n".join(node.content for node in retrieval.nodes)  # build context from documents
        messages = [ChatMessage(role="system", content=f"Answer based on:\n{context}"), *start.messages]
        async with config.llm.cost_reporting_llm(displayer) as llm:  # tracks token usage and cost
            return await displayer.display_llm_stream(config.llm, llm, messages, as_stop_step=True)  # stream to chat UI

    # Step 3b: only triggered by ContextInsufficientEvent — sends question to a Teams/Slack channel
    # BotInTheLoop pauses the workflow until the expert responds
    @step()
    async def escalate(
        self, _: ContextInsufficientEvent, start: UserMessageEvent, config: AgentConfig,
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(question=start.user_query, user=start.user, channel_config=config.channel)

    # Step 4: the dispatcher resumes here when the expert replies in Teams/Slack
    @step()
    async def relay_expert(self, event: BotInTheLoop.response, displayer: EventDisplayer) -> StopEvent:
        await displayer.display_chunk(f"{event.responder.user_name}: {event.response}", model_name="human-expert")
        return StopEvent()  # workflow complete

# One line to start — connects to NATS, registers with the platform, and listens for events
runner = AgentRunner(agent_type=ExpertQAAgent, agent_config=AgentConfig.as_form())
await runner.run_forever()
```

On startup the agent registers itself: it appears in the chat UI, gets a configuration form in the admin panel, and
receives full distributed tracing through Langfuse. The runtime routes `ContextSufficientEvent` to `respond` and
`ContextInsufficientEvent` to `escalate`; steps never call each other. `BotInTheLoop` sends the question to a configured
Teams or Slack expert channel and pauses the workflow; when the expert responds, the dispatcher resumes at
`relay_expert`.

### Data pipelines

Pipelines use a two-stage architecture: Stage 1 pulls files from external sources into the S3 data lake, Stage 2
processes them through MinerU parsing, chunking, embedding, and Milvus vector storage. Both stages are Dagster pipelines
— observable assets detect changes, dynamic partitions track individual files, and eager automation propagates updates
through the entire chain.

This pipeline connects to a legacy SFTP server, syncs documents into the data lake, then parses, chunks, embeds, and
indexes them for RAG — with hierarchical summaries and LLM-powered table refinement:

```python
from swiss_ai_hub.pipeline import default_definitions, default_rclone_to_datalake_definitions
from swiss_ai_hub.core.rclone import sftp_source

# Stage 1: SFTP → Data Lake
# sftp_source() reads RCLONE_SFTP_* env vars (host, user, key file)
sftp = sftp_source()

stage_1 = default_rclone_to_datalake_definitions(
    datalake_container_name="acme-knowledge-base",
    datalake_directory_name="contracts",             # namespace in the vector store
    rclone_config=sftp,
    source_remote=f"{sftp.name}:/legal/contracts",   # path on the SFTP server
    include_patterns=["*.pdf", "*.docx"],            # only sync documents
    observe_job_hour=1,                              # check for changes daily at 01:00
)

# Stage 2: Data Lake → Vector Store
# Monitors the same S3 bucket, processes any new or changed files
stage_2 = default_definitions(
    datalake_container_name="acme-knowledge-base",
    embedding_model_name="embedding/bge-m3",
    llm_model_name="text-generation/gemma-4-31B-it",
    with_summary_nodes=True,                         # hierarchical summaries for multi-level RAG
    with_table_refinement=True,                      # LLM-powered table detection and splitting
    with_figure_descriptions=True,                   # vision LLM describes images in documents
)
```

Stage 1 runs as a Dagster code location that observes the SFTP server on a daily schedule. When files change, Rclone
syncs them into SeaweedFS. Stage 2 runs as a separate code location that watches the same S3 bucket — when new files
land, eager automation triggers MinerU parsing, structural chunking, embedding, and Milvus upsert. Deleted source files
cascade through both stages automatically.

Source connectors for SharePoint, OneDrive, Google Drive, S3, Azure Blob, SFTP, and local filesystems ship as templates
with ready-to-use configuration.

______________________________________________________________________

## Pre-configured models

Both deployment profiles use the same embedding and reranking models (BGE-M3, BGE-Reranker-v2-M3), so you can migrate
between local and cloud without re-embedding your vector database. Additional providers can be added through LiteLLM
configuration.

### Local models (airgapped / GPU deployment)

| Task                   | Model                                                                                      | Served by        |
| ---------------------- | ------------------------------------------------------------------------------------------ | ---------------- |
| Chat & text generation | [Qwen3-VL-30B-A3B-Instruct-FP8](https://huggingface.co/Qwen/Qwen3-VL-30B-A3B-Instruct-FP8) | Local vLLM       |
| Text embeddings        | [BGE-M3](https://huggingface.co/BAAI/bge-m3)                                               | Local vLLM       |
| Reranking              | [BGE-Reranker-v2-M3](https://huggingface.co/BAAI/bge-reranker-v2-m3)                       | Local vLLM       |
| Document parsing (OCR) | [MinerU 2.5 1.2B](https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B)                  | Local MinerU VLM |
| Speech-to-text         | [Faster Whisper Large v3](https://huggingface.co/Systran/faster-whisper-large-v3)          | Local Speaches   |
| Text-to-speech         | Piper / Kokoro                                                                             | Local Speaches   |

> [!TIP]\
> On a single NVIDIA RTX 6000 Pro (96 GB VRAM), the platform runs chat, embeddings, reranking, OCR, and speech-to-text
> locally. No API keys, no egress traffic, no cloud bills.

### Swiss LLM Cloud models (cloud deployment)

| Task                   | Model                                                                                                                           | Served by       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| Chat & text generation | [Apertus 70B](https://huggingface.co/swiss-ai/Apertus-70B-Instruct-2509), Gemma 4 31B, Kimi K2.6, Ministral 3 14B, Qwen3.5 122B | Swiss LLM Cloud |
| Text embeddings        | [BGE-M3](https://huggingface.co/BAAI/bge-m3)                                                                                    | Swiss LLM Cloud |
| Reranking              | [BGE-Reranker-v2-M3](https://huggingface.co/BAAI/bge-reranker-v2-m3)                                                            | Swiss LLM Cloud |
| Document parsing (OCR) | [MinerU 2.5 1.2B](https://huggingface.co/opendatalab/MinerU2.5-2509-1.2B)                                                       | Swiss LLM Cloud |
| Speech-to-text         | [Whisper Large v3](https://huggingface.co/openai/whisper-large-v3)                                                              | Swiss LLM Cloud |

All models on [Swiss LLM Cloud](https://swissllmcloud.ch/) run in Swiss data centers under Swiss jurisdiction. Stateless
request processing: no prompts stored, no data used for training, no content leaves Switzerland.

______________________________________________________________________

## Contributing

Swiss AI-Hub is developed by [bbv Software Services](https://www.bbv.ch) and open to contributions. See
[CONTRIBUTING.md](https://github.com/bbvch-ai/aihub-core/blob/main/CONTRIBUTING.md) for the full guide, or jump in:

|                                                                |                                                              |
| -------------------------------------------------------------- | ------------------------------------------------------------ |
| [Join the Discord](https://discord.gg/wArT8zDB)                | Ask questions, share what you have built, get help           |
| [Open an issue](https://github.com/bbvch-ai/aihub-core/issues) | Report bugs and request features                             |
| [Read the ADRs](https://bbvch-ai.github.io/aihub-core/arc42/)  | Understand key decisions before proposing structural changes |

## License

Swiss AI Hub is **fully open-source** under a **dual-license model** — each published artifact carries its own license,
and the per-package `LICENSE` file is authoritative for its subtree:

- **Apache-2.0** — the platform runtime and shared code (`packages/core`, `agent`, `api`, `bot`, `pipeline`, `process`,
  and the repository root). See [LICENSE](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSE).
- **AGPL-3.0-or-later** — the frontend (`packages/web`), the multi-tenant administration plane (`packages/sysadmin-api`,
  `packages/sysadmin-web`), and the backup service (`packages/backup`).

The split is intentional: the backend stays **permissive** so you can build and run proprietary agents and extensions
without any obligation to disclose them, while the **copyleft** components (the UI, the administration plane, and the
backup service) keep improvements flowing back to the community and block proprietary SaaS rehosts.

See [LICENSES.md](https://github.com/bbvch-ai/aihub-core/blob/main/LICENSES.md) for the full per-package matrix and
rationale.

______________________________________________________________________

<div align="center">

Built in Switzerland by [bbv Software Services](https://www.bbv.ch). Runs anywhere.

</div>
