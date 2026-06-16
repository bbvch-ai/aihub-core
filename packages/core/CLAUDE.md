# packages/core - Foundational Shared Library

**Purpose**: Shared infrastructure library used by ALL Swiss AI Hub services. Code belongs here if used by 2+ services.
Three major systems: event-driven architecture (Swiss AI Agent Protocol), authentication/authorization, and AI/ML
utilities. NOT for service-specific business logic — that belongs in `packages/agent`, `packages/process`,
`packages/pipeline`, etc.

## Folder Structure

```
packages/core/swiss_ai_hub/core/
├── agents/                          # Agent config base + workflow visualization
│   ├── agent_config.py               # Base config class (Form duality pattern)
│   ├── agent_ref.py                  # Agent instance reference
│   └── visualizers/types/           # Workflow graph types (NodeData, EdgeData, WorkflowGraph)
├── auth/                            # Authentication & authorization
│   ├── access/access_checker.py      # Permission matching engine (hierarchical wildcards)
│   ├── dependencies/                # Auth handlers (AuthHandler → OAuth2, Token, Bearer, OpenWebUI, DevOnly)
│   └── identity/                    # Identity models (UserIdentity, TenantIdentity)
├── context/                         # Context utilities
├── dependencies/                    # NATS client dependency injection (use_nats)
├── dispatcher/                      # Workflow orchestration
│   ├── base_dispatcher.py            # Abstract: event routing, step execution, state management
│   └── stores/                      # JetStreamEventStore (event replay), StepStore (Redis)
├── displayers/                      # Real-time event emission for UI streaming
│   ├── event_displayer.py            # Core: display_chunk(), display_thought(), display_llm_stream()
│   ├── stream/stream_processor.py    # Buffers output by ContentType (REGULAR/THINKING)
│   ├── parser/tag_parser.py          # Parses <think>...</think> tags from LLM output
│   └── buffer/stream_buffer.py       # Auto-flush on sentence boundaries or size thresholds
├── distributor/                     # External event distributors (agent + process)
├── events/                          # Event type hierarchy (~100 event types)
│   ├── base_event.py                 # Root: auto-registry, polymorphic deserialization
│   ├── utils.py                     # Event utility functions
│   ├── discovery/                   # Shared discovery (ClassDiscoveryRequestEvent, EventSpecs)
│   ├── agent/                       # Agent-scoped events
│   │   ├── control_and_display_event.py
│   │   ├── aitl/                    # Agent-in-the-loop delegation events
│   │   ├── bitl/                    # Bot-in-the-loop integration events
│   │   ├── common/                  # Common agent events (LimitChatHistory, StandaloneQuestionCondenser)
│   │   ├── control/                 # ControlEvent, StartEvent, StopEvent, ExceptionEvent
│   │   ├── cost/                    # CostEvent, LLMCostEvent
│   │   ├── discovery/               # Agent discovery events
│   │   ├── display/                 # DisplayEvent, ChunkEvent, ThoughtEvent
│   │   ├── guard/                   # Guard acceptance/rejection events
│   │   ├── hitl/                    # Human-in-the-loop request/response events
│   │   ├── memory/                  # Memory operation events (retrieve, store, history)
│   │   ├── router/                  # LLM routing events
│   │   ├── semantic/                # SemanticEvent + OpenInference tracing subtypes
│   │   └── user/                    # UserMessageEvent
│   ├── process/                     # Process-scoped events
│   │   ├── process_event.py          # Process orchestration base
│   │   ├── start/, stop/, exception/ # Process lifecycle events
│   │   ├── work/                    # WorkEvent: Agent, Human, Process, Program
│   │   ├── work_request/            # WorkRequestEvent: Agent, Human, Program
│   │   └── discovery/               # Process discovery events
│   └── pipeline/                    # Pipeline events (SourceUpdatedEvent)
├── form/                            # Form system (Form duality, FormkitElement, PrimeVueElement, 28 elements)
│   ├── form.py                      # Form base class with duality pattern
│   ├── base/                        # FormkitElement, PrimeVueElement bases
│   └── elements/                    # 28 concrete form elements
├── generative_ai/                   # AI/ML utilities
│   ├── chat_history/                # Chat history management + memory extension
│   ├── document/                    # Loaders (MinerU, DocumentIntelligence), parsers, refinement
│   ├── evaluation/                  # LLM evaluation
│   ├── guards/                      # Guard implementations (PII, context, confidence, few-shot)
│   ├── memory/                      # AgentMemory (user + org scoped via mem0)
│   ├── processors/                  # Post-processors (ParentSummary, PrevNext, ScoreScaler)
│   ├── prompting/                   # Few-shot examples, language detection
│   ├── rerank/                      # Reranking via LiteLLM (provider-agnostic)
│   ├── resources/                   # LLMConfig, EmbeddingModelConfig, RerankingModelConfig
│   ├── retrieval/                   # RAG: retrieve_nodes, condense_question, combine_nodes
│   ├── retrievers/                  # KnowledgeRetriever (Milvus), BaseRetriever
│   ├── routing/                     # LLM-based event routing
│   └── utils/                       # Shared AI utilities
├── i18n/                            # Internationalization
│   ├── locale_string.py              # Multi-language container (de, en, fr, it)
│   ├── locale_handler.py             # Runtime locale resolution with fallback chains
│   └── translations/                # YAML files: {scope}/{name}.{locale}.yml
├── mcp/                             # MCP client configuration (McpClientConfig StepConfig)
├── infrastructure/                  # External service settings (Pydantic BaseSettings)
│   ├── api/                         # AIHubSettings (buckets, CORS, OpenAI endpoint)
│   ├── nats/                        # NatsSettings (broker connection)
│   ├── mongo/                       # MongoSettings (FerretDB connection)
│   ├── redis/                       # RedisSettings (Valkey connection)
│   ├── milvus/                      # MilvusSettings (vector DB)
│   ├── s3/                          # S3StorageSettings (SeaweedFS)
│   ├── neo4j/                       # Neo4jSettings (graph DB)
│   ├── langfuse/                    # LangfuseSettings + LangfuseProvisioner
│   ├── litellm/                     # LiteLLMProxySettings + LiteLLMService
│   ├── opentelemetry/               # SmartTracer + trace_fn decorator
│   ├── logging/                     # Logging setup (enable_logging())
│   ├── mineru/                      # MineruSettings (document parsing)
│   ├── rclone/                      # RcloneSettings (cloud sync)
│   ├── mem0/                        # Long-term memory settings
│   ├── sharepoint/                  # SharePointSettings
│   └── azure_*/                     # Azure Cognitive Services, Data Lake
├── persistence/                     # Database abstractions (MongoEngine ODM)
│   ├── access/                      # RoleEntity, TenantMetadataEntity, UserTenantRoleEntity
│   ├── agents/                      # AgentConfigEntity
│   ├── process/                     # ProcessConfigEntity
│   ├── messaging/                   # ThreadEntity, PersistedAgentEventEntity, PersistedProcessEventEntity
│   ├── user/                        # UserDashboardEntity (user dashboard config)
│   ├── i18n/                        # LocaleStringEntity
│   ├── rag/                         # RAG document persistence
│   └── notification/                # NotificationEntity
├── polling/                         # JSPoller (JetStream batch consumption)
├── processes/                       # Process config base (process_config.py)
├── publishers/                      # JSPublisher (JetStream, durable) + NCPublisher (NATS Core, ephemeral)
├── records/                         # Record types
├── requester/                       # RPC request side (AbstractRequester, NCRequester)
├── responder/                       # RPC response side (AbstractResponder, NCResponder)
├── routes/                          # FastAPI base controllers
│   ├── controller.py                # Abstract: base_route, auth DI, permission templates, OTEL spans
│   └── health/                      # HealthController, HealthServer, health checks
├── rpc/                             # AgentConfigClient, ProcessConfigClient (request-reply)
├── runners/                         # Execution runners
├── settings/                        # App-level configuration (EnvironmentSettings)
├── streams/                         # StreamManager (JetStream stream lifecycle)
├── subscribers/                     # JSSubscriber + NCSubscriber + agent/process specializations
├── testing/                         # Testing utilities
│   ├── asyncio_utils/bdd.py         # @async_test decorator for async pytest-bdd
│   ├── auth_utils/                  # fake_user(), user_mocks, role_mocks, OAuth2 test utils
│   └── route_adapter/asgi_adapter.py # ASGI adapter for testing FastAPI routes
├── topic_managers/                  # Subject string builders (Agent, Process, Pipeline)
├── topics/                          # NATS subject structures (auto-registry, polymorphic parsing)
├── tracing/                         # NATSMessageHeaders (OTEL trace context propagation)
└── workflow/                        # Dispatchable workflow system
    ├── dispatchable_workflow.py      # Base class for agents/processes (@step annotations)
    └── annotations/                 # Step annotation extractors
```

