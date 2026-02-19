# aihub_lib - Foundational Shared Library

**Purpose**: Shared infrastructure library used by ALL AI-Hub services. Code belongs here if used by 2+ services.
Three major systems: NATS event-driven architecture (Swiss AI Agent Protocol), authentication/authorization, and AI/ML
utilities. NOT for service-specific business logic — that belongs in `aihub_agent`, `aihub_process`, `aihub_pipeline`,
etc.

## Folder Structure

```
aihub_lib/
├── agents/                          # Agent config base + workflow visualization
│   ├── AgentConfig.py               # Base config class (Form duality pattern)
│   ├── AgentRef.py                  # Agent instance reference
│   └── visualizers/types/           # Workflow graph types (NodeData, EdgeData, WorkflowGraph)
├── auth/                            # Authentication & authorization
│   ├── access/AccessChecker.py      # Permission matching engine (hierarchical wildcards)
│   ├── dependencies/                # Auth handlers (AuthHandler → OAuth2, Token, Bearer, OpenWebUI, Superuser, DevOnly)
│   └── identity/                    # Identity providers (IdentityProvider → Azure, Token, Superuser, DevOnly)
├── context/                         # Context utilities
├── displayers/                      # Real-time event emission for UI streaming
│   ├── EventDisplayer.py            # Core: display_chunk(), display_thought(), display_llm_stream()
│   ├── stream/StreamProcessor.py    # Buffers output by ContentType (REGULAR/THINKING)
│   ├── parser/TagParser.py          # Parses <think>...</think> tags from LLM output
│   └── buffer/StreamBuffer.py       # Auto-flush on sentence boundaries or size thresholds
├── generative_ai/                   # AI/ML utilities
│   ├── chat_history/                # Chat history management + memory extension
│   ├── document/                    # Loaders (Docling, DocumentIntelligence), parsers, refinement
│   ├── evaluation/                  # LLM evaluation
│   ├── guards/                      # Guard implementations (PII, context, confidence, few-shot)
│   ├── memory/                      # AgentMemory (user + org scoped via mem0)
│   ├── processors/                  # Post-processors (ParentSummary, PrevNext, ScoreScaler)
│   ├── prompting/                   # Few-shot examples, language detection
│   ├── rerank/                      # Cohere reranking integration
│   ├── resources/                   # LLMConfig, EmbeddingModelConfig, RerankingModelConfig
│   ├── retrieval/                   # RAG: retrieve_nodes, condense_question, combine_nodes
│   ├── retrievers/                  # KnowledgeRetriever (Milvus), BaseRetriever
│   ├── routing/                     # LLM-based event routing
│   └── utils/                       # Shared AI utilities
├── i18n/                            # Internationalization
│   ├── LocaleString.py              # Multi-language container (de, en, fr, it)
│   ├── LocaleHandler.py             # Runtime locale resolution with fallback chains
│   └── translations/                # YAML files: {scope}/{name}.{locale}.yml
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
│   ├── docling/                     # DoclingSettings (document parsing)
│   ├── rclone/                      # RcloneSettings (cloud sync)
│   ├── mem0/                        # Long-term memory settings
│   ├── sharepoint/                  # SharePointSettings
│   └── azure_*/                     # Azure Cognitive Services, Data Lake
├── nats/                            # Event-driven messaging (CRITICAL — see sections below)
│   ├── events/                      # Event type hierarchy (~100 event types)
│   │   ├── BaseEvent.py             # Root: auto-registry, polymorphic deserialization
│   │   ├── ControlAndDisplayEvent.py
│   │   ├── control/                 # ControlEvent, StartEvent, StopEvent, ExceptionEvent
│   │   ├── display/                 # DisplayEvent, ChunkEvent, ThoughtEvent
│   │   ├── process/                 # ProcessEvent, ProcessStart/Stop/Exception
│   │   ├── work/                    # WorkEvent: Agent, Human, Process, Program
│   │   ├── work_request/            # WorkRequestEvent: Agent, Human, Program
│   │   ├── human_in_the_loop/       # HITL request/response events
│   │   ├── agent_in_the_loop/       # AITL delegation events
│   │   ├── bot_in_the_loop/         # BITL integration events
│   │   ├── semantic/                # SemanticEvent + OpenInference tracing subtypes
│   │   ├── form/                    # Form system (Form, FormkitElement, PrimeVueElement, 28 elements)
│   │   ├── discovery/               # Agent/Process discovery events
│   │   ├── user/                    # UserMessageEvent
│   │   ├── cost/                    # LLMCostEvent
│   │   ├── memory/                  # Memory operation events
│   │   ├── pipeline/                # SourceUpdatedEvent
│   │   └── guard/, router/, common/ # Guard, routing, utility events
│   ├── dispatcher/                  # Workflow orchestration
│   │   ├── BaseDispatcher.py        # Abstract: event routing, step execution, state management
│   │   └── stores/                  # JetStreamEventStore (event replay), StepStore (Redis)
│   ├── workflow/                    # Dispatchable workflow system
│   │   ├── DispatchableWorkflow.py  # Base class for agents/processes (@step annotations)
│   │   └── annotations/             # Step annotation extractors
│   ├── publishers/                  # JSPublisher (JetStream, durable) + NCPublisher (NATS Core, ephemeral)
│   ├── subscribers/                 # JSSubscriber + NCSubscriber + agent/process specializations
│   ├── topics/                      # NATS subject structures (auto-registry)
│   │   ├── Topic.py                 # Abstract base: from_subject() polymorphic parsing
│   │   ├── agents/                  # PartialAgentTopic → AgentClassTopic → AgentInstanceTopic
│   │   ├── process/                 # PartialProcessTopic → ProcessClassTopic → ProcessInstanceTopic
│   │   ├── pipeline/                # PipelineTopic
│   │   ├── discovery/               # Agent/Process discovery topics
│   │   └── rpc/                     # RpcTopic (config fetching)
│   ├── topic_managers/              # Subject string builders
│   │   ├── agents/                  # AgentTopicManager
│   │   ├── process/                 # ProcessTopicManager
│   │   └── pipeline/                # PipelineTopicManager
│   ├── rpc/                         # AgentConfigClient, ProcessConfigClient (request-reply)
│   ├── requester/                   # RPC request side
│   ├── responder/                   # RPC response side
│   ├── polling/                     # JSPoller (JetStream batch consumption)
│   ├── streams/                     # StreamManager (JetStream stream lifecycle)
│   └── tracing/                     # NATSMessageHeaders (OTEL trace context propagation)
├── persistence/                     # Database abstractions (MongoEngine ODM)
│   ├── access/                      # RoleEntity (roles + access rules)
│   ├── agents/                      # AgentConfigEntity
│   ├── process/                     # ProcessConfigEntity
│   ├── messaging/                   # ThreadEntity, PersistedAgentEventEntity, PersistedProcessEventEntity
│   ├── user/                        # UserEntity
│   ├── i18n/                        # LocaleStringEntity
│   ├── rag/                         # RAG document persistence
│   ├── notification/                # NotificationEntity
│   └── insight/, migrations/        # Analytics, schema migrations
├── processes/                       # Process config base
│   └── ProcessConfig.py             # Base config class (Form duality, parallel to AgentConfig)
├── records/                         # Record types
├── routes/                          # FastAPI base controllers
│   ├── Controller.py                # Abstract: base_route, auth DI, permission templates, OTEL spans
│   └── health/                      # HealthController, HealthServer, health checks
├── runners/                         # Execution runners
├── settings/                        # App-level configuration
└── testing/                         # Testing utilities
    ├── asyncio_utils/bdd.py         # @async_test decorator for async pytest-bdd
    ├── auth_utils/                   # fake_user(), user_mocks, role_mocks, OAuth2 test utils
    └── route_adapter/ASGIAdapter.py  # ASGI adapter for testing FastAPI routes
```

