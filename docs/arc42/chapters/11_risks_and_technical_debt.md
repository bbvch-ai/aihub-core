# Risks and technical debt

This chapter documents known technical risks and accumulated technical debt, ordered by severity. Risks are threats to
the architecture's quality goals that have not yet materialized but require monitoring or mitigation. Technical debt
represents intentional shortcuts or deferred work that increases the cost of future changes.

## Technical risks

### No formal database migration framework

The platform has no schema migration tool. Database schemas are created or updated implicitly by applications on
startup. This works for initial deployments but creates risk during upgrades: a schema change in FerretDB (MongoDB wire
protocol over PostgreSQL) or in the Pydantic models that define document structure has no versioned migration path.
Rolling back a failed upgrade requires restoring from backup rather than running a down-migration. The PostgreSQL
databases used by third-party services (Langfuse, Dagster, LiteLLM, OpenWebUI) manage their own migrations internally,
but the platform's own document schemas in FerretDB have no equivalent mechanism. This is tracked as a P0 item.
**Planned mitigation**: Introduce versioned migration scripts for FerretDB document schemas, executed idempotently at
application startup before serving requests. Schema versions would be stored in a metadata collection.

### Backup and restoration gaps

The platform stores persistent data across seven distinct systems (PostgreSQL, FerretDB, Milvus, SeaweedFS, NATS
JetStream, Valkey, Neo4j). All data resides under a single volume root directory, making filesystem-level backups
possible, but the platform provides no built-in mechanism to create application-consistent snapshots across all stores
simultaneously. A backup taken while an agent is mid-run may capture an inconsistent state between JetStream (event
log), FerretDB (persisted events), and Valkey (step tracking). Platform-level backup using internal S3 snapshots and
infrastructure-level off-site replication via SeaweedFS are both tracked as P0 items and are in progress. **Planned
mitigation**: A two-tier backup strategy is being implemented. Tier 1: Offen-based automated daily backups to S3 for all
stateful volumes. Tier 2: SeaweedFS asynchronous replication for off-site disaster recovery of object storage.

### Mime-type trust in file uploads

The platform currently trusts the `Content-Type` header provided by the client when files are uploaded. A malicious user
could upload an executable file with a forged `image/png` mime type. The file would be stored in SeaweedFS and
potentially served to other users or processed by the pipeline without content-based validation. File type detection
based on magic bytes (content sniffing) is not yet implemented. This is tracked as a P0 item. **Planned mitigation**:
Add server-side content sniffing using `python-magic` (libmagic bindings) in the upload endpoint, rejecting files whose
detected type does not match the declared Content-Type or falls outside an allowed-types whitelist.

### OpenWebUI agent visibility bypass

OpenWebUI renders all registered agents and models in its chat interface without consulting the platform's RBAC system.
A user who lacks `aihub.user.agent.RAGAgent.hr-agent` permission in the Admin UI can still see and attempt to interact
with the HR agent through OpenWebUI's model selector. The API will reject unauthorized requests, so no data leaks, but
the agent's existence and description are exposed. Filtering OpenWebUI's visible agent list based on the authenticated
user's permissions requires either OpenWebUI-side customization or a proxy layer that rewrites OpenWebUI's model list
endpoint. This is tracked as a P0 item. **Planned mitigation**: Implement a middleware or reverse proxy filter on the
OpenWebUI pipeline endpoint that intersects the model/agent list response and removes entries the authenticated user
lacks permission for, using the same `AccessChecker` rules that protect the Admin UI endpoints.

### Agent configuration schema evolution

When a developer changes an agent's `AgentConfig` Pydantic model (adding, removing, or renaming fields), existing
profiles stored in MongoDB become stale. `model_validate()` may fail on load if required fields were added, or silently
ignore removed fields. The `deep_merge()` of non-configurable values with persisted configurable values depends on field
names matching between the code and the stored data. There is no schema versioning, no migration path for stored
configurations, and no backend validation that a persisted profile is compatible with the current agent code. Backend
verification of agent configs against the live schema is tracked as a P0 item. **Planned mitigation**: During agent
discovery, validate all persisted profiles against the current `AgentConfig` schema. Profiles that fail validation are
flagged as incompatible in the Admin UI, preventing their use until an administrator updates them.

### Docker volume encryption at rest