## Import Convention

Two rules govern imports, depending on where the import happens:

**Within `packages/core`** — always use fully qualified direct paths to the source file:

```python
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.process.work.agent.agent_work_event import AgentWorkEvent
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.publishers.js_publisher import JSPublisher
```

**From other packages** (`packages/agent`, `packages/api`, etc.) — always import through `__init__.py` public interface:

```python
from swiss_ai_hub.core.events.agent import StartEvent, ChunkEvent
from swiss_ai_hub.core.events.process import WorkEvent, ProcessStartEvent
from swiss_ai_hub.core.publishers import JSPublisher
```

Each top-level directory has a lazy `__init__.py` with `TYPE_CHECKING` + `__getattr__` that provides the public
interface without eager loading.

## Event System (CRITICAL)

The heart of swiss_ai_hub.core. All inter-service communication uses events from this hierarchy. Understanding Control
vs Display separation is essential for working with any service.

### Auto-Registration

Events, Forms, and Topics all use `__pydantic_init_subclass__` to auto-register in class-level registries:

- `BaseEvent._event_registry` — enables `BaseEvent.deserialize_event(data)` for polymorphic deserialization
- `Form._form_registry` — enables form lookup by name
- `Topic._topic_registry` — enables `Topic.from_subject(subject)` for subject parsing

