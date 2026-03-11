# Solution strategy

## Driving forces

Five quality goals from chapter 1 (Introduction and goals) determine the architecture's shape: data sovereignty,
transparency, vendor independence, operational self-sufficiency, and extensibility without platform modification. Two
organizational constraints from chapter 2 (Architecture constraints) narrow the solution space further: the platform
must ship as Docker Compose (no Kubernetes requirement), and all inter-service communication must flow through NATS (no
direct HTTP calls for workflow orchestration). Every technology choice and structural decision documented below traces
back to at least one of these forces.

## Top-level decomposition

### Event-driven architecture over request-response

The platform uses an event-driven architecture with NATS as the sole communication backbone. Services publish and
subscribe to events rather than calling each other through REST endpoints. This choice is motivated by three quality
goals simultaneously.

Transparency requires that every interaction between components is observable. Events are immutable records. Publishing
a UserMessageEvent, a RetrieverEvent, or a StopEvent creates a persistent trace of what happened, when, and in what
order. A request-response model would require separate instrumentation to achieve the same visibility.

Extensibility requires that new agents can join the system without modifying existing components. With pub/sub, a new
agent subscribes to topics it cares about and publishes events when it has results. The API gateway, frontends, and
other agents do not need to know about it in advance. A REST-based registration model would require the platform to
maintain an agent registry and expose registration endpoints.

Vendor independence requires loose coupling between components. Event-driven communication means the API gateway does
not depend on any specific agent's interface, and agents do not depend on the API gateway's internal structure.
Replacing or upgrading any component requires only that it speaks the same event protocol.

### Control and display event separation

The Swiss AI Agent Protocol distinguishes two event categories. Control Events drive workflow state transitions: they
trigger agent steps, carry user messages, and signal workflow completion. Display Events provide observability: they
stream LLM chunks, expose retrieval results, and surface agent reasoning. Control Events are published on NATS JetStream
for durability. Display Events are published on NATS Core for ephemeral real-time delivery.

This separation guarantees that UI failures cannot break agent logic. A crashed frontend does not prevent agents from
completing their workflows. It also means agents can expose detailed internal reasoning through Display Events without
risk, because those events never influence workflow decisions even if they are lost or delayed.

### Platform and SDK as independent layers

The platform provides runtime infrastructure: authentication, LLM routing, vector storage, document parsing, event
streaming, and observability. The SDK provides the building blocks for custom logic: agent base classes, pipeline
factories, process definitions, and event types. The two layers communicate exclusively through NATS events and the
shared library swiss_ai_hub.core.

SDK code never makes direct database queries, never calls platform REST endpoints for workflow purposes, and never
implements its own authentication logic. It uses swiss_ai_hub.core abstractions for all infrastructure access. This
boundary exists so that platform updates do not break SDK-built agents and SDK changes do not require platform
redeployment. Each layer has its own release cycle.

## Technology decisions

### NATS for messaging

NATS serves as the central message broker for all inter-service communication. The Swiss AI Agent Protocol defines a
hierarchical topic structure (`agent.{class}.{id}.{thread}.{display}.{run}.{event_type}.{event_name}.{event_id}`) that
encodes routing, scoping, and event classification directly in the subject line. JetStream provides durable event
streams for Control Events. NATS Core handles ephemeral pub/sub for Display Events and request-reply patterns for
configuration RPC.

NATS was chosen over heavier alternatives because the platform's messaging patterns are straightforward: pub/sub with
hierarchical topics, durable streams for event replay, and request-reply for synchronous configuration queries. NATS
supports all three natively with minimal operational overhead. Its support for W3C Trace Context propagation in message
headers enables end-to-end distributed tracing across asynchronous boundaries without custom instrumentation.

### LiteLLM for model routing

Every LLM request in the platform, whether from an agent, the chat UI, or a bot integration, routes through LiteLLM.
LiteLLM provides an OpenAI-compatible HTTP API that abstracts away provider differences. Switching from one cloud
provider to another or to a locally hosted vLLM model requires a configuration change in LiteLLM, not a code change in
any agent or service.

This gateway pattern directly addresses vendor independence. It also centralizes cost tracking (LiteLLM records token
consumption per request), PII filtering (Presidio intercepts requests before they reach external providers), and access
control (API key management and per-user budgets). Without a unified gateway, each of these concerns would need to be
implemented separately in every service that calls an LLM.