Persistent data stored under the volume root directory is not encrypted at rest. An attacker with physical access to the
server or its disks can read database files, JetStream streams, vector embeddings, and uploaded documents directly. LUKS
full-disk encryption at the OS level would mitigate this, but the platform does not enforce or verify it. This is
tracked as a P0 and is under discussion because the mitigation lies outside the platform's Docker Compose boundary.
**Planned mitigation**: Document LUKS full-disk encryption as a deployment prerequisite in the operations guide. Add a
startup health check that verifies the volume root resides on an encrypted filesystem and logs a warning if not.

### Single-server deployment ceiling

The Docker Compose deployment model runs all containers on a single host. There is no built-in mechanism for horizontal
scaling, container orchestration across multiple nodes, or automatic failover. A hardware failure takes down the entire
platform. The ~30 containers compete for CPU, memory, and I/O on one machine, and GPU inference services are pinned to
device 0 with no multi-GPU distribution. Kubernetes support via Helm charts is tracked as a P2 milestone, and a full
rewrite to native Kubernetes operations is a separate P2 item. Until either is implemented, the platform's availability
and throughput are bounded by a single server's capacity. **Planned mitigation**: A Kubernetes Helm chart is the primary
path, translating the existing Docker Compose service definitions and network policies into Kubernetes manifests. As an
interim measure, Docker Swarm mode with replicated services could provide basic multi-node distribution without a full
Kubernetes migration.

### SSO integration fragility

OpenWebUI's authentication is not seamlessly integrated with the platform's SSO. Users may encounter separate login
prompts or session inconsistencies between OpenWebUI and the Admin UI, both of which use Azure AD but through different
integration points (OpenWebUI's built-in OAuth vs. the API's `TokenAndOauth2Handler`). Keycloak as a local OAuth2/OIDC
provider is in progress as a P2 item to provide a unified identity provider for self-hosted deployments without Azure
AD. Seamless SSO across all UIs is tracked as a P0 item. **Planned mitigation**: Deploy Keycloak as the single identity
broker, federating Azure AD and other providers behind a unified OIDC flow. All platform UIs (OpenWebUI, Admin UI,
Dagster, Langfuse) would authenticate through Keycloak, eliminating separate OAuth integration points.

### No load testing baseline

The platform has no load testing suite and no established performance baselines. Response latency under concurrent
users, maximum throughput of the document processing pipeline, NATS JetStream's behavior at queue depth limits, and
Milvus query performance at scale are all untested. The quality scenarios in chapter 10 (Quality requirements) describe
expected performance characteristics (streaming latency bounded by LLM time-to-first-token, linear pipeline scaling),
but these have not been validated under load. This is tracked as a P2 item. **Planned mitigation**: Build a load testing
suite using Locust that replays realistic user scenarios (concurrent RAG queries, document ingestion bursts, WebSocket
connections) against the full Docker Compose stack. Establish baseline metrics for P95 latency, throughput ceiling, and
resource saturation thresholds.

## Technical debt

### Single-tenant data model

The platform currently operates as a single-tenant system. All users share one set of databases, one NATS instance, one
Milvus collection namespace, and one set of agent configurations. Multi-tenancy — tenant-scoped database schemas,
tenant-aware authorization, tenant selection in the frontend, and tenant-scoped role management — is tracked across six
P1 issues and is partially in progress. Until multi-tenancy is implemented, each customer deployment requires a
completely separate Docker Compose stack, increasing operational overhead for organizations that serve multiple
independent teams or subsidiaries. **Planned mitigation**: Introduce a `tenant_id` field across all entities, NATS
subject hierarchies, and Milvus collection namespaces. Authorization rules would be extended with tenant-scoped
prefixes. The frontend would add a tenant selector. Implementation is phased across six P1 issues.

### Dual streaming infrastructure

The API maintains two parallel streaming mechanisms: WebSocket for the Admin UI (bidirectional, supports
human-in-the-loop interactions) and SSE for OpenWebUI and external consumers (unidirectional, OpenAI-compatible). Both
consume the same NATS display events but through different code paths (`WebSocketSender` vs. SSE generator functions).
Similarly, two OpenWebUI pipelines (event-based agent pipeline and OpenAI-compatible model pipeline) duplicate request
handling logic. This duplication increases the surface area for bugs and requires changes to streaming behavior to be
implemented twice. **Planned mitigation**: Extract a shared event streaming adapter that both the SSE generator and the
WebSocket sender consume, reducing the dual code paths to a single event-to-transport mapping layer.