**Important**: Event sub-package `__init__.py` files MUST NOT eagerly import event classes. Eager barrel imports cause
duplicate registration errors via `__pydantic_init_subclass__`. Use the lazy `__getattr__` pattern instead.

### Event Hierarchy

```
BaseEvent (root — auto-registry, sequence numbering, trace dict)  [events/base_event.py]
│
├── ControlEvent (drives workflow execution)                       [events/agent/control/]
│   └── ProcessEvent (process orchestration)                       [events/process/]
│       ├── WorkEvent (signals work completion)                    [events/process/work/]
│       │   ├── AgentWorkEvent[TEvent: StopEvent]
│       │   ├── HumanWorkEvent
│       │   ├── ProgramWorkEvent
│       │   └── ProcessWorkEvent
│       └── WorkRequestEvent (delegates work)                      [events/process/work_request/]
│           ├── AgentWorkRequestEvent
│           ├── HumanWorkRequestEvent
│           └── ProgramWorkRequestEvent
│
├── DisplayEvent (UI/monitoring ONLY)                              [events/agent/display/]
│   ├── ChunkEvent (streaming LLM output)
│   └── ThoughtEvent (reasoning transparency)
│
├── ControlAndDisplayEvent (dual purpose)                          [events/agent/control_and_display_event.py]
│   ├── StartEvent, StopEvent (workflow lifecycle)                 [events/agent/control/]
│   ├── HumanInTheLoopRequest/Response (HITL)                     [events/agent/hitl/]
│   ├── AgentInTheLoopRequest/Response (AITL)                     [events/agent/aitl/]
│   ├── BotInTheLoopRequest/Response (BITL)                       [events/agent/bitl/]
│   ├── SemanticEvent (OpenInference tracing)                     [events/agent/semantic/]
│   │   ├── LLMEvent, RetrieverEvent, EmbeddingEvent
│   │   ├── RerankerEvent, ToolEvent, ChainEvent
│   │   ├── GuardEvent, AgentEvent
│   │   └── ExceptionEvent
│   └── MetaQuestionDetectedEvent (meta-question classification)  [events/agent/self_awareness/]
│
├── ControlEvent (drives workflow execution)
│   └── NotAMetaQuestionEvent (all-clear gate for normal pipeline) [events/agent/self_awareness/]
│
├── UserMessageEvent (chat-UI contract — DO NOT subclass for domain data) [events/agent/user/]
├── CostEvent / LLMCostEvent (billing)                            [events/agent/cost/]
└── Discovery events                                               [events/agent/discovery/, events/process/discovery/]
```