### Dual-mode inference: Swiss LLM Cloud and local vLLM

The platform supports two inference modes. Non-GPU deployments route all inference through **Swiss LLM Cloud**, a
Swiss-hosted provider that keeps data within Swiss infrastructure. GPU deployments run all inference locally via
**vLLM** on a dedicated NVIDIA RTX 6000 Pro (96 GB VRAM). The two modes never mix: non-GPU compose files contain no
local model containers, and GPU compose files reference no cloud endpoints.

Embedding, reranking, OCR, and transcription use the same model families in both modes (BGE-M3, BGE-Reranker-v2-m3,
MinerU, Whisper Large v3), so switching between deployment modes requires no re-embedding. Text generation models
differ: the GPU runs a single multimodal model (Qwen3-VL-30B), while the cloud offers multiple models at different
capability and cost tiers.

All models are registered in LiteLLM and are indistinguishable from cloud providers from the perspective of calling
code. Local inference exists to support air-gapped deployments where no data may leave the organization's
infrastructure. See the ADR `2026_02_24_swiss_sovereign_dual_mode_inference.md` for the full rationale.

### FerretDB for document storage

The platform uses FerretDB instead of native MongoDB for document storage (conversation history, agent configuration,
event persistence). FerretDB provides the MongoDB wire protocol but stores data in PostgreSQL. This avoids a dependency
on MongoDB Inc.'s Server Side Public License, which would conflict with the platform's distribution model. It also
reduces the number of distinct database engines in the stack: FerretDB shares PostgreSQL as a backend, simplifying
backup and operational procedures.

### Milvus for vector search

Milvus stores vector embeddings generated by the document ingestion pipeline and serves semantic search queries during
RAG retrieval. It was chosen because it is open-source, self-hosted, and purpose-built for high-dimensional vector
search with support for multiple index types. It uses etcd for metadata management and SeaweedFS (via the S3 gateway)
for data persistence, integrating with infrastructure the platform already runs.

### SeaweedFS for object storage

SeaweedFS provides S3-compatible object storage without a dependency on AWS or any cloud provider. The platform uses it
as a data lake for ingested documents, a storage backend for Milvus vector data, an artifact store for Langfuse traces,
and a file upload target for the chat UI. Its distributed architecture (master, volume servers, filer, S3 gateway) can
scale storage capacity by adding volume servers. Running on the dedicated storage network isolates it from application
and database traffic.

### Dagster for data pipelines

The document ingestion pipeline is built on Dagster's asset-based model. Each processing stage (download, parse, chunk,
embed, index) is defined as a software-defined asset with explicit inputs and outputs. This provides data lineage from
every vector embedding back to its source document, which is necessary for auditing retrieval results and debugging RAG
quality.

The pipeline follows a two-stage pattern. Stage 1 is source-specific: it monitors external storage (SharePoint,
OneDrive, Google Drive, S3, SFTP via Rclone) for changes and downloads new or modified files into the SeaweedFS data
lake. Stage 2 is unified: it processes all data lake files through parsing (MinerU for OCR and structural extraction),
semantic chunking, embedding generation, and Milvus indexing. This separation means adding a new data source requires
only a new Stage 1 definition; the processing pipeline remains unchanged.

Dagster's dynamic partitioning treats each document as an independent partition, so processing scales linearly and
individual document failures do not block the rest of the pipeline.

### FastAPI for the API gateway

FastAPI handles HTTP REST, Server-Sent Events, and WebSocket connections between frontends and the NATS event bus. Its
async-native design matches the platform's requirement for consistent async I/O. The automatic OpenAPI schema generation
feeds the frontend's type-safe TypeScript SDK (generated via HeyAPI), keeping the API contract between backend and
frontend synchronized without manual maintenance.

### Nuxt 3 for the frontend

The admin UI and process UI are built with Nuxt 3 (Vue 3, TypeScript, PrimeVue, Tailwind CSS). The frontend consumes the
API exclusively through a generated TypeScript SDK and a single WebSocket connection for real-time Display Events.
Pinia-Colada manages server state as reactive queries and mutations, pushing incoming WebSocket events directly into the
cache without refetching.

