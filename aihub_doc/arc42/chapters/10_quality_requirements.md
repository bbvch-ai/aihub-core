# Quality requirements

Chapter 1 (Introduction and goals) established five quality goals ordered by stakeholder priority: data sovereignty,
transparency and auditability, vendor independence, operational self-sufficiency, and extensibility without platform
modification. This chapter refines those goals into concrete scenarios that can be evaluated against the architecture.

## Quality tree

The quality tree organizes requirements into categories. Each leaf references one or more scenarios in the next section.

- **Data sovereignty**
  - Network isolation (DS-1, DS-2)
  - PII protection (DS-3, DS-4)
  - Air-gapped operation (DS-5)
- **Transparency and auditability**
  - Event traceability (TA-1, TA-2)
  - Cost attribution (TA-3)
  - Workflow determinism (TA-4)
- **Vendor independence**
  - Model portability (VI-1, VI-2)
  - Infrastructure portability (VI-3)
  - License independence (VI-4)
- **Operational self-sufficiency**
  - Deployment simplicity (OS-1, OS-2)
  - Update path (OS-3)
  - Failure recovery (OS-4, OS-5)
- **Extensibility without platform modification**
  - Agent deployment (EX-1, EX-2)
  - Data source integration (EX-3)
  - Process composition (EX-4)
- **Performance**
  - Response latency (PF-1)
  - Pipeline throughput (PF-2)
- **Security**
  - Authentication (SE-1)
  - Authorization granularity (SE-2)
  - Lateral movement prevention (SE-3)

## Quality scenarios

### Data sovereignty

**DS-1: Network isolation prevents unauthorized data egress.** A container on the backend network attempts to open a
connection to an external IP address. The connection fails because the backend network is marked `internal: true` in
non-dev deployment stages. Only containers on the proxy network (via Traefik) and the egress network (with ICC disabled)
can reach external hosts. An operator can verify this by inspecting the generated Docker Compose file and the network
definitions.

**DS-2: Egress network prevents lateral movement.** Playwright runs on the egress network with inter-container
communication disabled. Playwright can reach external websites (required for web scraping) but cannot connect to any
other container in the stack, including databases and the message broker. A penetration test against Playwright confirms
that no TCP connection to any internal service succeeds.

**DS-3: PII is redacted before reaching external providers.** An agent configured with the `presidio-mask-guard`
guardrail sends a prompt containing a person's name and email address to an external LLM provider. LiteLLM intercepts
the request in pre-call mode, sends the prompt to the Presidio analyzer, and replaces the detected entities with tokens
(`<PERSON>`, `<EMAIL_ADDRESS>`) before forwarding to the provider. The Langfuse trace for this request shows the
original prompt (with PII) and the anonymized prompt (without PII) as separate spans.

**DS-4: PII blocking rejects requests containing sensitive data.** An agent configured with the `presidio-block-guard`
guardrail sends a prompt containing a credit card number. LiteLLM detects the entity and rejects the entire request
before it leaves the platform. The agent receives an error, and an `ExceptionEvent` surfaces the rejection reason in the
UI.

**DS-5: The platform operates without any external network access.** An operator deploys the platform on an air-gapped
server with no internet connectivity. Local llama.cpp instances serve chat (Gemma-3-12B), embedding (Qwen3-0.6B), and
reranking (Qwen3-Reranker-0.6B) models. Speaches serves speech-to-text (Whisper) and text-to-speech (Kokoro). All model
weights are pre-loaded into the shared HuggingFace cache volume. Users interact with agents through the web chat
interface. No request leaves the server. Langfuse, the OTEL Collector, and all databases run self-hosted within the same
Docker Compose stack.

### Transparency and auditability

**TA-1: Every agent interaction is reconstructable from the event log.** A compliance officer opens a thread in the
Admin UI and sees the complete event timeline: the user's message (`UserMessageEvent`), the agent's step executions
(each as a named event), every LLM call (`LLMEvent` with full prompt and response), every document retrieval
(`RetrieverEvent` with source references and relevance scores), guard evaluations (`GuardEvent`), reasoning steps
(`ThoughtEvent`), and the final response (`StopEvent`). Each event carries a nanosecond-precision timestamp, a unique
identifier, and a parent event reference. The events are persisted in MongoDB by the `EventPersister` and are available
even if the WebSocket connection was interrupted during the interaction.

**TA-2: Distributed traces span from HTTP request to agent step.** An operator opens a trace in Langfuse and follows a
single user request from the FastAPI HTTP span, through the NATS JetStream publish span, to the agent dispatcher span,
to the individual step execution spans, and into each LLM call span. W3C Trace Context propagated in NATS message
headers links all spans under a single trace ID. The OTEL Collector's noise filter removes health check and database
client spans, keeping the trace focused on application-level operations.