### Event Directory Scoping

Events are organized by which system they belong to:

| Scope                 | Directory                      | What belongs here                                                                   |
| --------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| Agent events          | `events/agent/`                | All agent workflow events (control, display, HITL, etc.)                            |
| Process events        | `events/process/`              | Process orchestration, work delegation, process discovery                           |
| Pipeline events       | `events/pipeline/`             | Data pipeline events (SourceUpdatedEvent)                                           |
| Self-awareness events | `events/agent/self_awareness/` | Meta-question detection gate (`MetaQuestionDetectedEvent`, `NotAMetaQuestionEvent`) |
| Shared base classes   | `events/`                      | BaseEvent, shared discovery (ClassDiscoveryRequestEvent)                            |

### Creating a New Event

1. Choose the correct base class from the hierarchy above
2. Place in `events/agent/`, `events/process/`, or `events/pipeline/` based on scope
3. Auto-registers on import — no manual registration needed
4. Do NOT add eager imports to any `__init__.py` — this causes duplicate registration errors
5. If the event subclasses any type already in the `DisplayEvents` union
   (`packages/api/.../contextualized_agent_event.py`), add the new subclass to the union too — otherwise it silently
   downcasts during WebSocket serialization (see `packages/api/CLAUDE.md` → DisplayEvents union)

## Form System (Form Duality Pattern)

Located at `core/form/` (not under events — forms are independent of the event system).

The Form system enables a single Pydantic model to serve two purposes:

**Form mode** (rendering): Field values are `FormkitElement` instances. Call `to_formkit_form()` to extract a list of
form elements for the frontend (FormKit + PrimeVue rendering).

**Data mode** (submission): Field values are plain Python types. Standard Pydantic validation applies.

The duality is achieved through union types:

```python
class MyConfig(Form):
    name: Annotated[str | InputText, Field(description="Agent name")]
    model: Annotated[str | ModelSelect, Field(description="LLM model")]
    enabled: Annotated[bool | Checkbox, Field(description="Enable feature")]
```

### Key Form Methods

- `to_formkit_form()` — extracts FormkitElement instances, auto-assigns IDs, wraps nested Forms in Groups
- `to_form_submission_model()` — creates Pydantic model with FormkitElement types stripped from unions
- `to_configurable_submission_model()` — instance-based, includes only fields with FormkitElement values
- `deep_merge()` — merges non-configurable base values with form submission data
- `get_configurable_fields()` / `get_non_configurable_fields()` — separates editable from fixed fields

### Element Hierarchy

`FormkitElement` → `PrimeVueElement` → 28 concrete elements:

InputText, Textarea, InputNumber, InputMask, Password, InputOtp, Checkbox, ToggleSwitch, ToggleButton, RadioButton,
Select, MultiSelect, Listbox, CascadeSelect, SelectButton, DatePicker, ColorPicker, Rating, Knob, Slider, Group (nested
forms), Repeater (arrays), LocaleInput (multi-language), AgentSelector, ModelSelect, KnowledgeDatabaseSelector,
VectorStoreInput, IconSelector.

### Nested Forms

- Nested `Form` fields → automatically wrapped in `Group` elements with conditional visibility
- `list[Form]` fields → automatically wrapped in `Repeater` elements with a template item

## NATS Messaging

### Topics

Structured NATS subject representations with auto-registry and polymorphic parsing via `Topic.from_subject(subject)`.

**Agent topic pattern**: `agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}`

**Process topic pattern**: `process.{class}.{id}.{walkthrough_id}.{event_type}.{event_name}.{event_id}`