### Valkey for ephemeral state

Valkey (a Redis-compatible fork) stores ephemeral agent state: RunContext (per-execution), ThreadContext
(per-conversation), session data, and WebSocket connection state. All data has a 30-day TTL. Agents can reconstruct
their conversational context from the NATS event history if Valkey data is lost, so no persistent data depends on Valkey
availability.

Valkey was chosen over Redis because Redis changed its license to a dual-license model (RSALv2/SSPLv1) that conflicts
with the platform's distribution as a bundled Docker Compose stack.

### PostgreSQL as relational backbone

PostgreSQL hosts four databases: OpenWebUI (chat history and user preferences), Langfuse (trace metadata), Dagster
(pipeline run state), and LiteLLM (usage tracking and API key management). A separate PostgreSQL instance serves as
FerretDB's storage backend. Using a single database engine for relational needs simplifies operations, backup
procedures, and monitoring.

### Transparency and auditability

Every agent step execution, LLM call, document retrieval, and user interaction is captured as an immutable event in the
NATS JetStream. Events carry nanosecond-precision timestamps, unique identifiers, parent event references, and user
identity. OpenTelemetry traces link these events across service boundaries via W3C Trace Context propagated in NATS
message headers. Langfuse captures the full prompt and response of every LLM call along with token counts and cost.
Agents use bounded, step-based workflows where each step is a named, discoverable unit of execution. The admin UI
renders the complete event timeline for any thread, providing a deterministic audit trail from user request to agent
response.

### Vendor independence

The LLM gateway abstracts all model access behind a single OpenAI-compatible interface. Switching providers is a
configuration change. All infrastructure components use open-source licenses compatible with the platform's Apache 2.0
distribution model.

### Operational self-sufficiency

The platform deploys with a single `docker compose up` command.

### Extensibility without platform modification

Agents are discovered at runtime through NATS. The API gateway broadcasts a ClassDiscoveryRequestEvent periodically;
running agents respond with their event schemas, configuration schemas, and workflow graphs. The gateway dynamically
generates REST endpoints for each discovered agent. Deploying a new agent means starting a container that connects to
NATS and publishes a discovery response. No platform code changes, no endpoint registration, no redeployment of the API
gateway. The agent inherits authentication, tracing, cost tracking, and event streaming from the SDK base classes and
swiss_ai_hub.core abstractions.

## Architectural patterns

### Bounded agent workflows

Agents follow explicit, step-by-step workflows defined with `@step` decorators. Each step accepts a typed input event,
performs one unit of work, and returns a typed output event. A dispatcher routes events to the appropriate step based on
which steps are ready to execute. Steps can declare maximum execution counts per run to prevent infinite loops and
preconditions that must be satisfied before execution.

This pattern was chosen over autonomous, goal-seeking agent loops. The trade-off is deliberate: agents have less
autonomy but their behavior is predictable, testable, and auditable. Every step execution appears as a named event in
the audit trail. The workflow graph is discoverable and visualizable. This aligns with the transparency quality goal and
with the requirements of regulated organizations that need to explain how an AI system arrived at a recommendation.

### Stateless agents with externalized state

Agent instances hold no in-memory state between workflow steps. All state is externalized to Valkey (ephemeral
RunContext and ThreadContext with 30-day TTL) and NATS JetStream (immutable event history). Agents reconstruct their
conversational context by replaying events from the thread's event stream. This enables horizontal scaling (any server
instance can execute any step) and crash recovery (a step can resume on a different instance if the original fails).

### Controller-service-entity separation

The API layer follows a three-tier pattern. Controllers handle HTTP routing, authentication via FastAPI's `Security()`
mechanism, and request/response serialization. Services contain business logic and external system integration, marked
as stateless classes with `@staticmethod` methods. Entities are MongoEngine documents that combine schema definition
with repository classmethods. Controllers never access the database directly; services never handle HTTP concerns.

### Form duality for configuration

Agent and process configurations use a pattern where the same Pydantic model serves two purposes. In form mode, fields
are FormkitElement instances that the admin UI renders as interactive form controls. In data mode, the same fields
contain the submitted values as primitive types. A single class definition produces both the UI form schema and the
runtime configuration validation, eliminating the need to maintain parallel definitions.
