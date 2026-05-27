# C4 Model Diagrams — Swiss AI Hub Ecosystem

**Phương pháp**: Simon Brown's C4 Model (4 levels of abstraction). **Phạm vi**: Platform (aihub-core) + 2 customer
deployments (aihub-bmd, aihub-ctc). **Định dạng**: Mermaid (render được trong VitePress, GitHub, IDE preview). **Tài
liệu song hành**:

- [Architecture Review Overview](01_architecture_review_overview.vi.md): Executive summary cho stakeholders.
- [Architecture Review Details](02_architecture_review_details.md): Technical deep-dive cho dev team.

______________________________________________________________________

## Mục lục

- [Level 1 — System Context](#level-1--system-context)
- [Level 2 — Container](#level-2--container) (3 views)
- [Level 3 — Component](#level-3--component) (4 zooms)
- [Dynamic Diagrams](#dynamic-diagrams) (5 sequences)
- [Deployment Diagram](#deployment-diagram)
- [Multi-Customer Topology View](#multi-customer-topology-view)
- [Future-State Target Architecture](#future-state-target-architecture)

______________________________________________________________________

## Level 1 — System Context

**Mục đích**: Đặt Swiss AI Hub trong bối cảnh — ai dùng nó, nó tích hợp với hệ thống nào.

```mermaid
C4Context
    title System Context — Swiss AI Hub Platform

    Person(end_user, "End User", "Nhân viên trong tenant — tương tác chat, gọi agent")
    Person(tenant_admin, "Tenant Admin", "Quản lý users, roles, agent configs trong tenant của mình")
    Person(sys_admin, "Sys Admin", "AIHubSysAdmin — quản lý platform-wide, provision tenants")
    Person(dev, "Developer", "Build customer projects (bmd, ctc) consume SDK")

    System(aihub, "Swiss AI Hub", "Self-hosted AI platform: agents, pipelines, processes, multi-tenant")

    System_Ext(keycloak, "Keycloak", "Identity provider — OIDC, tenant groups, roles")
    System_Ext(litellm_cloud, "Swiss LLM Cloud", "Sovereign LLM endpoints (chat, embed, rerank)")
    System_Ext(teams_slack, "MS Teams / Slack", "Bot integration channels")
    System_Ext(openwebui, "OpenWebUI", "Chat UI hosted alongside (de facto external)")
    System_Ext(sharepoint, "SharePoint / OneDrive", "Document sources (via Rclone)")
    System_Ext(jira_confluence, "Jira / Confluence", "Issue tracking & wiki (CTC use case)")
    System_Ext(azure_kv, "Azure Key Vault", "Secrets storage (CTC deployment)")

    Rel(end_user, aihub, "Chat, query, approve HITL", "HTTPS/SSE/WebSocket")
    Rel(tenant_admin, aihub, "Configure agents, manage users", "HTTPS")
    Rel(sys_admin, aihub, "Provision tenants, manage platform", "HTTPS")
    Rel(dev, aihub, "Consume SDK via git tag", "git+ssh")

    Rel(aihub, keycloak, "Auth, group sync", "OIDC/Admin API")
    Rel(aihub, litellm_cloud, "LLM completion, embedding", "HTTPS")
    Rel(aihub, teams_slack, "Bot messaging", "REST/Webhook")
    Rel(end_user, openwebui, "Chat UI", "HTTPS")
    Rel(openwebui, aihub, "Pipe to agents", "OpenAI-compatible API")
    Rel(aihub, sharepoint, "Document ingestion", "Rclone/HTTP")
    Rel(aihub, jira_confluence, "Issue/wiki sync (CTC)", "REST")
    Rel(aihub, azure_kv, "Fetch secrets at deploy", "Azure SDK")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Quan sát từ Context**:

| Actor         | Tần suất tương tác      | Concern chính                      |
| ------------- | ----------------------- | ---------------------------------- |
| End User      | High (chat, HITL)       | Latency, accuracy, privacy         |
| Tenant Admin  | Medium                  | Config UI usability, audit log     |
| Sys Admin     | Low                     | Tenant provisioning, observability |
| Developer     | Medium                  | SDK ergonomics, version stability  |
| Keycloak      | Per request (cached 6h) | Availability — outage cascades     |
| LiteLLM Cloud | Per LLM call            | Cost, latency, data residency      |
| OpenWebUI     | Per chat                | RBAC bypass risk (gap G1.5)        |

**Trust boundaries**:

```
┌──────────────────── INTERNAL (trusted) ────────────────────┐
│  end_user, tenant_admin, sys_admin, dev                    │
│  Swiss AI Hub (all containers)                             │
│  Keycloak (same network zone)                              │
└────────────────────────────────────────────────────────────┘
                            ↕ TLS
┌──────────────────── EXTERNAL (untrusted) ───────────────────┐
│  LiteLLM Cloud, Teams/Slack, SharePoint, Jira/Confluence   │
│  Azure Key Vault                                           │
└────────────────────────────────────────────────────────────┘
```

> **Gap visible at this level**:
>
> - OpenWebUI ở "ngoài" trust boundary nhưng có access trực tiếp vào agents → G1.5 (RBAC bypass).
> - LiteLLM Cloud xử lý PII chưa được scrub bởi Presidio (DTC-3) trước khi gửi ra.

______________________________________________________________________

## Level 2 — Container

### View 2.1 — Platform Container Diagram

**Mục đích**: Các "containers" (deployable units) của Swiss AI Hub.

```mermaid
C4Container
    title Container Diagram — Swiss AI Hub Platform (aihub-core)

    Person(user, "User", "End user / Admin")
    System_Ext(keycloak, "Keycloak", "Identity provider")
    System_Ext(litellm_cloud, "Swiss LLM Cloud", "Sovereign LLMs")

    System_Boundary(aihub, "Swiss AI Hub") {
        Container(web, "Admin UI", "Nuxt 3, Vue 3, PrimeVue", "Tenant + agent admin")
        Container(openwebui_proxy, "OpenWebUI", "Open source", "Chat UI (modelproxy → API)")
        Container(api, "API Gateway", "FastAPI, Python 3.13", "REST + WebSocket + SSE")
        Container(agents, "Agent Workers", "Python (DispatchableWorkflow)", "8 agent types; horizontal scale via NATS")
        Container(bot, "Bot Service", "FastAPI", "Teams/Slack integration")
        Container(pipelines, "Pipeline Workers", "Dagster", "Document ingestion (2-stage)")
        Container(backup, "Backup Service", "Dagster (independent)", "Daily backup all stateful")
        Container(litellm_proxy, "LiteLLM Proxy", "Python", "LLM gateway + cost tracking")
        Container(traefik, "Traefik", "Reverse proxy", "TLS termination, routing")

        ContainerDb(postgres, "PostgreSQL", "4 DBs", "openwebui, langfuse, dagster, litellm")
        ContainerDb(ferretdb, "FerretDB", "MongoDB wire over PG", "Entities, configs, threads, events")
        ContainerDb(milvus, "Milvus", "Vector DB", "Embeddings + sparse BM25 (1023 partitions)")
        ContainerDb(neo4j, "Neo4j", "Graph DB", "Knowledge graph (optional)")
        ContainerDb(valkey, "Valkey", "Redis-compat", "StepStore, ThreadContext, RunContext")
        ContainerQueue(nats, "NATS JetStream", "Event broker", "Control + Display events")
        ContainerDb(seaweedfs, "SeaweedFS", "S3-compat", "Documents, artifacts, backups")
        ContainerDb(etcd, "etcd", "KV store", "Metadata cho Milvus + SeaweedFS")
    }

    Rel(user, traefik, "HTTPS")
    Rel(traefik, web, "")
    Rel(traefik, openwebui_proxy, "")
    Rel(traefik, api, "")

    Rel(web, api, "REST", "HTTPS/SSE")
    Rel(openwebui_proxy, api, "OpenAI-compat", "HTTPS")

    Rel(api, keycloak, "JWT verify, group sync")
    Rel(api, nats, "Publish events")
    Rel(api, ferretdb, "CRUD entities")
    Rel(api, valkey, "Step state, sessions")
    Rel(api, seaweedfs, "File upload/download")

    Rel(agents, nats, "Subscribe events, publish")
    Rel(agents, valkey, "RunContext, ThreadContext")
    Rel(agents, ferretdb, "Persist events")
    Rel(agents, milvus, "Vector search RAG")
    Rel(agents, neo4j, "Graph queries")
    Rel(agents, litellm_proxy, "LLM calls")

    Rel(bot, nats, "Bot events")
    Rel(bot, agents, "Via NATS")

    Rel(pipelines, seaweedfs, "Documents")
    Rel(pipelines, milvus, "Insert vectors")
    Rel(pipelines, ferretdb, "Document metadata")
    Rel(pipelines, litellm_proxy, "Embedding calls")
    Rel(pipelines, nats, "Triggers, sensors")

    Rel(backup, postgres, "pg_dump")
    Rel(backup, ferretdb, "Mongo dump")
    Rel(backup, milvus, "milvus-backup CLI")
    Rel(backup, neo4j, "neo4j-admin")
    Rel(backup, valkey, "RDB snapshot")
    Rel(backup, nats, "Stream snapshot")
    Rel(backup, seaweedfs, "Store backups")

    Rel(litellm_proxy, litellm_cloud, "LLM API", "HTTPS")

    Rel(milvus, etcd, "Metadata")
    Rel(seaweedfs, etcd, "Filer coordination")
    Rel(ferretdb, postgres, "Storage backend")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

**30+ containers thực tế** trong `infra/docker-compose.dev.yml` — diagram trên đã consolidate các phụ trợ (etcd,
postgres-ferretdb) vào logical containers.

**Container vs scaling readiness**:

| Container        | Stateless? | Horizontal scale ready? | Bottleneck                           |
| ---------------- | :--------: | :---------------------: | ------------------------------------ |
| Admin UI (Nuxt)  |     ✅     |           ✅            | Asset CDN cần                        |
| OpenWebUI        |     ⚠️     |           ⚠️            | DB-backed sessions                   |
| API Gateway      |     ✅     |           ✅            | Keycloak call per req                |
| Agent Workers    |     ✅     |           ✅            | NATS consumer groups OK              |
| Bot Service      |     ✅     |           ✅            | -                                    |
| Pipeline Workers |     ❌     |           ❌            | `in_process_executor` (DTC-6)        |
| Backup Service   |     ❌     |           N/A           | Singleton design OK                  |
| LiteLLM Proxy    |     ✅     |           ✅            | Single instance hiện tại             |
| PostgreSQL       |     ❌     |           ❌            | Single instance                      |
| FerretDB         |     ❌     |           ❌            | **FerretDB không sharding**          |
| Milvus           |     ❌     |           ❌            | **Single-node, HNSW wall**           |
| Neo4j            |     ❌     |           ⚠️            | Cluster mode khả thi                 |
| Valkey           |     ❌     |           ❌            | **Single instance**                  |
| NATS JetStream   |     ⚠️     |           ⚠️            | Single node hiện tại                 |
| SeaweedFS        |     ❌     |           ⚠️            | **replication="000"** (no replicate) |

### View 2.2 — Customer Project Container Diagram (BMD example)

**Mục đích**: Customer project consume SDK như thế nào.

```mermaid
C4Container
    title Container Diagram — aihub-bmd (Customer Project)

    System_Ext(aihub_core_sdk, "Swiss AI Hub Core SDK", "v0.279.2 git tag")
    System_Ext(smb_share, "SMB Share", "Customer file source")
    System_Ext(aihub_platform, "aihub-core Platform", "Deployed separately")

    System_Boundary(bmd, "aihub-bmd (Customer Deployment)") {
        Container(bmd_agent_svc, "BMD Agent Service", "Python FastAPI", "Selection router")
        Container(expert_rag_svc, "Expert RAG Service", "Python FastAPI", "RAG responder")
        Container(expert_asking_svc, "Expert Asking Service", "Python FastAPI", "Expert escalation")
        Container(pipeline_customers, "Customers Pipeline (2-stage)", "Dagster", "SMB→S3→Milvus")
        Container(pipeline_suppliers, "Suppliers Pipeline (2-stage)", "Dagster", "SMB→S3→Milvus")
        Container(bmd_dagster_ui, "Dagster Webserver", "Dagster", "Pipeline orchestration UI")
        Container(configs, "Configs", "16 service configs (Jinja2)", "Traefik, Keycloak, OTEL, etc.")
    }

    Rel(bmd_agent_svc, aihub_core_sdk, "Extends Agent base", "Python import")
    Rel(expert_rag_svc, aihub_core_sdk, "Extends Agent", "Python import")
    Rel(expert_asking_svc, aihub_core_sdk, "Extends Agent", "Python import")
    Rel(pipeline_customers, aihub_core_sdk, "Uses default_definitions()", "Python import")
    Rel(pipeline_suppliers, aihub_core_sdk, "Uses default_definitions()", "Python import")

    Rel(pipeline_customers, smb_share, "Watch + download", "SMB protocol")
    Rel(pipeline_suppliers, smb_share, "Watch + download", "SMB protocol")
    Rel(pipeline_customers, aihub_platform, "S3 write, Milvus insert, NATS events")
    Rel(pipeline_suppliers, aihub_platform, "S3 write, Milvus insert, NATS events")

    Rel(bmd_agent_svc, aihub_platform, "NATS subscribe/publish")
    Rel(expert_rag_svc, aihub_platform, "NATS subscribe/publish + Milvus query")
    Rel(expert_asking_svc, aihub_platform, "NATS + Teams escalation")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Quan sát BMD**:

- 5 deployable containers tự chạy (3 agent services + 2 pipelines).
- Tất cả dùng `aihub-core SDK v0.279.2` qua git tag.
- Phụ thuộc aihub-core platform deployment cho NATS, Milvus, SeaweedFS, FerretDB.
- 6 docker-compose files: chia theo concern (agents, pipelines, backfill).
- `configs/` là Jinja2 templates cho 16 service configs — duplicate effort với core.

### View 2.3 — Customer Project Container Diagram (CTC example)

**Mục đích**: Customer phức tạp hơn — có custom API.

```mermaid
C4Container
    title Container Diagram — aihub-ctc (Customer Project)

    System_Ext(aihub_core_sdk, "Swiss AI Hub Core SDK", "v0.274.3 git tag (older than bmd!)")
    System_Ext(jira_cloud, "Jira / Service Desk", "palsystem.atlassian.net")
    System_Ext(confluence_cloud, "Confluence", "Wiki source")
    System_Ext(sharepoint, "SharePoint", "Document source")
    System_Ext(azure_kv, "Azure Key Vault", "Secret store")
    System_Ext(aihub_platform, "aihub-core Platform", "Deployed separately")

    System_Boundary(ctc, "aihub-ctc (Customer Deployment)") {
        Container(chat_agent_svc, "Chat Agent", "FastAPI", "Main conversational")
        Container(jira_agent_svc, "Jira Issue Agent", "FastAPI", "Auto-respond Jira")
        Container(log_agent_svc, "Log Analysis Agent", "FastAPI", "Parse zip logs")
        Container(orchestrator_svc, "Retrieval Orchestrator", "FastAPI", "Multi-source RAG router")
        Container(custom_api, "CTC Custom API", "FastAPI", "Jira webhook + Support req")
        Container(jira_pipeline, "Jira Pipeline (2-stage)", "Dagster", "API→S3→Milvus")
        Container(confluence_pipeline, "Confluence Pipeline (2-stage)", "Dagster", "API→S3→Milvus")
        Container(sharepoint_pipeline, "SharePoint Pipeline (2-stage)", "Dagster", "API→S3→Milvus")
        ContainerDb(lib_common, "lib/common/", "Python lib", "Shared events, types, ops")
    }

    Rel(chat_agent_svc, lib_common, "Import")
    Rel(jira_agent_svc, lib_common, "Import")
    Rel(log_agent_svc, lib_common, "Import")
    Rel(orchestrator_svc, lib_common, "Import")
    Rel(custom_api, lib_common, "Import")
    Rel(lib_common, aihub_core_sdk, "⚠️ Vi phạm import: from swiss_ai_hub.core.events.agent (internal)")

    Rel(custom_api, jira_cloud, "Webhook receive")
    Rel(custom_api, jira_cloud, "Support Desk API")
    Rel(custom_api, azure_kv, "Fetch secrets")
    Rel(custom_api, aihub_platform, "NATS publish (Jira events)")

    Rel(jira_pipeline, jira_cloud, "Fetch issues")
    Rel(confluence_pipeline, confluence_cloud, "Fetch pages")
    Rel(sharepoint_pipeline, sharepoint, "Fetch docs")

    Rel(chat_agent_svc, orchestrator_svc, "AgentInTheLoop")
    Rel(orchestrator_svc, jira_agent_svc, "AgentInTheLoop")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Quan sát CTC**:

- 9 deployable containers (4 agents + 1 custom API + 3 pipelines + lib shared).
- **Có `lib/common/`** — pattern bmd KHÔNG có. Tốt cho code sharing trong cùng customer, nhưng raises câu hỏi tại sao
  không ở core.
- **Vi phạm import rule** (`lib/common/types/RetrievalAgentInTheLoop.py:1-4`).
- **Custom API** với 2 endpoints (Jira webhook + Support request) — không có ở bmd, không ở core.
- Tích hợp Azure Key Vault (enterprise-grade), bmd dùng .env files.
- Version SDK CŨ HƠN bmd (v0.274.3 vs v0.279.2).

______________________________________________________________________

## Level 3 — Component

### View 3.1 — `packages/core` Components

**Mục đích**: Zoom vào shared infrastructure package.

```mermaid
C4Component
    title Component Diagram — packages/core (shared infrastructure)

    Container_Ext(api, "API Gateway")
    Container_Ext(agents, "Agent Workers")
    Container_Ext(pipelines, "Pipeline Workers")
    Container_Ext(keycloak, "Keycloak")
    ContainerDb_Ext(nats, "NATS")
    ContainerDb_Ext(mongo, "FerretDB")
    ContainerDb_Ext(redis, "Valkey")

    Container_Boundary(core, "packages/core") {
        Component(auth_handlers, "Auth Handlers", "5 implementations", "Keycloak/Token/Bearer/OAuth2/OpenWebUI")
        Component(access_checker, "AccessChecker", "RBAC + ABAC", "Hierarchical permission template, tenant ceiling")
        Component(usage_limits, "UsageLimits", "❌ NOT WIRED", "Defined nhưng không enforce — DTC-1")
        
        Component(base_event, "BaseEvent", "Auto-registry", "Polymorphic deserialization via _event_registry")
        Component(publishers, "JSPublisher", "NATS publish", "UUID + Nats-Msg-Id, 60s dedup")
        Component(subscribers, "AbstractSubscriber", "NATS subscribe", "Ack-on-receive, no DLQ")
        Component(topics, "TopicManager", "Subject hierarchy", "Topic._topic_registry")
        Component(streams, "StreamManager", "JetStream config", "duplicate_window=60s, retention")
        
        Component(workflow, "DispatchableWorkflow", "Base class", "Used by Agent + Process (process dead)")
        Component(dispatcher, "BaseDispatcher", "Event-driven step exec", "Step replay from JetStream")
        Component(step_store, "StepStore", "Redis-backed", "MD5(events) idempotency key")
        
        Component(persistence, "Persistence", "MongoEngine", "Entity classes — version field unused (I5)")
        Component(rag_vectors, "RAG Vectors", "Milvus client wrapper", "PartitionAwareMilvusVectorStore — no upsert (DTC-4)")
        Component(rag_documents, "RAG Documents", "Document mgmt", "Hash-based ID")
        
        Component(forms, "Form System", "Pydantic + FormKit", "28 elements × 2 modes — high surface")
        Component(controller, "Controller", "FastAPI base", "Fluent builder, TenantScopedController")
        Component(routes, "Routes", "REST endpoints", "Inherits Controller")
        
        Component(otel, "OpenTelemetry", "Tracing", "SmartTracer, @trace_fn, NATSMessageHeaders")
        Component(langfuse_int, "Langfuse Integration", "LLM tracing", "Prompt/response, cost tracking")
        Component(health, "HealthController", "Liveness check", "⚠️ Không phân biệt readiness")
        
        Component(settings, "Pydantic Settings", "20+ classes", "MongoSettings, NatsSettings, etc.")
        Component(i18n, "LocaleHandler", "i18n", "DE/EN/FR/IT translations")
    }

    Rel(api, controller, "Inherits")
    Rel(api, auth_handlers, "DI")
    Rel(api, access_checker, "Permission check")

    Rel(agents, workflow, "Extends")
    Rel(agents, dispatcher, "Uses")
    Rel(agents, step_store, "Idempotency")
    Rel(agents, publishers, "Emit events")
    Rel(agents, subscribers, "Listen events")
    Rel(agents, rag_vectors, "Vector search")

    Rel(pipelines, rag_vectors, "Insert (no upsert)")
    Rel(pipelines, rag_documents, "Mgmt")

    Rel(publishers, nats, "JetStream API")
    Rel(subscribers, nats, "Pull/push")
    Rel(persistence, mongo, "ODM")
    Rel(step_store, redis, "Atomic ops")
    Rel(rag_vectors, mongo, "Metadata")

    Rel(auth_handlers, keycloak, "JWT verify, JWKS")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

**Critical components highlighted**:

- 🔴 `UsageLimits` — defined nhưng KHÔNG wire (DTC-1)
- 🔴 `PartitionAwareMilvusVectorStore` — không có upsert (DTC-4)
- 🔴 `AbstractSubscriber` — ack-on-receive, không có DLQ (I3)
- ⚠️ `Persistence` — `version` field exists nhưng không dùng (I5)
- ⚠️ `HealthController` — không phân biệt liveness/readiness
- ⚠️ `Form System` — 28 elements × 2 modes = 56 surfaces (maintenance cost)

### View 3.2 — `packages/agent` Components

**Mục đích**: Agent framework internals.

```mermaid
C4Component
    title Component Diagram — packages/agent (Agent Framework)

    Container_Ext(api, "API Gateway")
    ContainerDb_Ext(nats, "NATS")
    ContainerDb_Ext(redis, "Valkey")
    Container_Ext(litellm, "LiteLLM Proxy")

    Container_Boundary(agent_pkg, "packages/agent") {
        Component(agent_base, "Agent", "Extends DispatchableWorkflow", "Introspection: get_start/stop/hitl events")
        
        Component(step_decorator, "@step decorator", "Workflow building block", "params: name, precondition, max_executions, stop_on_error")
        Component(precondition, "@precondition", "Async callable→bool", "Gates step execution")
        
        Component(agent_dispatcher, "AgentDispatcher", "Step executor", "Replay events, MD5 idempotency check")
        Component(event_store, "JetStreamEventStore", "Durable event log", "Subscribe per execution_context")
        
        Component(run_context, "RunContext", "Redis-backed", "Per-run ephemeral, 30d TTL")
        Component(thread_context, "ThreadContext", "Redis-backed", "Per-thread persistent, no TTL")
        
        Component(displayer, "EventDisplayer", "DI", "Emit DisplayEvents for streaming UI")
        Component(memory, "AgentMemory", "mem0 integration", "User + org memory")
        Component(tracer, "AgentRunTracer", "OTEL + Langfuse", "Span per agent run")
        
        Component(mcp_client, "MCP Client Factory", "fastmcp>=3.0", "Discover + call MCP tools")
        Component(agent_itl, "AgentInTheLoop", "Sub-workflow", "AgentInTheLoopRequestEvent → wait StopEvent")
        Component(hitl, "HITL", "Human-In-The-Loop", "HumanInTheLoopRequestEvent")

        Container_Boundary(pre_built, "app/ - Pre-built Agents") {
            Component(rag_agent, "RAGAgent", "Multi-source retrieval + memory")
            Component(llm_wrap, "LLMWrappingAgent", "Simple 2-step LLM chat")
            Component(expert_ask, "ExpertAskingAgent", "HITL escalation Teams/Slack")
            Component(expert_rag, "ExpertRAGAgent", "RAG + HITL consent")
            Component(few_shot, "FewShotAgent", "Pattern matching + examples")
            Component(ns_select, "NamespaceSelectionAgent", "HITL namespace approval")
            Component(retrieval, "RetrievalAgent", "Pure retrieval (no LLM)")
            Component(mcp_react, "MCP_ReactAgent", "ReAct loop + MCP tools")
            Component(duy_wip, "DuyAgent (WIP)", "Under development")
        }
    }

    Rel(rag_agent, agent_base, "Extends")
    Rel(llm_wrap, agent_base, "Extends")
    Rel(expert_ask, agent_base, "Extends")
    Rel(expert_rag, agent_base, "Extends + uses AgentInTheLoop")
    Rel(few_shot, agent_base, "Extends")
    Rel(ns_select, agent_base, "Extends + HITL")
    Rel(retrieval, agent_base, "Extends")
    Rel(mcp_react, agent_base, "Extends + MCP")

    Rel(agent_base, step_decorator, "Decorate methods")
    Rel(step_decorator, precondition, "Optional gate")

    Rel(agent_dispatcher, event_store, "Replay")
    Rel(agent_dispatcher, run_context, "State")
    Rel(agent_dispatcher, thread_context, "State")

    Rel(rag_agent, displayer, "Stream")
    Rel(rag_agent, memory, "Recall")
    Rel(rag_agent, tracer, "Trace")

    Rel(mcp_react, mcp_client, "Tool calls")

    Rel(event_store, nats, "JetStream")
    Rel(run_context, redis, "Get/Set")
    Rel(thread_context, redis, "Get/Set")

    Rel(api, agent_base, "Trigger via NATS event")
    Rel(rag_agent, litellm, "LLM call")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Framework gaps highlighted** (xem 02_architecture_review_details.md §12):

- ❌ Không có `@step(timeout=...)` parameter
- ❌ Không có `@step(retry={"attempts": 3, "backoff": "exp"})` native
- ❌ Không có cron trigger event class
- ❌ Không có per-tenant MCP tool authorization layer

### View 3.3 — `packages/pipeline` Components

**Mục đích**: Dagster-based ingestion pipeline internals.

```mermaid
C4Component
    title Component Diagram — packages/pipeline (Dagster Pipelines)

    Container_Ext(rclone, "Rclone")
    Container_Ext(mineru, "MinerU API")
    Container_Ext(litellm, "LiteLLM (embedding)")
    ContainerDb_Ext(seaweedfs, "SeaweedFS S3")
    ContainerDb_Ext(milvus, "Milvus")
    ContainerDb_Ext(nats, "NATS")
    ContainerDb_Ext(mongo, "FerretDB")

    Container_Boundary(pipeline_pkg, "packages/pipeline") {
        Component(definitions_util, "definitions_util.py", "Factory", "default_definitions(), default_local_filesystem_to_datalake_definitions()")
        
        Container_Boundary(stage1, "Stage 1 — Source → Data Lake") {
            Component(obs_factory, "ObservableSourceFactory", "Asset factory", "Dynamic partitions by file URI")
            Component(rclone_resource, "RcloneResource", "Dagster resource", "Manage rclone client")
            Component(file_sensor, "FileSensor", "Polling 60s default", "Detect new files")
            Component(replace_partitions, "replace_partition_keys()", "Partition mgmt", "Max 1000 per tick — explosion risk DTC-10")
        }
        
        Container_Boundary(stage2, "Stage 2 — Data Lake → Vector Store") {
            Component(parse_op, "parse_document_op", "MinerU integration", "VLM parsing (no per-doc timeout)")
            Component(chunk_op, "chunk_md_structural", "MarkdownStructuralNodeParser", "Heading-based, no semantic/sliding")
            Component(embed_op, "embed_nodes", "LlamaIndex batch", "RetryPolicy(6, exp backoff). No explicit batch size — recursive bisection fallback")
            Component(milvus_write, "MilvusWriteOp", "Insert vectors", "❌ No upsert-by-doc-id (DTC-4)")
            Component(nats_sensor, "nats_document_uploaded_sensor", "Cross-pipeline trigger", "Triggers when file in S3")
        }
        
        Component(executor_factory, "executors/factory.py", "❌ in_process_executor", "Single-thread ops (DTC-6)")
        Component(io_managers, "IOManagers", "Asset persistence", "S3, Milvus")
        Component(automation_cond, "AutomationCondition.eager()", "Auto-materialize", "Triggered by upstream")
    }

    Rel(obs_factory, rclone_resource, "Use")
    Rel(rclone_resource, rclone, "RC API")
    Rel(file_sensor, replace_partitions, "Add new partition keys")
    Rel(obs_factory, seaweedfs, "Write parsed files")

    Rel(nats_sensor, nats, "Subscribe doc-uploaded")
    Rel(parse_op, mineru, "VLM call")
    Rel(parse_op, seaweedfs, "Read")
    Rel(chunk_op, parse_op, "Pipe")
    Rel(embed_op, chunk_op, "Pipe")
    Rel(embed_op, litellm, "Embedding call")
    Rel(milvus_write, milvus, "Insert (no upsert)")
    Rel(milvus_write, mongo, "Metadata")

    Rel(definitions_util, obs_factory, "Compose")
    Rel(definitions_util, executor_factory, "Use")
    Rel(definitions_util, automation_cond, "Use")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

**Critical issues highlighted**:

- 🔴 `executor_factory` dùng `in_process_executor` → all ops single-thread (DTC-6)
- 🔴 `MilvusWriteOp` không upsert-by-id → vector duplication (DTC-4)
- 🟠 `replace_partition_keys()` max 1000/tick → 1M files = DAG explosion (DTC-10)
- 🟠 `parse_op` không có per-document timeout — pipeline stuck on slow doc
- 🟠 `embed_op` không có explicit batch size — recursive bisection suboptimal

### View 3.4 — Customer Extension Points (Mapping)

**Mục đích**: Khi customer (bmd/ctc) extend core, họ extend những điểm nào.

```mermaid
graph LR
    subgraph "Core SDK (extension contracts)"
        Agent[Agent base class]
        Form[Form duality]
        Controller[Controller base]
        ATL[AgentInTheLoopRequestEvent]
        HITL[HumanInTheLoopRequestEvent]
        Step["@step decorator"]
        Precondition["@precondition decorator"]
        DefaultDefs[default_definitions]
        LocaleString[LocaleString i18n]
    end

    subgraph "aihub-bmd extensions"
        BMDAgent[BMDAgent ←]
        BMDConfig[BMDAgentConfig ←]
        SnkEvent[Custom SNK events ←]
        BMDPipelines[4 pipelines via DefaultDefs ←]
        BMD_i18n[DE/EN/FR/IT translations ←]
    end

    subgraph "aihub-ctc extensions"
        ChatAgent[ChatAgent ←]
        JiraAgent[JiraIssueAgent ←]
        OrchestratorAgent[RetrievalOrchestratorAgent uses ATL ←]
        LogAgent[LogAnalysisAgent ←]
        CTCEvents["lib/common/events (10 types) ←"]
        JiraController[JiraWebhookController ←]
        SupportController[SupportRequestController ←]
        CTCPipelines[6 pipelines via DefaultDefs ←]
    end

    Agent --> BMDAgent
    Agent --> ChatAgent
    Agent --> JiraAgent
    Agent --> OrchestratorAgent
    Agent --> LogAgent
    Form --> BMDConfig
    Controller --> JiraController
    Controller --> SupportController
    ATL --> OrchestratorAgent
    DefaultDefs --> BMDPipelines
    DefaultDefs --> CTCPipelines
    LocaleString --> BMD_i18n

    style BMDAgent fill:#e1f5ff
    style ChatAgent fill:#fff4e1
    style OrchestratorAgent fill:#fff4e1
```

**Quan sát extension patterns**:

| Extension type               | BMD usage      | CTC usage             |            Reusable?            |
| ---------------------------- | -------------- | --------------------- | :-----------------------------: |
| `Agent` base class           | 3 services     | 4 agents              |         ✅ Core pattern         |
| `AgentConfig (Form)`         | BMDAgentConfig | Multiple configs      |         ✅ Core pattern         |
| `Controller` base            | ❌ Không dùng  | 2 custom controllers  |           ⚠️ CTC-only           |
| `AgentInTheLoopRequestEvent` | ❌ Không dùng  | RetrievalOrchestrator | ✅ Core pattern (underutilized) |
| `HumanInTheLoopRequestEvent` | BMDAgent       | NamespaceSelection    |               ✅                |
| `default_definitions()`      | 4 pipelines    | 6 pipelines           |         ✅ Core pattern         |
| Custom events                | SNK events     | 10 event types        |       ⚠️ Pattern lặp lại        |
| i18n LocaleString            | DE/EN/FR/IT    | (chưa rõ scope)       |               ✅                |

**Insight quan trọng**: CTC's `RetrievalOrchestratorAgent` đang dùng đúng pattern `AgentInTheLoop` của core. Pattern
multi-agent orchestration NÊN được document rõ trong arc42 + extract example về `packages/agent/app/`.

______________________________________________________________________

## Dynamic Diagrams

### Dynamic 4.1 — Agent Workflow Execution (Happy Path)

**Scenario**: User gửi message qua OpenWebUI → RAGAgent xử lý.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant OW as OpenWebUI
    participant API as API Gateway
    participant NATS as NATS JetStream
    participant Agent as RAGAgent Worker
    participant Redis as Valkey (Step Store)
    participant Milvus as Milvus
    participant LLM as LiteLLM Proxy
    participant OTEL as OTEL Collector

    U->>OW: Chat message
    OW->>API: POST /api/v1/{tenant_id}/threads/{id}/messages
    API->>API: AuthHandler.authenticate (Keycloak JWT)
    API->>API: AccessChecker.has_access (tenant + permission)
    Note over API: ❌ UsageLimits không enforce here (DTC-1)
    API->>NATS: Publish StartEvent (UUID + Nats-Msg-Id, 60s dedup)
    API->>OTEL: Span "api.message.create"
    API-->>OW: 202 Accepted + thread_id

    NATS->>Agent: Deliver StartEvent
    Agent->>Redis: Step idempotency check (MD5 events hash)
    alt Step already executed
        Agent->>NATS: Ack, skip
    else New execution
        Agent->>Agent: @step precondition check
        Agent->>OTEL: Span "agent.step.retrieve"
        Agent->>Milvus: Vector search (namespace filter, 1023 partitions)
        Milvus-->>Agent: Top-K nodes
        Agent->>LLM: LLM completion (prompt + context)
        LLM-->>Agent: Streaming tokens
        Agent->>NATS: Publish DisplayEvent (token stream)
        Agent->>Redis: Store step state (counter, parameters hash)
        Agent->>NATS: Publish StopEvent
        Agent->>NATS: Ack original message
    end

    NATS->>OW: Stream DisplayEvents via SSE
    OW-->>U: Render tokens

    Note over OTEL: Trace context propagates via NATSMessageHeaders<br/>(api → agent → all downstream linked)
```

**Tracing**: ✅ End-to-end visible. **Idempotency**: ✅ Step execution dedup. **Gaps marked**: ❌ UsageLimits không check.

### Dynamic 4.2 — Document Ingestion Pipeline (2-Stage)

**Scenario**: File mới ở SharePoint → indexed vào Milvus.

```mermaid
sequenceDiagram
    autonumber
    participant SP as SharePoint
    participant Sensor as Dagster Sensor
    participant S1 as Stage 1 Pipeline
    participant S3 as SeaweedFS
    participant NATS as NATS
    participant Sensor2 as nats_document_uploaded_sensor
    participant S2 as Stage 2 Pipeline
    participant Parse as MinerU
    participant Embed as LiteLLM (embed)
    participant Milvus as Milvus

    Note over Sensor: Poll every 60s
    Sensor->>SP: List files
    SP-->>Sensor: New file metadata
    Sensor->>S1: Add partition key (max 1000/tick — DTC-10 risk)

    S1->>S1: in_process_executor (single-thread DTC-6)
    S1->>SP: Download file (via Rclone)
    SP-->>S1: File bytes
    S1->>S3: Upload to bucket
    S1->>NATS: Publish document-uploaded event

    NATS->>Sensor2: Trigger
    Sensor2->>S2: Materialize asset (per partition)

    S2->>S3: Read file
    S3-->>S2: Bytes
    S2->>Parse: VLM parse (no per-doc timeout)
    Parse-->>S2: Markdown text
    S2->>S2: Chunk (markdown structural — no semantic)
    S2->>Embed: Embedding batch (recursive bisection fallback)
    Embed-->>S2: Vectors
    S2->>Milvus: Insert (❌ no upsert — DTC-4)
    Note over Milvus: Re-ingest cùng doc = duplicate vectors

    S2->>NATS: Publish index-completed event
```

**Issues highlighted**:

- 🔴 DTC-6: `in_process_executor` → throughput limited
- 🔴 DTC-4: Milvus insert (no upsert) → vector duplication
- 🟠 DTC-10: Dynamic partitions per file → DAG explosion at scale
- 🟠 No per-doc timeout on MinerU
- 🟠 No explicit batch size on embedding

### Dynamic 4.3 — HITL (Human-In-The-Loop) Flow

**Scenario**: Agent gặp uncertain situation → escalate to expert.

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant Agent as ExpertRAGAgent
    participant NATS as NATS
    participant Bot as Bot Service
    participant Teams as MS Teams
    participant Expert as Domain Expert

    U->>Agent: Ambiguous query
    Agent->>Agent: @precondition - confidence < threshold
    Agent->>NATS: Publish HumanInTheLoopRequestEvent
    Note over Agent: Workflow PAUSED (waiting on response)

    NATS->>Bot: Deliver event
    Bot->>Teams: Post adaptive card with question
    Teams->>Expert: Notification

    Expert->>Teams: Click "Approve" / "Provide answer"
    Teams->>Bot: Callback
    Bot->>NATS: Publish HumanInTheLoopResponseEvent

    NATS->>Agent: Deliver response (via event replay)
    Agent->>Agent: Resume from paused step
    Agent->>NATS: Publish StopEvent + answer to user
```

**Strength**: HITL first-class trong framework. ✅

### Dynamic 4.4 — Multi-Agent Collaboration (AgentInTheLoop)

**Scenario**: CTC's RetrievalOrchestratorAgent routes query to multiple retrievers.

```mermaid
sequenceDiagram
    autonumber
    participant Chat as ChatAgent
    participant Orch as RetrievalOrchestratorAgent
    participant JA as JiraRetrievalAgent
    participant CA as ConfluenceRetrievalAgent
    participant SA as SharePointRetrievalAgent
    participant NATS as NATS

    Chat->>NATS: AgentInTheLoopRequestEvent(target=Orch, payload=question)
    NATS->>Orch: Deliver
    
    par Distribute to 3 sources
        Orch->>NATS: AgentInTheLoopRequestEvent(target=JA)
        NATS->>JA: Deliver
        JA->>NATS: AgentInTheLoopResponseEvent(jira_context)
    and
        Orch->>NATS: AgentInTheLoopRequestEvent(target=CA)
        NATS->>CA: Deliver
        CA->>NATS: AgentInTheLoopResponseEvent(confluence_context)
    and
        Orch->>NATS: AgentInTheLoopRequestEvent(target=SA)
        NATS->>SA: Deliver
        SA->>NATS: AgentInTheLoopResponseEvent(sharepoint_context)
    end

    Note over Orch: @precondition all_responses_received
    Orch->>Orch: Consolidate 3 contexts
    Orch->>NATS: CombinedResponsesEvent
    NATS->>Chat: Deliver
    Chat->>Chat: Resume with consolidated context

    Note right of Chat: Pattern này nên<br/>được extract về core<br/>như reference example
```

**Insight**: CTC built pattern này custom, nhưng dùng đúng core primitives (`AgentInTheLoopRequestEvent`). Core nên
document rõ và provide example.

### Dynamic 4.5 — Failure Scenario (Poison Message Without DLQ)

**Scenario**: Một event gây handler crash repeatedly.

```mermaid
sequenceDiagram
    autonumber
    participant Producer as API
    participant NATS as JetStream
    participant Sub as JSSubscriber
    participant Handler as AgentDispatcher
    participant Logs as Logs

    Producer->>NATS: Publish malformed event
    NATS->>Sub: Deliver
    Sub->>Sub: Deserialize OK
    Sub->>NATS: Ack (ack-on-receive policy)
    Note over Sub: ❌ Already ack'd — không retry được

    Sub->>Handler: Process async
    Handler->>Handler: Step execution fails
    Handler->>Logs: Log exception
    Note over Handler: Workflow stuck<br/>No DLQ to investigate later<br/>No automated alert (I3)

    Producer->>NATS: Same malformed event (retry)
    NATS->>Sub: Deliver
    Note over Sub: Within 60s dedup window<br/>→ Filtered. But if >60s, re-delivered, crash again.
```

**Gap I3**: JSSubscriber ack-on-receive policy means poison messages silently fail. Need DLQ implementation.

______________________________________________________________________

## Deployment Diagram

### View 5.1 — Current Single-Host Deployment

```mermaid
graph TB
    subgraph "Internet"
        Users[End Users]
        Devs[Developers]
    end

    subgraph "Single Production Host (per customer)"
        Traefik[Traefik :443]
        
        subgraph "Proxy Network"
            Traefik
            OW[OpenWebUI :8080]
            AdminUI[Admin UI :3333]
            API[FastAPI :8000]
        end
        
        subgraph "Backend Network"
            Agents[Agent Workers x N]
            Pipelines[Pipeline Workers x N]
            Bot[Bot Service]
            LiteLLM[LiteLLM Proxy :4000]
            Backup[Backup Dagster]
            Langfuse[Langfuse]
        end
        
        subgraph "Data Network"
            PG[(PostgreSQL :5432)]
            FerretDB[(FerretDB :27017)]
            Milvus[(Milvus :19530)]
            Neo4j[(Neo4j :7687)]
            Valkey[(Valkey :6379)]
            NATS[NATS :4222]
            ETCD[(etcd)]
        end
        
        subgraph "Storage Network"
            SeaweedM[SeaweedFS Master]
            SeaweedV[SeaweedFS Volume]
            SeaweedF[SeaweedFS Filer]
            SeaweedS3[SeaweedFS S3 :9000]
        end
        
        subgraph "Egress Network"
            Keycloak_KC[Keycloak]
            MinerU[MinerU API]
        end
        
        subgraph "Volumes (Local Disk)"
            Volumes["./docker-volumes/<br/>❌ Not encrypted at rest (G3.3)"]
        end
    end
    
    subgraph "External"
        KC_External[Keycloak SaaS]
        LiteLLM_Cloud[Swiss LLM Cloud]
        Sources[SharePoint/Jira/Confluence]
        AzureKV[Azure Key Vault]
    end

    Users -->|HTTPS| Traefik
    Devs -->|HTTPS Admin| Traefik
    
    Traefik --> OW
    Traefik --> AdminUI
    Traefik --> API
    
    API --> Agents
    API --> NATS
    API --> FerretDB
    API --> Valkey
    
    Agents --> NATS
    Agents --> Milvus
    Agents --> LiteLLM
    
    Pipelines --> Milvus
    Pipelines --> SeaweedS3
    Pipelines --> LiteLLM
    
    LiteLLM --> LiteLLM_Cloud
    Agents --> KC_External
    Pipelines --> Sources
    
    PG --- FerretDB
    Milvus --- ETCD
    SeaweedF --- ETCD
    
    Backup --> Volumes
    All_DBs[All DBs] --> Volumes

    style Volumes fill:#ffcccc
    style API fill:#ffe6cc
```

**Critical issues highlighted in deployment**:

- 🔴 **Single host** = single point of failure (G6.1)
- 🔴 **Volumes không encrypt** at rest (G3.3)
- 🔴 **Tất cả stateful single instance** — no HA
- 🟠 **NATS single node** — không cluster
- 🟠 **No K8s** — không có Helm chart (G5.5)
- 🟠 **No resource limits** trong docker-compose

### View 5.2 — Network Zones (Defense in Depth)

```mermaid
flowchart TB
    Internet([Internet])
    
    subgraph proxy["proxy network (DMZ)"]
        Traefik
        OW2[OpenWebUI]
        Adm[Admin UI]
    end
    
    subgraph backend["backend network (app tier)"]
        API2[FastAPI]
        Ag2[Agents]
        Bot2[Bot]
        Pipe2[Pipelines]
    end
    
    subgraph data["data network (data tier)"]
        Mongo2[(FerretDB)]
        Vec[(Milvus)]
        Cache[(Valkey)]
        Stream[NATS]
        Graph[(Neo4j)]
        PG2[(PostgreSQL)]
    end
    
    subgraph storage["storage network (object tier)"]
        SeaweedAll[SeaweedFS cluster]
    end
    
    subgraph egress["egress network (outbound)"]
        IntCom[inter_container_communication: false]
    end
    
    Internet --> proxy
    proxy --> backend
    backend --> data
    backend --> storage
    backend -.->|outbound only| egress
    egress --> Internet
    
    style proxy fill:#ffe6e6
    style backend fill:#fff4e6
    style data fill:#e6f4ff
    style storage fill:#e6ffe6
    style egress fill:#f0e6ff
```

**5 Docker networks** (ADR `2026_01_22_docker_network_isolation`):

| Network   | Purpose                                 | Note                                   |
| --------- | --------------------------------------- | -------------------------------------- |
| `proxy`   | DMZ — TLS termination, external ingress | Traefik mounted here                   |
| `backend` | App tier — stateless services           | Agents, API, Bot, Pipelines            |
| `data`    | Data tier — DBs, cache, broker          | Restricted access                      |
| `storage` | Object storage cluster                  | SeaweedFS only                         |
| `egress`  | Outbound to internet                    | `inter_container_communication: false` |

**Strength**: ✅ Network isolation good (defense in depth). **Gap**: ⚠️ Service-to-service auth bên trong network không
mTLS (DTC-9).

______________________________________________________________________

## Multi-Customer Topology View

### View 6.1 — Hiện tại — Per-Customer Stack

```mermaid
flowchart TB
    subgraph customer_a["Customer A (e.g., aihub-bmd)"]
        A_All[Toàn bộ stack 30+ containers<br/>aihub-core v0.279.2<br/>1 host, 1 set DBs]
    end
    
    subgraph customer_b["Customer B (e.g., aihub-ctc)"]
        B_All[Toàn bộ stack 30+ containers<br/>aihub-core v0.274.3<br/>1 host, 1 set DBs<br/>+ Custom API]
    end
    
    subgraph customer_n["Customer N (future)"]
        N_All[Toàn bộ stack lặp lại<br/>aihub-core v?.?.?<br/>1 host, 1 set DBs]
    end
    
    subgraph shared["Shared / External"]
        SLC[Swiss LLM Cloud]
        KCSaaS[Keycloak SaaS<br/>chia sẻ realms]
        Repo[(GitHub aihub-core<br/>git tag references)]
    end
    
    customer_a -->|LLM API| SLC
    customer_b -->|LLM API| SLC
    customer_n -->|LLM API| SLC
    
    customer_a -.->|OIDC| KCSaaS
    customer_b -.->|OIDC| KCSaaS
    customer_n -.->|OIDC| KCSaaS
    
    customer_a -.->|git clone tag| Repo
    customer_b -.->|git clone tag| Repo
    customer_n -.->|git clone tag| Repo
    
    style customer_a fill:#e1f5ff
    style customer_b fill:#fff4e1
    style customer_n fill:#f5e1ff
```

**Vấn đề**:

- 🔴 Chi phí vận hành tuyến tính theo số customers.
- 🔴 Version drift không kiểm soát.
- 🔴 Mỗi customer = 30+ containers tự quản — operational burden.
- 🔴 Không có shared resource (Milvus, Mongo, NATS) → wasted capacity.

### View 6.2 — Target — Shared Multi-Tenant SaaS (H3 vision)

```mermaid
flowchart TB
    subgraph shared_cluster["Shared K8s Cluster"]
        subgraph tenant_a["Tenant A namespace"]
            A_App[App pods<br/>tenant_id=a]
        end
        
        subgraph tenant_b["Tenant B namespace"]
            B_App[App pods<br/>tenant_id=b]
        end
        
        subgraph tenant_n["Tenant N namespace"]
            N_App[App pods<br/>tenant_id=n]
        end
        
        subgraph shared_data["Shared Data Layer"]
            NATSCluster["NATS cluster<br/>Subject: aihub.tenant.{id}.*"]
            MilvusCluster["Milvus cluster<br/>Collection: {tenant_id}__logical"]
            MongoCluster["Mongo replica set<br/>tenant_id field index"]
            ValkeyCluster["Valkey cluster<br/>Key prefix: tenant:{id}:"]
            SeaweedCluster["SeaweedFS cluster<br/>Bucket: tenant-{id}-*"]
        end
        
        subgraph control_plane["Control Plane"]
            Provisioner[Tenant Provisioning API]
            QuotaMgr[Quota Manager]
            CostAttr[Cost Attribution per tenant]
        end
    end
    
    tenant_a --> shared_data
    tenant_b --> shared_data
    tenant_n --> shared_data
    
    control_plane --> tenant_a
    control_plane --> tenant_b
    control_plane --> tenant_n
    
    style shared_data fill:#ccffcc
    style control_plane fill:#ccccff
```

**Để đạt được target**:

| Component           | Current state                       | Target state                   | Gap          |
| ------------------- | ----------------------------------- | ------------------------------ | ------------ |
| NATS subjects       | Flat hierarchy                      | `aihub.tenant.{id}.*`          | G1.1 part 1  |
| Mongo entities      | No tenant_id                        | Required tenant_id + index     | G1.1 part 2  |
| Milvus collections  | Single collection, NAMESPACE filter | Per-tenant collection          | G1.1 part 3  |
| Valkey keys         | Mixed                               | Prefix per tenant              | G1.1 part 4  |
| Resource quotas     | None                                | Per-tenant CPU/mem/storage/LLM | New ADR      |
| Tenant provisioning | Manual Keycloak + Mongo             | API + automation               | G1.3         |
| Cost attribution    | LiteLLM tracks per-call             | Per-tenant aggregate + cap     | DTC-1 part 2 |

______________________________________________________________________

## Future-State Target Architecture

### View 7.1 — Architecture sau H1 + H2 (6 tháng)

```mermaid
C4Container
    title Target Container Diagram — After H1+H2 (6 months)

    Person(user, "User")

    System_Boundary(aihub, "Swiss AI Hub (Production-Hardened)") {
        Container(traefik, "Traefik + RBAC Filter", "✅ NEW: OpenWebUI agent visibility filter")
        Container(api, "API Gateway", "FastAPI", "✅ UsageLimits middleware wired")
        Container(agents, "Agent Workers (K8s pods)", "Python", "✅ Horizontal scaling formalized")
        Container(pipelines, "Pipeline Workers", "Dagster", "✅ multiprocess_executor + temporal partitions")
        Container(audit, "Audit Service", "NEW: write-once log", "✅ All admin/user mutations")
        Container(presidio, "Presidio Anonymizer", "NEW or removed claim", "✅ PII scrub before LLM")
        Container(migrations, "Migration Runner", "NEW: versioned scripts", "✅ DB schema versioning")
        Container(dlq, "DLQ Consumer", "NEW: NATS DLQ", "✅ Poison message investigation")

        ContainerDb(milvus_cluster, "Milvus Cluster", "3+ queryNodes", "✅ Per-tenant collections")
        ContainerDb(mongo_replica, "Mongo Replica Set", "Replicated", "✅ tenant_id indexed")
        ContainerDb(valkey_cluster, "Valkey Cluster", "HA + sharded", "✅ Per-tenant key prefix")
        ContainerQueue(nats_cluster, "NATS Cluster", "3 nodes", "✅ Subject: aihub.tenant.{id}.*")
        ContainerDb(seaweed_cluster, "SeaweedFS Cluster", "3+ volume servers, replication=002", "✅ HA")
    }

    System_Ext(grafana, "Grafana", "NEW: Dashboards + SLO alerts")
    System_Ext(secrets_vault, "Secrets Vault", "NEW: rotation automation")

    Rel(user, traefik, "HTTPS")
    Rel(traefik, api, "")
    Rel(api, audit, "Log mutations")
    Rel(api, presidio, "Scrub before LLM")
    Rel(agents, dlq, "Failed messages")
    Rel(api, grafana, "Metrics emit")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

**Bổ sung sau H1+H2**:

- ✅ Audit Service (DTC-2)
- ✅ Presidio integration (DTC-3) HOẶC remove claim
- ✅ Migration Runner (G4.1)
- ✅ DLQ Consumer (I3)
- ✅ Milvus cluster mode (DTC-7)
- ✅ NATS cluster với tenant subjects (G1.1)
- ✅ Mongo replica set với tenant_id index (G1.1)
- ✅ Valkey cluster (sharding + HA)
- ✅ SeaweedFS HA (replication=002)
- ✅ Grafana + AlertManager
- ✅ Secrets Vault với rotation

### View 7.2 — Quick Reference: Containers Khác Biệt

| Container          | Hôm nay           | Sau H1 (3m)                    | Sau H2 (6m)               | Sau H3 (12m)              |
| ------------------ | ----------------- | ------------------------------ | ------------------------- | ------------------------- |
| Milvus             | Standalone        | Standalone (DISKANN benchmark) | Cluster mode              | Cluster + cross-region    |
| NATS               | Single node       | Single node + DLQ              | Cluster (3 nodes)         | Cluster + cross-region    |
| Mongo              | Single (FerretDB) | Single + tenant_id index       | Replica set               | Sharded by tenant_id      |
| Valkey             | Single            | Single                         | Cluster (HA)              | Cluster (HA + sharding)   |
| SeaweedFS          | replication=000   | replication=000                | Cluster + replication=002 | Cross-region async        |
| Pipelines executor | in_process        | multiprocess                   | multiprocess + Celery     | K8s Jobs                  |
| Audit Service      | ❌                | ✅ New                         | ✅ + Compliance           | ✅ + Real-time alerts     |
| Migration Runner   | ❌                | ✅ New                         | ✅ Mature                 | ✅ Auto-migrate on deploy |
| DLQ Consumer       | ❌                | ✅ New                         | ✅ + UI                   | ✅ + Auto-retry           |
| Presidio           | ❌ Claim only     | ✅ Integrated OR removed       | ✅                        | ✅ Multi-language         |

______________________________________________________________________

## Tổng kết Phase 3

### Deliverables đã tạo

| #   | Diagram                        | Mục đích                            |
| --- | ------------------------------ | ----------------------------------- |
| 1   | System Context                 | Actors + external systems           |
| 2.1 | Platform Container             | Tất cả containers Swiss AI Hub      |
| 2.2 | aihub-bmd Container            | Customer A consume SDK              |
| 2.3 | aihub-ctc Container            | Customer B consume SDK + custom API |
| 3.1 | `packages/core` Components     | Shared infrastructure internals     |
| 3.2 | `packages/agent` Components    | Agent framework internals           |
| 3.3 | `packages/pipeline` Components | Pipeline internals                  |
| 3.4 | Extension Points Mapping       | Customer extends core như thế nào   |
| 4.1 | Dynamic: Agent Workflow        | Happy path end-to-end               |
| 4.2 | Dynamic: Document Ingestion    | 2-stage pipeline với gaps marked    |
| 4.3 | Dynamic: HITL Flow             | Human-in-the-loop                   |
| 4.4 | Dynamic: Multi-Agent Collab    | CTC's orchestrator pattern          |
| 4.5 | Dynamic: Failure (Poison Msg)  | Gap analysis I3                     |
| 5.1 | Deployment: Current            | Single-host topology                |
| 5.2 | Deployment: Network Zones      | 5 Docker networks                   |
| 6.1 | Multi-Customer: Current        | Per-customer stack                  |
| 6.2 | Multi-Customer: Target         | Shared SaaS vision                  |
| 7.1 | Future: After H1+H2            | Target architecture 6 months        |
| 7.2 | Future: Container delta        | Container progression table         |

### Liên kết với assessment

Mỗi diagram đều tham chiếu tới gaps được identify trong
[02_architecture_review_details.md](02_architecture_review_details.md):

- Container 2.1 highlight các stateful single instances (G6.x)
- Component 3.1 marks DTC-1, DTC-4, I3, I5
- Dynamic 4.2 marks DTC-6, DTC-4, DTC-10
- Dynamic 4.5 illustrates I3 (no DLQ)
- Deployment 5.1 marks G3.3, G6.1, G5.5

### Render diagrams

Tất cả diagrams dùng Mermaid syntax. Render được trong:

- VitePress (đã setup trong `docs/.vitepress/config.mts`)
- GitHub markdown preview
- VS Code Markdown Preview Mermaid Support extension
- mermaid.live (online editor)

### Tiếp theo

- **Phase 4**: arc42 multi-customer view (12 chapters bằng tiếng Việt)
- **Phase 5**: 15 Proposed ADRs cho critical gaps
- **Phase 6**: Executive Summary + Index page

______________________________________________________________________

**Phiên bản**: 1.0 — 2026-05-25 **Liên kết**:

- [02_architecture_review_details.md](02_architecture_review_details.md) — Architecture review chi tiết
- [05_proposed_adrs/](05_proposed_adrs/) — Proposed ADRs