## Event System (CRITICAL)

The heart of aihub_lib. All inter-service communication uses NATS events from this hierarchy. Understanding
Control vs Display separation is essential for working with any service.

### Auto-Registration

Events, Forms, and Topics all use `__pydantic_init_subclass__` to auto-register in class-level registries:

- `BaseEvent._event_registry` — enables `BaseEvent.deserialize_event(data)` for polymorphic deserialization
- `Form._form_registry` — enables form lookup by name
- `Topic._topic_registry` — enables `Topic.from_subject(subject)` for subject parsing

`_parent_event_names` tracks full inheritance chain, enabling runtime type checks via `is_control_event`,
`is_display_event`, `is_work_event`, etc.

### Event Hierarchy

```
BaseEvent (root — auto-registry, sequence numbering, trace dict)
│
├── ControlEvent (drives workflow execution — ONLY type that controls flow)
│   └── ProcessEvent (process orchestration)
│       ├── WorkEvent (signals work completion)
│       │   ├── AgentWorkEvent[TEvent: StopEvent]
│       │   ├── HumanWorkEvent
│       │   ├── ProgramWorkEvent
│       │   └── ProcessWorkEvent (ProcessStartEvent, ProcessStopEvent)
│       └── WorkRequestEvent (delegates work to entities)
│           ├── AgentWorkRequestEvent
│           ├── HumanWorkRequestEvent
│           └── ProgramWorkRequestEvent
│
├── DisplayEvent (UI/monitoring ONLY — never affects control flow)
│   ├── ChunkEvent (streaming LLM output)
│   └── ThoughtEvent (reasoning transparency)
│
├── ControlAndDisplayEvent (dual purpose — both control AND display)
│   ├── StartEvent, StopEvent (workflow lifecycle)
│   ├── HumanInTheLoopRequestEvent / HumanInTheLoopResponseEvent (HITL)
│   ├── AgentInTheLoopRequestEvent / AgentInTheLoopResponseEvent (AITL)
│   ├── BotInTheLoopRequestEvent / BotInTheLoopResponseEvent (BITL)
│   └── SemanticEvent (OpenInference tracing)
│       ├── LLMEvent, RetrieverEvent, EmbeddingEvent
│       ├── RerankerEvent, ToolEvent, ChainEvent
│       ├── GuardEvent, AgentEvent
│       └── ExceptionEvent
│
├── UserMessageEvent (user chat input)
├── LLMCostEvent (billing/cost tracking)
└── Discovery events (AgentDiscoveryResponseEvent, ProcessDiscoveryResponseEvent)
```