**Pipeline topic pattern**:
`pipeline.{source_type}.{source_id}.to.{target_type}.{target_id}.{run_key}.{event_name}.{event_id}`

**Topic narrowing**: PartialTopic (wildcards) → ClassTopic (class-level) → InstanceTopic (fully specified). Each topic
has `execution_context_id` (run_id for agents, walkthrough_id for processes).

### Publishers and Subscribers

| Component      | Protocol  | Durability | Use Case                                     |
| -------------- | --------- | ---------- | -------------------------------------------- |
| `JSPublisher`  | JetStream | Durable    | Workflow events, event replay, audit trail   |
| `NCPublisher`  | NATS Core | Ephemeral  | Real-time UI updates, discovery              |
| `JSSubscriber` | JetStream | Durable    | Workflow dispatchers, consumer groups        |
| `NCSubscriber` | NATS Core | Ephemeral  | Discovery responses, ephemeral notifications |

Both publishers extend `AbstractPublisher[TEvent]`. Both subscribers extend `AbstractSubscriber[TEvent]` with generic
event type. OTEL trace context propagated via `NATSMessageHeaders`.

### Topic Managers

Subject string builders that construct NATS subjects. Each manager provides methods like
`get_subject_for_all_events_in_agent()`, `get_subject_for_specific_event_in_agent()`, etc.

- `AgentTopicManager` — agent subjects with DISPLAY_EVENT / CONTROL_EVENT type segments
- `ProcessTopicManager` — process subjects
- `PipelineTopicManager` — pipeline subjects

### RPC

Request-reply pattern for config fetching (decouples config from event payloads):

- `AgentConfigClient.fetch_config(class, id)` → sends `FetchAgentConfigRequest` → receives config dict
- `ProcessConfigClient.fetch_config(class, id)` → same pattern
- Subject: `aihub.rpc.config.{entity_type}.{class}.{id}`

### Polling

`JSPoller` — generic JetStream batch poller. Yields `PolledMessage` with `.event` (deserialized BaseEvent), `.ack()`,
and `.nak()`. Used by sensors and consumers that need explicit batch processing.

## Dispatcher and Workflow

### BaseDispatcher

Abstract orchestrator that drives workflow execution. Handles:

- Event routing: receives events on NATS, stores in `JetStreamEventStore`, checks step readiness
- Step execution: builds kwargs from event mapping, executes step method, publishes returned events
- State management: all state in JetStream (events) + Redis (steps via `StepStore`). No instance state on the dispatcher
  — enables horizontal scaling and load balancing via JetStream consumer groups.

### DispatchableWorkflow

Abstract base class for both agents and processes. Methods annotated with `@step` (agents) or `@process_step`
(processes) become workflow building blocks.

Step annotations store:

- `_input_event_mapping`: which event types each parameter expects
- `_output_events`: which event types the step can produce
- `_size_requirements`: how many events of each type are needed

Key methods:

- `get_steps()` — all annotated step methods
- `get_steps_waiting_for_event(event_class)` — steps that handle a specific event type
- `get_input_events()` / `get_output_events()` — all event types consumed/produced

## Authentication and Authorization

### Auth Handlers

`AuthHandler` (abstract) → extracts/validates credentials from HTTP requests → returns `UserIdentity`.

| Handler                 | Mechanism                     |
| ----------------------- | ----------------------------- |
| `KeycloakAuthHandler`   | Keycloak OIDC (JWT + JWKS)    |
| `TokenAuthHandler`      | Simple token validation       |
| `BearerAuthHandler`     | Bearer token header           |
| `TokenAndOauth2Handler` | Combined token + OAuth2       |
| `OpenWebuiAuthHandler`  | OpenWebUI session integration |

Tests and playground servers use `TestAuthHandler` from `swiss_ai_hub.core.testing.auth_utils`, which bypasses token
parsing and returns a fixed identity built from the constants in `test_identity.py`. It lives under `core.testing` — not
`core.auth` — so it cannot be imported into production code by accident.