### Event persister coupling

The `EventPersister` runs as a NATS subscriber within the API process, writing every event to MongoDB for historical
retrieval. This couples event persistence to the API's lifecycle — if the API restarts, event persistence is interrupted
until the subscriber reconnects. Extracting the event persister into a standalone service would improve reliability and
allow independent scaling, but it is deferred as a P2 item because JetStream's durable delivery guarantees that control
events are not lost during the gap (they are redelivered), and display events are ephemeral by design. **Planned
mitigation**: Extract the event persister into a standalone microservice with its own NATS durable consumer, decoupling
event persistence from the API's lifecycle.

### Presidio limited to single-language NER

Presidio's named entity recognition models are configured for German by default. PII detection for French, Italian, and
English content is less accurate or non-functional depending on the entity type. For a platform that supports four
languages in its UI and serves organizations across Switzerland's language regions, this creates a gap between the i18n
coverage of the user interface and the PII protection of the LLM gateway. Multi-language Presidio support is tracked as
a P3 enhancement. **Planned mitigation**: Configure per-language Presidio recognizer sets and select the appropriate set
based on the detected language of each prompt (using the existing locale context or a lightweight language detector).

### Missing observability in the bot scope

The bot integration (`packages/bot`) is not instrumented with OpenTelemetry. Traces that originate from a Teams or Slack
message do not connect to the downstream NATS and agent spans, creating a gap in the distributed trace. Diagnosing
issues reported through bot channels requires correlating bot-side logs with agent-side traces manually. Adding OTEL
instrumentation to the bot is tracked as a P2 item. **Planned mitigation**: Add `@trace_fn` decorators to `BaseChatBot`,
`CompletionHandler`, and `BotInTheLoopHandler` methods, and propagate the bot's trace context into the NATS StartEvent
headers so downstream agent spans link to the originating bot span.

### No agent versioning

When an agent's code changes (new steps, modified event types, different workflow graph), all running instances
immediately use the new version. There is no mechanism to run multiple versions of the same agent simultaneously, to
roll back to a previous version, or to migrate in-flight conversations to a new version gracefully. An agent update that
changes the step graph while runs are in progress can cause those runs to fail because the dispatcher's step readiness
logic encounters event types or step names that no longer exist. Agent versioning is tracked as a P3 enhancement.
**Planned mitigation**: Embed a version identifier in the agent's discovery response and NATS subject prefix. The
dispatcher would tag each run with the agent version at start time and reject events from mismatched versions, allowing
blue-green agent deployments.

### No run or delegation timeouts

Agent runs, human-in-the-loop requests, and bot-in-the-loop delegations have no timeout mechanism. A run that enters a
state where no step's input event is ever published will remain in progress indefinitely in the `StepStore`. A
human-in-the-loop request that is never answered blocks the process walkthrough permanently. The platform relies on
operators noticing stalled runs through the Admin UI or Langfuse traces. **Planned mitigation**: Add configurable
timeout durations to the dispatcher (per-run maximum wall time) and to delegation annotations (per-step response
deadline). On timeout, the dispatcher publishes an `ExceptionEvent` with a timeout-specific error code and cleans up the
run or walkthrough.

### No malware scanning for uploads

Files uploaded through the API or ingested through the pipeline are stored in SeaweedFS and processed without malware
scanning. A document containing embedded malware could be stored, chunked, and served to users through the knowledge
retrieval system. The pipeline's parsing step (MinerU) processes documents in isolated containers, limiting the blast
radius of a malicious payload during parsing, but the uploaded file remains in SeaweedFS and can be downloaded by
authorized users. **Planned mitigation**: Integrate ClamAV as a sidecar container. The upload endpoint would submit
files to ClamAV via its REST API before storing them in SeaweedFS, rejecting infected files with a descriptive error.

### Ansible configuration drift

The hosted deployment uses Ansible playbooks that are not based on Ansible Galaxy roles, making them harder to maintain
and share. OS-level updates on the deployment servers are not automated, creating a risk of unpatched vulnerabilities in
the host operating system. **Planned mitigation**: Refactor playbooks into reusable Ansible Galaxy roles with automated
`unattended-upgrades` for OS patching. Add a CI step that lints Ansible playbooks and validates role dependencies.