### When to Use Which Event Type

| Type                     | Purpose                          | Who consumes              | Examples                            |
| ------------------------ | -------------------------------- | ------------------------- | ----------------------------------- |
| `ControlEvent`           | Drive workflow state transitions | Dispatchers, step methods | `StartEvent`, `StopEvent`           |
| `DisplayEvent`           | Real-time UI feedback            | Frontend, tracing         | `ChunkEvent`, `ThoughtEvent`        |
| `ControlAndDisplayEvent` | Both workflow + UI               | Both                      | `StartEvent`, HITL events, semantic |
| `ProcessEvent`           | Process orchestration            | Process dispatchers       | `WorkEvent`, `WorkRequestEvent`     |
| `SemanticEvent`          | OpenInference observability      | Langfuse, tracing         | `LLMEvent`, `RetrieverEvent`        |

### Creating a New Event

1. Choose the correct base class from the hierarchy above
2. Place in `nats/events/<category>/` (new directory if needed)
3. Auto-registers on import — no manual registration needed
4. If it's a ControlAndDisplayEvent, it inherits from both ControlEvent and DisplayEvent

## Form System (Form Duality Pattern)

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
Select, MultiSelect, Listbox, CascadeSelect, SelectButton, DatePicker, ColorPicker, Rating, Knob, Slider,
Group (nested forms), Repeater (arrays), LocaleInput (multi-language), AgentSelector, ModelSelect,
KnowledgeDatabaseSelector, VectorStoreInput, IconSelector.

All elements support LocaleString labels/help, validation rules, and `in_locale()` for localization.

### Nested Forms

- Nested `Form` fields → automatically wrapped in `Group` elements with conditional visibility
- `list[Form]` fields → automatically wrapped in `Repeater` elements with a template item

## NATS Messaging

### Topics

Structured NATS subject representations with auto-registry and polymorphic parsing via `Topic.from_subject(subject)`.

**Agent topic pattern**: `agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}`

**Process topic pattern**: `process.{class}.{id}.{walkthrough_id}.{event_type}.{event_name}.{event_id}`

**Pipeline topic pattern**: `pipeline.{source_type}.{source_id}.to.{target_type}.{target_id}.{run_key}.{event_name}.{event_id}`

**Topic narrowing**: PartialTopic (wildcards) → ClassTopic (class-level) → InstanceTopic (fully specified).
Each topic has `execution_context_id` (run_id for agents, walkthrough_id for processes).

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