Sysadmin-only endpoints (those requiring the `AIHubSysAdmin` Keycloak realm role) are NOT protected by a separate auth
handler. They use `Security(self.sys_admin_user())` from the `Controller` base class, which wraps `authenticated_user()`
and gates on `UserIdentity.is_sys_admin`. The flag itself is populated by the regular auth handlers from the JWT roles
claim (or, for static tokens, via `KeycloakAdminService.get_user_realm_roles`).

### Permission System (AccessChecker)

Hierarchical permission matching: `aihub.[user|admin].<resource>.<subresource>.<id>`

**Wildcards**: `*` (single level), `>` (multi-level), `?*` (any single with value), `?>` (any remaining)

**AccessLevel**: `ACCESS_ADMIN` > `ACCESS_USER` > `ACCESS_DENIED`. Admin rules implicitly grant user access.

### KeycloakAdminService

Static-method service wrapping the Keycloak Admin API. Encodes platform-specific knowledge of the `/tenants/` hierarchy
and the `AIHubSysAdmin` realm role. Selected methods:

- `tenant_exists(tenant_id)` / `filter_existing_tenant_ids(ids)` — authoritative existence check (Keycloak owns
  existence, not Mongo). Use these before trusting `TenantMetadataEntity` data.
- `get_tenant_group(tenant_id)` / `get_all_tenant_groups()` / `create_tenant_group(tenant_id)` — group lifecycle.
- `assign_user_to_tenant(user_id, tenant_id)` / `remove_user_from_tenant(user_id, tenant_id)` /
  `get_tenant_members(tenant_id, ...)` / `count_tenant_members(tenant_id)` — membership.
- `get_user_realm_roles(user_id)` / `get_user_ids_with_realm_role(role_name)` — realm role lookups.
- `get_active_tenant_id(user_id)` / `set_active_tenant(user_id, tenant_id)` / `clear_active_tenant(user_id)` /
  `get_user_ids_with_active_tenant(tenant_id)` — active-tenant attribute (per ADR `2026_04_07`).
- `get_superuser_id()` (memoized) / `assign_superuser_to_tenant(tenant_id)` (idempotent) — superuser membership; the
  latter is called from startup-tenant bootstrap and `TenantAdminService.create_tenant_metadata` (per ADR
  `2026_04_15_superuser_added_to_every_new_tenant`).

**Key methods**:

- `AccessChecker.from_user(user)` — create checker from UserIdentity (carries `is_sys_admin` through)
- `.has_access_to_agent(agent_class, agent_id)` → bool
- `.has_access_to_process(process_class, process_id)` → bool
- `.has_access_to_service(service_name)` → bool
- `.access_level(permission_template)` → AccessLevel

**Sysadmin short-circuit**: When `UserIdentity.is_sys_admin=True`, `access_level()` returns `ACCESS_ADMIN`
unconditionally, bypassing both the tenant-ceiling and user-rule stages. Sysadmins may have `acting_within_tenant=None`.
The auth pipeline (`AuthHandler._resolve_tenant_by_id` / `_resolve_active_tenant`) also skips the `UserTenantRoleEntity`
membership check for sysadmins. See ADR `2026_04_15_sysadmin_implicit_admin_access.md`.

## Internationalization (i18n)

**Default locale**: English (`en`). **Required**: `de`, `en`, `fr`, `it`.

**LocaleString**: Multi-language container. `LocaleString(de="Hallo", en="Hello", fr="Bonjour", it="Ciao")`. Methods:
`in_locale(locale)`, `from_i18n_path(path)` (load from YAML), `as_form(label)` (create `LocaleInput`).

**LocaleHandler**: Runtime resolution. Fallback: requested → `en` → first available.

**Translations**: YAML files at `i18n/translations/{scope}/{name}.{locale}.yml`. Accessed via dot notation:
`lib.events.start_event.name`. Scopes: `lib`, `bot`, `api`, `agent`, `process`, `action`.

## Persistence

**Pattern**: MongoEngine `Document` + repository methods as `@classmethod`. Schema and data access in one class.