**TA-3: Cost is attributed per user, per agent, and per trace.** An administrator opens the Langfuse dashboard and sees
token consumption and cost broken down by user, by agent class, and by individual trace. LiteLLM records token counts
and cost per request. The `LangfuseProvisioner` registers custom model pricing definitions for models whose names (e.g.,
`text-generation/nano`) do not match Langfuse's built-in pricing database. Per-role usage limits enforced via Redis Lua
scripts cap spending by time period.

**TA-4: Agent workflows are deterministic sequences, not opaque loops.** An auditor inspects an agent's workflow graph
in the Admin UI (transmitted via `AgentClassDiscoveryResponseEvent` during discovery). The graph shows every step, its
input and output event types, and the edges between them. Each step has a `max_executions_per_run` limit that prevents
infinite loops. The auditor can predict which steps will execute for any given input by following the event type edges.
No step executes autonomously; every execution is triggered by a typed event matching its input annotation.

### Vendor independence

**VI-1: Switching LLM providers requires only a configuration change.** An organization switches from Azure OpenAI
GPT-4o to a locally hosted Gemma-3-12B model. An administrator changes the model assignment in LiteLLM's configuration
file. No agent code changes. No data migration. The switch takes effect on the next LLM request. Agent code calls
`llm_config.cost_reporting_llm()`, which resolves to whatever model LiteLLM routes to, without any provider-specific
logic.

**VI-2: Multiple model providers coexist in the same deployment.** An organization runs local llama.cpp models for
general chat (low cost, no data egress), Azure OpenAI for complex reasoning tasks (higher capability), and a local
Qwen3-0.6B for embeddings. All three providers are registered in LiteLLM's configuration. Agents select models by
logical name (e.g., `text-generation/default`, `text-generation/premium`), not by provider. The administrator can
reassign logical names to different providers without touching agent code.

**VI-3: No component depends on a proprietary infrastructure service.** Every infrastructure component in the stack uses
an open-source license compatible with Apache 2.0 distribution. FerretDB provides the MongoDB wire protocol without a
MongoDB Inc. SSPL dependency. Valkey provides Redis compatibility without Redis Ltd.'s RSALv2/SSPL license. Langfuse
(MIT) replaced Phoenix (ELv2). MinerU (AGPL) runs in isolated containers with REST-only communication, maintaining
license isolation. The platform can run entirely on commodity Linux servers without any cloud-provider-specific service.

**VI-4: Replacing a component does not require changes beyond the integration boundary.** An operator decides to replace
Milvus with a different vector database. The change requires implementing a new `VectorStoreIOManager` for the pipeline
and a new vector store adapter for agent retrieval, both in aihub_lib. No agent code, API code, or frontend code
changes. The NATS event protocol, the agent discovery mechanism, and the form duality pattern are unaffected.

### Operational self-sufficiency

**OS-1: The platform starts with a single command.** An operator copies `.env.dev` to `.env`, adjusts credentials, and
runs `docker compose -f docker-compose.latest.yml up -d`. Docker Compose's `depends_on` with health checks ensures that
infrastructure services start before application services. Init containers create database schemas, S3 buckets, and
default roles idempotently. The platform is usable within the time it takes for all containers to pass their health
checks.

**OS-2: No specialized expertise is required for deployment.** The platform ships as Docker Compose files, not Helm
charts or Terraform modules. An operator who understands Docker, environment variables, and DNS records can deploy and
operate the platform. The Jinja2 template system generates all compose files and service configurations from a single
source, so the operator does not need to maintain consistency across dozens of configuration files manually.

**OS-3: Updates arrive as new Docker image tags.** An operator updates the platform by changing image tags in the
compose file (or pulling new tags if using `latest` or `nightly`) and running `docker compose up -d`. Docker Compose
restarts only the containers whose images changed. Database schemas are migrated automatically by the applications on
startup. No manual migration scripts, no downtime coordination beyond the container restart.

**OS-4: An agent crash does not lose workflow state.** An agent process is killed mid-run (out-of-memory, deployment
restart). When the agent restarts, `JetStreamEventStore` replays all historical events from JetStream, the dispatcher
reconstructs which steps have executed via `StepStore` in Valkey, and JetStream redelivers the unacknowledged control
event. The idempotency check (`was_called_with_events()`) prevents re-execution of completed steps. The run resumes from
where it was interrupted.

**OS-5: Frontend disconnection does not affect agent execution.** A user's browser crashes or loses network connectivity
while an agent is processing a request. The agent continues executing because its workflow is driven by control events
on JetStream, not by the frontend connection. Display events published during the disconnection are lost (NATS Core is
ephemeral), but the `EventPersister` writes every event to MongoDB. When the user reconnects and opens the thread, the
Admin UI fetches the complete event history from the REST API.