`JSPoller` — generic JetStream batch poller. Yields `PolledMessage` with `.event` (deserialized BaseEvent),
`.ack()`, and `.nak()`. Used by sensors and consumers that need explicit batch processing.

## Dispatcher and Workflow

### BaseDispatcher

Abstract orchestrator that drives workflow execution. Handles:

- Event routing: receives events on NATS, stores in `JetStreamEventStore`, checks step readiness
- Step execution: builds kwargs from event mapping, executes step method, publishes returned events
- State management: all state in JetStream (events) + Redis (steps via `StepStore`). No instance state on the
  dispatcher — enables horizontal scaling and load balancing via JetStream consumer groups.

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

| Handler                               | Mechanism                     |
| ------------------------------------- | ----------------------------- |
| `OAuth2AuthHandler`                   | OpenID Connect (Azure AD)     |
| `TokenAuthHandler`                    | Simple token validation       |
| `BearerAuthHandler`                   | Bearer token header           |
| `TokenAndOauth2Handler`               | Combined token + OAuth2       |
| `OpenWebuiAuthHandler`                | OpenWebUI session integration |
| `SuperuserAuthHandler`                | Hardcoded superuser token     |
| `DangerousDevelopmentOnlyAuthHandler` | No validation (dev only)      |

### Identity Providers

`IdentityProvider` (abstract) → retrieves full user details from identity systems.

Implementations: `AzureIdentityProvider` (Azure AD/Graph API), `TokenIdentityProvider`,
`SuperuserIdentityProvider`, `MultiStrategyIdentityProvider`, `DangerousDevelopmentOnlyIdentityProvider`.

### Permission System (AccessChecker)

Hierarchical permission matching: `aihub.[user|admin].<resource>.<subresource>.<id>`

**Wildcards**: `*` (single level), `>` (multi-level), `?*` (any single with value), `?>` (any remaining)

**AccessLevel**: `ACCESS_ADMIN` > `ACCESS_USER` > `ACCESS_DENIED`. Admin rules implicitly grant user access.

**Key methods**:

- `AccessChecker.from_user(user)` — create checker from UserIdentity
- `.has_access_to_agent(agent_class, agent_id)` → bool
- `.has_access_to_process(process_class, process_id)` → bool
- `.has_access_to_service(service_name)` → bool
- `.access_level(permission_template)` → AccessLevel

## Internationalization (i18n)

**Default locale**: English (`en`). **Required**: `de`, `en`, `fr`, `it`.

**LocaleString**: Multi-language container. `LocaleString(de="Hallo", en="Hello", fr="Bonjour", it="Ciao")`.
Methods: `in_locale(locale)`, `from_i18n_path(path)` (load from YAML), `as_form(label)` (create `LocaleInput`).

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

**Key entities**: `RoleEntity` (access), `ThreadEntity` (conversations), `PersistedAgentEventEntity` /
`PersistedProcessEventEntity` (event storage), `AgentConfigEntity` / `ProcessConfigEntity` (configs),
`UserEntity`, `NotificationEntity`, `LocaleStringEntity`.

## Infrastructure Settings

~20 Pydantic `BaseSettings` classes for external service connections. Auto-load from environment variables.

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
| `DoclingSettings`      | Document parsing       | `DOCLING_`  |
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

| Module          | Purpose                               | Key Entry Points                                            |
| --------------- | ------------------------------------- | ----------------------------------------------------------- |
| `memory/`       | Agent-scoped memory (user + org)      | `AgentMemory.add_user_memory()`, `search_user_memory()`     |
| `retrieval/`    | RAG node retrieval                    | `retrieve_nodes()`, `condense_standalone_question()`        |
| `retrievers/`   | Vector store abstraction              | `KnowledgeRetriever`, `BaseRetriever`                       |
| `rerank/`       | Result reranking                      | `rerank_nodes()` (Cohere)                                   |
| `guards/`       | Input/output guards                   | `agent_description_guard`, `context_sufficient_guard`       |
| `processors/`   | Retrieval post-processors             | `ParentSummaryPostProcessor`, `VectorPrevNextPostProcessor` |
| `resources/`    | LLM/embedding model configs           | `LLMConfig`, `EmbeddingModelConfig`, `RerankingModelConfig` |
| `document/`     | Document loading and parsing          | `DoclingLoader`, `MarkdownStructuralNodeParser`             |
| `prompting/`    | Few-shot examples, language detection | `FewShotExample`, `check_language()`                        |
| `chat_history/` | Chat context management               | `limit_chat_history()`, `extend_with_user_memory()`         |
| `routing/`      | LLM-based event routing               | `route_to_event_using_llm()`                                |