```python
class RoleEntity(Document):
    meta = {"collection": "roles", "indexes": [{"fields": ["name"], "unique": True}]}
    name = StringField(required=True, unique=True)
    access_rules = ListField(StringField(), default=list)

    @classmethod
    def get_access_rules_for_roles(cls, role_names: list[str]) -> set[str]:
        return {rule for role in cls.objects(name__in=role_names) for rule in role.access_rules}
```

**Key entities**: `RoleEntity` (access rules; every role belongs to exactly one tenant), `TenantMetadataEntity` (tenant
display metadata — name, description, access rules; **NOT** the source of truth for tenant existence, Keycloak's
`/tenants/<id>` group is — verify via `KeycloakAdminService.tenant_exists()`), `UserTenantRoleEntity` (tenant-scoped
role assignments), `ThreadEntity` (conversations), `PersistedAgentEventEntity` / `PersistedProcessEventEntity` (event
storage), `AgentConfigEntity` / `ProcessConfigEntity` (configs), `UserDashboardEntity` (dashboard config),
`NotificationEntity`, `LocaleStringEntity`.

## Infrastructure Settings

~20 Pydantic `BaseSettings` classes for external service connections. Environment variables are NOT auto-loaded — they
must be loaded explicitly when constructing settings instances.

| Settings Class         | Service                | Env Prefix  |
| ---------------------- | ---------------------- | ----------- |
| `AIHubSettings`        | Core API config        | (various)   |
| `NatsSettings`         | NATS broker            | `NATS_`     |
| `MongoSettings`        | MongoDB/FerretDB       | `MONGO_`    |
| `RedisSettings`        | Valkey/Redis           | `REDIS_`    |
| `MilvusSettings`       | Milvus vector DB       | `MILVUS_`   |
| `S3StorageSettings`    | SeaweedFS/S3           | `S3_`       |
| `Neo4jSettings`        | Neo4j graph DB         | `NEO4J_`    |
| `LangfuseSettings`     | Langfuse observability | `LANGFUSE_` |
| `LiteLLMProxySettings` | LiteLLM gateway        | `LITELLM_`  |
| `MineruSettings`       | Document parsing       | `MINERU_`   |
| `RcloneSettings`       | Cloud sync             | `RCLONE_`   |

OpenTelemetry: `SmartTracer` for span creation, `@trace_fn` decorator for automatic function tracing.

## Displayers

Real-time event emission for streaming LLM output to the UI:

- **EventDisplayer**: Core class. `display_chunk(text)` → `ChunkEvent`, `display_thought(text)` → `ThoughtEvent`,
  `display_llm_stream(stream)` → full streaming with token counting, `display_llm_costs()` → cost events.
- **StreamProcessor**: Buffers and flushes output by `ContentType` (REGULAR vs THINKING). Call `process_chunk(delta)`
  for each streaming chunk, then `finalize()` to get the aggregate response.
- **TagParser**: Parses `<think>...</think>` tags from LLM reasoning output, splitting into thinking vs regular content.
- **StreamBuffer**: Auto-flush buffer with configurable thresholds (sentence boundaries, character count).

## Generative AI Utilities

| Module          | Purpose                               | Key Entry Points                                                                                                   |
| --------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `memory/`       | Agent-scoped memory (user + org)      | `AgentMemory.add_user_memory()`, `search_user_memory()`                                                            |
| `retrieval/`    | RAG node retrieval                    | `retrieve_nodes()`, `condense_standalone_question()`                                                               |
| `retrievers/`   | Vector store abstraction              | `KnowledgeRetriever`, `BaseRetriever`                                                                              |
| `rerank/`       | Result reranking                      | `rerank_nodes()` (via LiteLLM)                                                                                     |
| `guards/`       | Input/output guards                   | `agent_description_guard`, `context_sufficient_guard`                                                              |
| `processors/`   | Retrieval post-processors             | `ParentSummaryPostProcessor`, `VectorPrevNextPostProcessor`, `ScoreScalerPostProcessor`                            |
| `resources/`    | LLM/embedding model configs           | `LLMConfig`, `EmbeddingModelConfig`, `RerankingModelConfig`                                                        |
| `document/`     | Document loading and parsing          | `MineruLoader`, `MarkdownStructuralNodeParser`                                                                     |
| `prompting/`    | Few-shot examples, language detection | `FewShotExample`, `check_language()`                                                                               |
| `chat_history/` | Chat context management               | `limit_chat_history()`, `extend_chat_history_with_user_memory()`, `extend_chat_history_with_organization_memory()` |
| `routing/`      | LLM-based event routing               | `route_to_event_using_llm()`                                                                                       |