### Extensibility without platform modification

**EX-1: A new agent is deployed without changing platform code.** A developer writes a Python class with
`@step`-decorated methods, defines its `AgentConfig` with configurable and non-configurable fields, and deploys it as a
Docker container that connects to NATS. The API gateway discovers the agent within 60 seconds via
`ClassDiscoveryRequestEvent`, dynamically registers REST and SSE streaming endpoints for its event types, invalidates
the OpenAPI schema, and begins routing user messages to the agent. No platform code was modified. No endpoint was
manually registered. The agent inherits authentication, tracing, cost tracking, event persistence, and WebSocket
streaming from the SDK base classes and the platform's NATS subscribers.

**EX-2: Agent configuration is managed without developer involvement.** An administrator opens the Admin UI, selects a
discovered agent class, chooses a profile template, adjusts configurable fields (model selection, temperature, knowledge
database, system prompt), and saves the profile. The configuration is stored in MongoDB and fetched via NATS RPC on
every `StartEvent`. The developer defined which fields are configurable by setting them to `FormkitElement` instances in
`as_form()`; the rest is handled by the platform.

**EX-3: A new document source is added without modifying the processing pipeline.** A developer defines a new Dagster
observable source asset that polls a custom document source and returns `DataVersionsByPartition`. The asset's I/O
manager downloads files into SeaweedFS as `DataLakeFile` objects. The existing Stage 2 pipeline (parse, chunk, embed,
index) processes these files automatically because it consumes `DataLakeFile` regardless of origin.
`AutomationCondition.eager()` triggers downstream materialization within 60 seconds of detecting a new data version.

**EX-4: A process composes agents, humans, and external systems without custom integration code.** A developer defines a
process class with `@process_step`-decorated methods. Steps declare their inputs and outputs using `Agent.In`,
`Human.Out`, `Program.Out` type annotations. The `AgentDelegator` handles agent-to-process bridging (creating threads,
wrapping stop events as work events). The API handles human task assignment (rendering forms, collecting submissions).
The process engine handles webhook-based program delegation. The developer writes only the orchestration logic; all
communication infrastructure is provided by the platform.

### Performance

**PF-1: Streaming response tokens reach the user within the LLM's time-to-first-token.** When an agent streams LLM
output, `ChunkEvent` objects are published to NATS Core (ephemeral, no persistence overhead) and forwarded to the
WebSocket or SSE connection. The path from LLM token generation to user display involves no queuing beyond the NATS Core
pub/sub and the `asyncio.Queue` in the SSE generator. Display events bypass JetStream entirely, avoiding the durability
overhead that control events incur.

**PF-2: Document processing scales linearly with document count.** Each document is an independent Dagster partition.
Processing one document does not block or slow down any other document. A failure in one partition does not affect
others. Dagster's dynamic partitioning adds new documents as partitions at observation time, and
`AutomationCondition.eager()` triggers processing within 60 seconds. The pipeline's throughput scales with the number of
available workers and the inference capacity of the embedding and parsing services.

### Security

**SE-1: Authentication supports multiple identity providers and token types.** The `TokenAndOauth2Handler` composes
authentication strategies dynamically: OAuth2/OIDC (Azure AD JWT validation with JWKS), API access tokens (MongoDB
lookup with constant-time comparison), OpenWebUI HMAC-signed headers, and superuser tokens. Each strategy resolves to
the same `UserIdentity` model. WebSocket authentication uses the same handlers via `authenticate_token()` on the first
message. Adding a new identity provider (Keycloak, LDAP) requires implementing a new `AuthHandler` and
`IdentityProvider` without changing existing authentication logic.

**SE-2: Permissions are granular to individual agent instances.** Access rules use dotted-path notation with wildcards:
`aihub.user.agent.RAGAgent.hr-agent` grants access to a specific agent instance, `aihub.user.agent.RAGAgent.*` grants
access to all instances of a class, and `aihub.admin.agent.>` grants admin access to all agents. Permission templates in
controllers interpolate path parameters at request time, so a single endpoint definition enforces instance-level access
control without per-instance code.

**SE-3: Container compromise does not grant access to unrelated services.** The five-network Docker isolation model
ensures that a compromised container can only reach services on its assigned networks. A compromised Playwright
container (egress network, ICC disabled) cannot reach any other container. A compromised llama.cpp container (backend
network only) cannot reach databases (data network) or storage (storage network). The API is the most connected service
(four networks) and is therefore the highest-value target; it is protected by authentication, authorization, and the
Traefik reverse proxy.