## FastAPI Controllers

**Controller**: Abstract base class for all API endpoints.

- `base_route`: URL prefix string
- `auth`: injected `AuthHandler` dependency
- `user_with_permission(template)`: returns FastAPI `Depends` that checks permissions
- Automatic OTEL span enrichment with user/service/request context
- `mount(app)`: attaches router to FastAPI application

**HealthController**: Standard health check endpoints at `/health`.

## Testing Utilities

- `@async_test`: Decorator for async pytest-bdd step functions (wraps with `asyncio.run()`)
- `fake_user()`: Creates a mock `UserIdentity` for tests (uses `DangerousDevelopmentOnlyAuthSettings`)
- `ASGIAdapter`: ASGI adapter for testing FastAPI routes without a running server
- User/role mocks in `auth_utils/user_mocks.py`, `role_mocks.py`
- OAuth2 test utils in `auth_utils/oauth2_utils/`

**Test location**: `aihub_lib/tests/`

**Run tests**: `make test` (from scope directory)

## Scope Responsibility

**Add code here when**:

- Used by 2+ services
- Core infrastructure (auth, events, config, settings, testing)
- Shared abstractions (base classes, interfaces, utilities)

**Do NOT add**:

- Service-specific business logic → `aihub_agent`, `aihub_process`, `aihub_pipeline`, `aihub_api`
- Single-use implementations
- Agent/process-specific events (create them in the respective scope, not here)

## Essential Files

**Event system**:

- `aihub_lib/nats/events/BaseEvent.py` — event foundation (auto-registry, deserialization)
- `aihub_lib/nats/events/control/ControlEvent.py` — workflow control base
- `aihub_lib/nats/events/display/DisplayEvent.py` — UI observability base
- `aihub_lib/nats/events/ControlAndDisplayEvent.py` — dual-purpose base
- `aihub_lib/nats/events/form/Form.py` — form duality system
- `aihub_lib/nats/events/form/base/PrimeVueElement.py` — form element base
- `aihub_lib/nats/events/form/elements/` — 28 form elements

**Workflow engine**:

- `aihub_lib/nats/workflow/DispatchableWorkflow.py` — workflow base class
- `aihub_lib/nats/dispatcher/BaseDispatcher.py` — event orchestration
- `aihub_lib/nats/topics/Topic.py` — NATS subject parsing
- `aihub_lib/nats/topic_managers/agents/AgentTopicManager.py` — subject builders
- `aihub_lib/nats/publishers/JSPublisher.py` — durable event publishing
- `aihub_lib/nats/rpc/AgentConfigClient.py` — config RPC

**Auth and identity**:

- `aihub_lib/auth/access/AccessChecker.py` — permission engine
- `aihub_lib/auth/dependencies/AuthHandler.py` — auth handler base
- `aihub_lib/auth/identity/IdentityProvider.py` — identity provider base
- `aihub_lib/auth/identity/UserIdentity.py` — user model

**Config and i18n**:

- `aihub_lib/agents/AgentConfig.py` — agent config with form duality
- `aihub_lib/processes/ProcessConfig.py` — process config with form duality
- `aihub_lib/i18n/LocaleString.py` — multi-language strings
- `aihub_lib/i18n/LocaleHandler.py` — locale resolution

**Infrastructure**:

- `aihub_lib/infrastructure/api/AIHubSettings.py` — core settings
- `aihub_lib/infrastructure/opentelemetry/tracing/SmartTracer.py` — tracing
- `aihub_lib/displayers/EventDisplayer.py` — UI event emission

**Testing**:

- `aihub_lib/testing/asyncio_utils/bdd.py` — async BDD helper
- `aihub_lib/testing/auth_utils/fake_user.py` — mock users

**Persistence**:

- `aihub_lib/persistence/access/entities/RoleEntity.py` — entity pattern example
- `aihub_lib/routes/Controller.py` — FastAPI controller base