## FastAPI Controllers

**Controller**: Abstract base class for all API endpoints.

- `base_route`: URL prefix string
- `auth`: injected `AuthHandler` dependency
- `user_with_permission(template)`: returns FastAPI `Depends` that checks permissions
- Automatic OTEL span enrichment with user/service/request context
- `mount(app)`: attaches router to FastAPI application

**HealthController**: Standard health check endpoints at `/health`.

## Testing

**Location**: Tests are colocated with the source code they test (e.g., `events/test_events.py`,
`auth/dependencies/TokenAuthHandler/test/`). No separate top-level `tests/` directory.

**Utilities**:

- `db_isolation`: REQUIRED. Every package's top-level `conftest.py` must import `swiss_ai_hub.core.testing.db_isolation`
  BEFORE any other `swiss_ai_hub.*` import. The module sets `AIHUB_MONGO_MAIN_DB_NAME=aihub_test` at import time so all
  `AIHubSettings()` instances resolve to the test DB (never the dev/prod `aihub` DB), and registers a session-autouse
  fixture that drops the test DB at session start. Failing to import this first means tests silently hit the dev
  database.
- `@async_test`: Decorator for async pytest-bdd step functions (wraps with `asyncio.run()`)
- `fake_user()`: Creates a mock `UserIdentity` for tests (uses constants in `auth_utils/test_identity.py`)
- `ASGIAdapter`: ASGI adapter for testing FastAPI routes without a running server
- User/role mocks in `auth_utils/user_mocks.py`, `role_mocks.py`
- OAuth2 test utils in `auth_utils/oauth2_utils/`

**Run tests**: `make test` (from scope directory)

## Scope Responsibility

**Add code here when**:

- Used by 2+ services
- Core infrastructure (auth, events, config, settings, testing)
- Shared abstractions (base classes, interfaces, utilities)

**Do NOT add**:

- Service-specific business logic → `packages/agent`, `packages/process`, `packages/pipeline`, `packages/api`
- Single-use implementations
- Agent/process-specific events (create them in the respective scope, not here)

## Essential Files

**Event system**:

- `core/events/base_event.py` — event foundation (auto-registry, deserialization)
- `core/events/agent/control/control_event.py` — workflow control base
- `core/events/agent/display/display_event.py` — UI observability base
- `core/events/agent/control_and_display_event.py` — dual-purpose base
- `core/events/agent/semantic/semantic_event.py` — OpenInference tracing base
- `core/events/process/process_event.py` — process orchestration base

**Form system**:

- `core/form/form.py` — form duality system
- `core/form/base/prime_vue_element.py` — form element base
- `core/form/elements/` — 28 form elements

**Workflow engine**:

- `core/workflow/dispatchable_workflow.py` — workflow base class
- `core/dispatcher/base_dispatcher.py` — event orchestration
- `core/topics/topic.py` — NATS subject parsing
- `core/topic_managers/agents/agent_topic_manager.py` — subject builders
- `core/publishers/js_publisher.py` — durable event publishing
- `core/rpc/agent_config_client.py` — config RPC

**Auth and identity**:

- `core/auth/access/access_checker.py` — permission engine
- `core/auth/dependencies/auth_handler.py` — auth handler base
- `core/auth/identity/user_identity.py` — user identity model

**Config and i18n**:

- `core/agents/agent_config.py` — agent config with form duality
- `core/processes/process_config.py` — process config with form duality
- `core/i18n/locale_string.py` — multi-language strings

**Infrastructure**:

- `core/infrastructure/api/ai_hub_settings.py` — core settings
- `core/infrastructure/opentelemetry/tracing/smart_tracer.py` — tracing
- `core/displayers/event_displayer.py` — UI event emission
