# packages/agent - AI Agent SDK

**Purpose**: SDK for building transparent, workflow-based AI agents. Three parts: the framework (`packages/agent/`),
pre-built agents (`agents/` + `app/`), and playground examples (`playground/`). Business logic for individual steps
(retrieval, LLM calls, memory) lives in agent-specific code or `packages/core`, not in the SDK framework itself.

## Folder Structure

```
packages/agent/                       # SDK framework
├── swiss_ai_hub/agent/
│   ├── agents/                        # Agent base class + production agent implementations
│   │   ├── agent.py                   # Base class (extends DispatchableWorkflow)
│   │   ├── rag_agent/                 # Knowledge QA with retrieval, reranking, memory
│   │   ├── llm_wrapping_agent/        # Simple LLM chat passthrough
│   │   ├── expert_asking_agent/       # Human expert escalation via Teams/Slack
│   │   ├── expert_rag_agent/          # RAG with expert fallback
│   │   ├── few_shot_agent/            # Pattern-matching with examples
│   │   ├── email_classification_agent/ # Non-conversational: files unread mail into category folders
│   │   ├── imap_agent/                # Non-conversational IMAP mail read/move + draft-reply
│   │   ├── namespace_selection_agent/ # LLM-driven knowledge routing
│   │   └── retrieval_agent/           # Pure document retrieval (no LLM)
│   ├── context/
│   │   ├── run/run_context.py          # Per-run ephemeral state (Redis, 30d TTL)
│   │   └── thread/thread_context.py    # Per-thread persistent state (Redis, 30d TTL)
│   ├── dispatchers/
│   │   └── agent_dispatcher.py         # Core workflow executor (DI, config fetch, step dispatch)
│   ├── i18n/
│   │   ├── agent_locale_string.py      # Multi-locale string resolution for agents
│   │   └── translations/agent/         # Translation files: {name}.{de|en|fr|it}.yml
│   ├── mcp/                            # MCP tool integration (McpClientFactory, McpReactService)
├── rag/                            # Shared RAG step functions and preconditions
│   ├── runners/
│   │   ├── agent_runner.py             # Production runner (NATS, Redis, Milvus, discovery)
│   │   └── agent_test_runner.py        # Test runner (sandboxed, event capture, mock config)
│   ├── steps/                          # Shared step configs (e.g., FewShotStepConfig)
│   ├── tracing/
│   │   └── agent_run_tracer.py         # OpenTelemetry + Langfuse trace integration
│   └── workflow/
│       └── decorators/
│           ├── step.py                 # @step() decorator — defines workflow building blocks
│           └── precondition.py         # @precondition() decorator — step readiness checks

app/                               # Entry points (one per agent, each with main.py + Dockerfile)
├── rag_agent/main.py
├── llm_wrapping_agent/main.py
├── expert_asking_agent/main.py
├── expert_rag_agent/main.py
├── few_shot_agent/main.py
├── namespace_selection_agent/main.py
└── retrieval_agent/main.py

playground/                        # Examples and testing
├── agent/                         # Production-like agents (bot_in_the_loop_agent, hitl_demo_agent,
│                                  #   cron_demo_agent)
├── minimal_workflow/              # 20 self-contained pattern showcases (START HERE)
├── performance/                   # Load testing with performance_testing_agent
└── testing/                       # SDK integration tests
```

## Agent Blueprint vs Agent Profile

The platform separates **what an agent can do** (code) from **how it's configured** (data).

**Agent Blueprint** (`agent_class`): The Python class. Defines workflow steps, event specs, form schema, default config.
One per agent type. Discovered automatically when agents come online. Stored in MongoDB `agent_classes` collection.
Example: `RAGAgent`.

**Agent Profile** (`agent_id`): A user-created configuration of a blueprint. Has a unique URL-safe slug, name,
description, icon, and specific settings. Multiple profiles from one blueprint. Stored in MongoDB `agent_configs`
collection. Example: `rag-agent-hr`, `rag-agent-legal`.

**What you start**: An `AgentRunner` with an agent class (blueprint). It listens on NATS for all profiles of that class.

**What gets a run**: An agent profile. When a `StartEvent` arrives, it carries an `agent_id` linking to a specific
profile. The dispatcher fetches that profile's config via NATS RPC.

**Analogy**: Blueprint = Docker image, Profile = container. Or: Blueprint = class definition, Profile = instance.

**In code**: `AgentConfig.agent_class` is the blueprint name, `AgentConfig.agent_id` is the profile slug.

## Architecture: Decentralized Event-Driven Workflows

This is a custom workflow engine — LlamaIndex is only used for LLMs and retrievers, not for workflow orchestration.

**Inheritance chain**: `DispatchableWorkflow` → `Agent` → concrete agents (e.g., `RAGAgent`)

**Key design property**: Everything is decentralized. Steps are dispatched via NATS/JetStream — consecutive steps on the
same run may execute on different servers. This means:

- No instance state on the agent class
- No in-memory workflow state
- All state lives in Redis (`RunContext`/`ThreadContext`) and JetStream (event history)
- `AgentRunner` cannot track run state — it subscribes to events and delegates to `AgentDispatcher`
- The dispatcher creates a fresh `agent()` instance for each step execution

## The Agent Class

Minimal and stateless. Only class-level attributes — never instantiated by hand.

```python
class MyAgent(Agent):
    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.my_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.my_agent.metadata.description")
    icon: ClassVar[str] = "mage:robot"

    @step()
    async def start_step(self, event: UserMessageEvent) -> CustomEvent:
        return CustomEvent(data="processed")

    @step()
    async def end_step(self, event: CustomEvent) -> StopEvent:
        return StopEvent()
```

`Agent` (extends `DispatchableWorkflow`) provides introspection: `get_start_events()`, `get_stop_events()`,
`get_hitl_request_events()`, `get_hitl_response_events()` — all cached classmethods that scan `@step()` signatures.

### Built-in Self-Awareness (meta questions)

Conversational blueprints can answer meta questions about themselves ("what can you do?", "why did you do X?") instead
of running their normal pipeline. The detection/answer logic is shared as free functions (`do_detect_meta_question`,
`do_answer_meta_question`, `summarize_workflow_for_meta_answer` in `self_awareness/`); the **steps are defined
explicitly in each self-aware agent** — there is no base-class mixin and no `get_steps()` filtering. An agent is
self-aware iff it defines the steps. Non-conversational blueprints (e.g. `RetrievalAgent`) simply don't.

Adopting it has two parts (see ADR `2026_06_04_self_awareness_as_explicit_per_agent_steps` and `RAGAgent` as the
reference):

1. **Define the two thin `@step` methods** on the agent: `detect_meta_question_step` (on `UserMessageEvent`) and
   `answer_meta_question_step` (returns `LLMStopEvent` directly). Each delegates to the shared free functions, passing
   `agent_config.task_llm` — both detection and the answer are auxiliary work, and `task_llm` falls back to the main
   `llm` when no task model is configured. (There is no separate stop step: once the consumer drains trailing display
   events before teardown — ADR `2026_06_09_drain_display_event_streams_before_consumer_teardown` — the answer step can
   emit the terminal `LLMStopEvent` itself without its chunks being raced.)

2. **Gate every raw `UserMessageEvent` entry step** so detection can't be raced. Two equivalent forms depending on the
   agent's start events:

   - **Entry accepts only `UserMessageEvent`** (e.g. `LLMWrappingAgent`, `FewShotAgent`): add a **required**
     `_clear: NotAMetaQuestionEvent` parameter. The dependency alone gates the step — no precondition.
   - **Entry also accepts a programmatic start** (e.g. `RAGAgent`, `ExpertRAGAgent`, `NamespaceSelectionAgent` accept
     `UserMessageEvent | RAGStartEvent`): keep `_clear: NotAMetaQuestionEvent | None = None` and combine the step's
     precondition with `check_passed_meta_question_gate(start_event, clear)`, so programmatic starts skip detection.

   The gate falls out of event dependencies — the entry step can't fire on a chat message until detection emits
   `NotAMetaQuestionEvent`. Gating cannot be automated; a self-aware blueprint that forgets it (or defines a partial
   step set) fails `self_awareness/tests/test_self_awareness_wiring.py`.

## The @step Decorator

```python
@step(
    name=LocaleString(en="My Step"),         # UI display name
    description=LocaleString(en="Does X"),   # UI description
    icon="mage:magic-wand",                  # Iconify icon
    precondition=my_precondition_fn,         # Async callable → bool
    max_executions_per_run=3,                # Limits re-execution in loops
    stop_on_error=True,                      # Default: stop workflow on exception
)
async def my_step(self, event: InputEvent) -> OutputEvent:
    ...
```

Input events are inferred from parameter type annotations, output events from the return type. The decorator extracts
event metadata and stores it as function attributes — it does not modify the function itself.

## Step Dependency Injection

The dispatcher resolves `@step()` parameters by type annotation. Declare what you need, the dispatcher provides it:

| Type Annotation                          | What Gets Injected                                                                                                                                                                                                                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event subclass (e.g., `MyEvent`)         | Matched from event history by type                                                                                                                                                                                                                                      |
| `AgentConfig` subclass                   | The merged runtime config for this run                                                                                                                                                                                                                                  |
| `StepConfig` subclass                    | Step-specific config extracted from AgentConfig                                                                                                                                                                                                                         |
| `RunContext`                             | Per-run ephemeral state (Redis)                                                                                                                                                                                                                                         |
| `ThreadContext`                          | Per-thread persistent state (Redis)                                                                                                                                                                                                                                     |
| `Redis`                                  | The raw Valkey client, for cross-run state that needs `SET NX`/TTL                                                                                                                                                                                                      |
| `UserIdentity` or `UserIdentity \| None` | The invoking user, for per-user LLM cost attribution. Read from the start event's own `user` field, so a start event that does not declare one always yields `None`. Annotate it `\| None` on programmatically-started blueprints, which may genuinely have no identity |
| `EventDisplayer`                         | Emit display events for frontend visualization                                                                                                                                                                                                                          |
| `LocaleHandler` or `AgentLocaleHandler`  | i18n handler in the run's locale                                                                                                                                                                                                                                        |
| `AgentMemory`                            | User and organization memory access                                                                                                                                                                                                                                     |
| `AgentInstanceTopic`                     | NATS topic info for this event                                                                                                                                                                                                                                          |
| `AgentClassTopic`                        | NATS topic info (class level)                                                                                                                                                                                                                                           |
| `PartialAgentTopic`                      | NATS topic info (partial/wildcard)                                                                                                                                                                                                                                      |

Source: `AgentDispatcher._get_parameter_value()` in `dispatchers/agent_dispatcher.py`.

## AgentConfig, Form Duality & Config Lifecycle

### Form Duality Pattern

`AgentConfig` inherits from `Form` — a dual-purpose Pydantic model. Every configurable field uses a union type:

```python
class MyAgentConfig(AgentConfig):
    temperature: Annotated[float | InputNumber, Field(description="LLM temperature"), Ge(0.0), Le(2.0)] = 0.7
    model_name: Annotated[str | InputText, Field(description="LLM model")] = "gpt-4"

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            **base.model_dump(),
            temperature=InputNumber(label=LocaleString(en="Temperature"), min=0.0, max=2.0),
            model_name=InputText(label=LocaleString(en="Model")),
        )
```

- **Form mode**: Fields hold `FormkitElement` instances → UI rendering. Created by `as_form()`.
- **Data mode**: Fields hold primitive values → runtime configuration. Created by `model_validate()`.
- **Configurable fields**: Set to a FormkitElement in `as_form()` — user edits in Admin UI.
- **Non-configurable fields**: Set to a primitive in `as_form()` — deployment-specific, baked in.

A base field that `AgentConfig.as_form()` deliberately leaves unset is the runner's business, not yours — `cron` is the
only one today. That is why the override above stays correct without listing it: the runner injects the element for
schedulable classes via `for_discovery()`, and a field whose value is not a form element is absent from both the
rendered form and the submission schema.

### FormKit Elements

From `swiss_ai_hub.core.form.elements`:

- **Input**: `InputText`, `InputNumber`, `Textarea`, `Password`, `InputMask`, `InputOtp`
- **Selection**: `Select`, `MultiSelect`, `CascadeSelect`, `Checkbox`, `ToggleSwitch`, `ToggleButton`, `RadioButton`,
  `SelectButton`, `Listbox`
- **Specialized**: `ModelSelect` (LLM picker), `AgentSelector` (class+id cascading), `KnowledgeDatabaseSelector`,
  `VectorStoreInput`, `IconSelector`, `LocaleInput` (multi-language), `ColorPicker`, `DatePicker`, `Knob`, `Rating`,
  `Slider`
- **Layout**: `Group` (nested forms — auto-created from nested `Form` subclasses), `Repeater` (list of forms —
  auto-created from `list[FormSubclass]`)

### Form Constraints

Use form-aware constraints from `swiss_ai_hub.core.form.constraints` — NOT Pydantic's `ge=`, `le=`:

- `Ge()`, `Le()`, `Gt()`, `Lt()` — numeric bounds
- `MinLen()`, `MaxLen()` — string/list length
- `Pattern()` — regex validation

These are `AfterValidator`s that skip validation when the value is a `FormkitElement`.

### StepConfig

`StepConfig` is a marker subclass of `Form`. Fields of type `StepConfig` on `AgentConfig` are extracted by
`get_step_configs()` and injected into steps that declare the matching type as a parameter.

### The Config Lifecycle

1. **Definition**: Developer subclasses `AgentConfig`, annotates fields with `type | FormkitElement` unions, implements
   `as_form()`.

2. **Discovery**: `AgentRunner` receives `MyConfig.as_form()` at init. On discovery request:

   - `to_formkit_form()` → extracts FormKit elements for Admin UI
   - `get_non_configurable_values()` → pre-computes deployment-fixed values
   - `ConfigSpecs.from_form()` → `to_configurable_submission_model().model_json_schema()` → JSON schema
   - All published in `AgentClassDiscoveryResponseEvent` (form, specs, event specs, workflow graph)

3. **Storage**: Admin creates a profile via Admin UI. API validates submission against
   `agent_config_specs.config_schema`, saves to `AgentConfigEntityDocument` (MongoDB `agent_configs` collection) with
   `(agent_class, agent_id)` compound unique index.

4. **Runtime Fetch**: On each `StartEvent`, dispatcher calls `AgentConfigClient.fetch_config(agent_class, agent_id)` →
   NATS RPC (`aihub.rpc.config.agent.{class}.{id}`) → `AgentConfigResponder` (API side) →
   `AgentConfigEntityDocument.find_for_class_and_id()` → returns `config_data` dict.

5. **Merge**: `Form.deep_merge(non_configurable_values, submitted_config)` → combines deployment-fixed values with
   user-configured values. Result stored in `RunContext`.

6. **Injection**: `agent_config_type.model_validate(merged_dict)` reconstructs typed config in data mode. Injected into
   `@step()` methods that declare the `AgentConfig` subclass as a parameter.

**This runs on every dispatched event, before any step.** So a config-level validation error is not a validation error —
it stops the whole agent for that profile. The dispatcher reports it as an `ExceptionEvent` rather than letting it
escape (see below), but the rule for config authors is: **do not raise in a config `model_validator` for an invariant
only some code paths need.** Enforce it where it is used, inside a step, where the failure is scoped and visible. Note
also that the API cannot run such validators at save time at all — it validates submissions against a JSON Schema
rebuilt from the model, which cannot express cross-field rules — so a config violating one saves regardless. See ADR
`2026_08_07_agent_config_failures_surface_as_exception_events`.

## AgentRunner & AgentDispatcher

**AgentRunner**: Connects agent to infrastructure (NATS, JetStream, Redis, Milvus, MongoDB). Responds to discovery
requests. Subscribes to control events and delegates to dispatcher. Constructed with `agent_type` (the class) and
`agent_config` (form-mode instance from `as_form()`). Includes health check server.

```python
runner = AgentRunner(agent_type=MyAgent, agent_config=MyAgentConfig.as_form())
await runner.run_forever()
```

**AgentDispatcher** (extends `BaseDispatcher`): The core workflow executor.

- On `StartEvent`: fetches config via NATS RPC, deep-merges with non-configurable defaults, stores in `RunContext`
- For each event: finds waiting steps via `get_steps_waiting_for_event()`, checks preconditions, executes ready steps
- Builds kwargs via dependency injection (events from history + injected services)
- Instantiates a fresh `agent()` for each step execution (stateless)
- Publishes output events to JetStream (control) or NATS Core (display)
- Checks idempotency: skips if step was already called with same input events
- On `StopEvent`/`ExceptionEvent`: cleans up `RunContext`, marks completion. Handled **before** config resolution —
  teardown needs no config, and the `ExceptionEvent` below would otherwise hit the same failure it reports and never
  retire its run
- If the config cannot be fetched, merged or validated: publishes an `ExceptionEvent` and aborts the run, so the chat
  shows an error instead of hanging forever. The message carries field locations and reasons only — an agent config
  holds credentials (e.g. `ImapClientConfig.password`) and this text reaches the user's chat

## Topic Hierarchy

NATS subject format:

```
agent.{agent_class}.{agent_id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}
```

Topic classes form a narrowing hierarchy:

| Class                | Specificity | Description                                      |
| -------------------- | ----------- | ------------------------------------------------ |
| `PartialAgentTopic`  | Loose       | Wildcards allowed, for broad subscriptions       |
| `AgentClassTopic`    | Medium      | `agent_class` specified, `agent_id` may wildcard |
| `AgentInstanceTopic` | Tight       | Fully specified including `agent_id`             |

Topic managers mirror the hierarchy (`AgentTopicManager` → `AgentClassTopicManager` → `AgentInstanceTopicManager`),
constructing NATS subjects at each specificity level. See `packages/core/swiss_ai_hub/core/topic_managers/agents/`.

## Context Management

- **RunContext**: Per-run state in Valkey. Scoped to `(thread_id, run_id)`. 30-day TTL (safety net for orphaned runs).
  Cleaned up explicitly on StopEvent. Use for: loop counters, intermediate results, retrieved docs.
- **ThreadContext**: Per-thread persistent state in Valkey. Scoped to `thread_id`. No TTL — truly persistent. Use for:
  conversation history, user preferences, namespace selections. Persists across runs.
- Neither can be reconstructed from NATS events — they hold arbitrary agent-set data that only exists in Valkey.
- Both use `async get(key, default)` / `async set(key, value)` / `async delete(key)` API.
- Factory: `RunContext.for_topic(redis, topic)`, `ThreadContext.for_topic(redis, topic)`.

## Event System

- `ControlEvent` — workflow state transitions (dispatched via JetStream, consumed by steps)
- `StartEvent` — triggers a new run (subclass of `ControlEvent`)
- `CronStartEvent` — a cron-fired run. Handling it is what makes a blueprint **schedulable**: `AgentRunner` derives
  `is_schedulable` from the declared start events, exactly as `UserMessageEvent` derives `is_conversational`. Scheduled
  runs are system runs — `user` is `None` and the thread has no members, so a step must not depend on an initiating
  identity; take tenant context from the agent's own profile instead. You declare no schedule field of your own — `cron`
  lives on the `AgentConfig` base and `AgentRunner` injects the form element for schedulable classes only, so a
  non-schedulable blueprint offers no schedule and a schedulable one cannot mis-name it. The one thing the derivation
  cannot tell you: **every scheduled run of one profile shares one thread**, so `ThreadContext` persists across runs
  while `RunContext` does not — deliberate, but a step that assumed a fresh thread per run will see the previous run's
  state
- `StopEvent` — terminates a run (subclass of `ControlEvent`)
- `DisplayEvent` — observability (dispatched via NATS Core, consumed by API/frontend)
- `HumanInTheLoopRequestEvent` / `ResponseEvent` — HITL pause/resume
- `BotInTheLoopRequestEvent` / `ResponseEvent` — bot channel escalation
- `AgentInTheLoopRequestEvent` / `ResponseEvent` — agent-to-agent delegation
- Custom events: inherit from `ControlEvent`, define payload fields

**`UserMessageEvent` is a chat UI contract.** It is the entry point every chat interface (OpenWebUI, Teams, Slack,
WebChat) must publish and render. Keep its payload minimal — extending it (or subclassing it) raises the bar for every
chat client. If an agent needs a richer, non-chat entry payload (e.g. from a custom domain front-end or from another
agent delegating via `AgentInTheLoop`), subclass `StartEvent` directly and accept `UserMessageEvent | YourStartEvent` on
the relevant steps.

## i18n

- `AgentLocaleString.from_i18n_path()` for agent/step `name` and `description`
- Translation files: `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/*.{locale}.yml` (4 locales: de, en, fr,
  it)
- `AgentLocaleHandler` extends `LocaleHandler` with agent-specific translation paths
- Injected into steps via DI: declare `t: LocaleHandler` or `t: AgentLocaleHandler` as a parameter

## Pre-Built Agents

| Agent                        | Purpose                                                      | Key Pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RAGAgent**                 | Knowledge QA with retrieval                                  | Multi-source retrieval + reranking + user/org memory + opted-in self-awareness (meta-question gate). Conversation metadata: title is an early fan-out `@step` (anchored on the pre-answer `LimitChatHistoryEvent`), follow-up questions are generated inline in the terminal step — both best-effort. The meta-question branch gets metadata too: title via a parallel `@step` on `MetaQuestionDetectedEvent`, follow-ups inline in `answer_meta_question_step` (see ADR `2026_06_18`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **LLMWrappingAgent**         | Simple LLM chat passthrough                                  | Minimal 2-step workflow, no retrieval                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **ExpertAskingAgent**        | Human expert escalation                                      | BotInTheLoop + iterative refinement + org memory                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **ExpertRAGAgent**           | RAG with expert fallback                                     | RAGAgent steps + HITL consent + AgentInTheLoop                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **FewShotAgent**             | Pattern-matching with examples                               | Suitability guard + few-shot example injection                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **NamespaceSelectionAgent**  | LLM-driven knowledge routing                                 | HITL namespace approval + ThreadContext + RAG delegate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **RetrievalAgent**           | Pure document retrieval (no LLM)                             | Retrieval-only, returns structured context                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **MemoryWriterAgent**        | System agent: async user-memory persistence (issue #1179)    | Non-discoverable; triggered by `MemoryStorageRequestedEvent` from RAG/ExpertRAG when `enable_async_memory_storage` is on; rebuilds the origin agent's `AgentMemory` and writes off the chat critical path                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **ImapAgent**                | Non-conversational IMAP mail agent (read/move + draft-reply) | Two independent, programmatically-started chains: **read/move** (`ReadMailStartEvent` → list unread → fetch the oldest message with S3-stored attachments → optionally move to the processed folder, creating that folder if it does not exist) and **draft** (`DraftMailStartEvent` → draft LLM replies for a batch of the oldest not-yet-drafted messages, `APPEND` to drafts, flag the source). Both chains order candidates oldest-sent-first before applying their limit (server `SORT DATE`, else client-side). Read-only IMAP (`BODY.PEEK`, source stays unread), at-least-once (append before flag), never sends. Grouped `ImapClientConfig`/`DraftEmailSettings` config in `packages/core/imap/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **EmailClassificationAgent** | Non-conversational mailbox triage (issue #1637)              | Files every unread message into the folder for its category. Categories are a `MailCategory` repeater (name, folder, description) — the description is what the model classifies on. The model returns an *index* into the configured list, never a folder name, which is what contains prompt injection from untrusted mail. One route to the configured fallback folder: the model explicitly answering "none fit" (a self-reported confidence score was measured and removed — see the ADR). Filing is the dedup — every message leaves the inbox, so a re-run is a no-op and a half-failed batch is safe. One looping step (runtime-variable count), connection closed across the LLM calls. Never sends. **Schedulable** (issue #1638): the entry step accepts `ClassifyMailStartEvent \| CronStartEvent`, which is the whole opt-in — the `cron` field the scheduler reads lives on the `AgentConfig` base and is injected by `AgentRunner`, not declared here. Because scheduling makes overlapping runs reachable, a `MailboxRunLease` (`imap/mailbox_run_lease.py`, Redis `SET NX EX`; renew and release are Lua so the holder check and the write are one round trip) lets one run at a time hold a profile's mailbox — filing is only the dedup *between* runs, and mail stays unread until it moves. The work runs under `lease.heartbeat(...)`, which renews for as long as its body does anything, so the TTL bounds crash recovery rather than run length; per-phase renewal was not enough, since the batch fetch and the filing pass have no per-item hook. A lost lease raises `MailboxLeaseLostError` *before* filing — the only phase that mutates the mailbox. Released by whichever step returns the terminal `StopEvent`. **Drafts replies per category** (issue #1639): `MailCategory.draft_reply` opts a category in, and `draft_replies_step` (which replaced `finish_classification_step` — two steps on one event would both fire) appends a threaded draft per opted-in message; `finish_drafting_step` is the other terminal step. It reads each message back from the S3 archive rather than IMAP, because the UID died with the `MOVE` and a body has no business on a persisted event; filing, not a flag, is the dedup. Attachment text is optional (`include_attachments`), routed by core's `DocumentLoaderSelector` (PDF/image → MinerU, Office → MarkItDown), floored at `min_attachment_bytes` so signature logos cost nothing, and a textless image is reported in the prompt's inventory rather than dropped. `DraftPromptBuilder` fits the prompt to `number_of_input_tokens`, sacrificing attachment extracts before trimming the body. **Bounded and isolated per message**: both prompts trim untrusted mail to a token budget (`TokenBudget` in `imap/token_budget.py`, shared by `DraftPromptBuilder` and `MailClassifier`) and cap the subject, because the subject sits in the part neither trims. `MailClassifier.classify` and `_compose_one` never raise: a message that cannot be classified gets `ClassificationOutcome.FAILED` and is filed into `failure_folder`, and one that cannot be drafted is skipped. Both matter because filing is the only dedup — a raise before filing leaves the message unread, and `list_unread` re-selects it oldest-first on every run forever, blocking every message behind it. `_validate` now constructs the `DraftPromptBuilder` up front, so a budget too small to work fails before the batch is classified and filed rather than after. |

Each agent has: `agents/{snake_name}/` (implementation), `app/{snake_name}/main.py` (entry point),
`agents/{snake_name}/tests/` (BDD tests).

**System (non-discoverable) agents**: set `discoverable: ClassVar[bool] = False` on the agent class so the runner skips
discovery — the agent never registers a user-facing blueprint in the Admin UI but still subscribes to and processes its
control events. Used for programmatically-triggered agents like `MemoryWriterAgent`. Such an agent's config bakes its
identity as non-configurable primitives in `as_form()` (agent_id/name/description as plain values, not FormKit
elements), so `deep_merge(non_configurable, {})` yields a valid runtime config with no `agent_configs` DB record — no
config seeder needed.

## Playground

- `playground/agent/` — Production-like agents (bot_in_the_loop_agent, hitl_demo_agent, cron_demo_agent)
- `playground/minimal_workflow/` — **START HERE**. Self-contained pattern examples: `simple_workflow`,
  `conditional_workflow`, `human_in_the_loop_workflow`, `agent_in_the_loop_workflow`, `fan_out_workflow`,
  `precondition_workflow`, `bounded_loop`, `context_workflow`, `configured_workflow`, `custom_start_stop_events`,
  `discoverable_workflow`, `displaying_workflow`, `multi_locale_workflow`, `optional_workflow`,
  `organization_memory_workflow`, `semantic_workflow`, `user_memory_workflow`, `multistep_human_in_the_loop_workflow`,
  `long_running_agent`, `llama_index_workflow`, `mcp_react_workflow`
- `playground/performance/` — Load testing with PerformanceTestingAgent

## Testing

- BDD with pytest-bdd: `.feature` files (Gherkin) + `test_*.py` (step implementations)
- `AgentTestRunner` (extends `AgentRunner`): sandboxed test environment with `test_run()` context manager
- Mocks the config client so tests don't need the API running
- `@async_test` decorator from `swiss_ai_hub.core.testing.asyncio_utils.bdd` wraps pytest-bdd steps for async
- Pattern: `Given` creates runner → `When` sends event via `send_event_from_topic()` → `Then` asserts
  `has_start_event`/`has_stop_event`/`get_events_of_class()`
- `wait_for_event(event_class, timeout)` for async assertions
- `ensure_dependent_agent_stream(agent_class)` for agent-in-the-loop tests
- Test markers: `self_hosted`, `slow`, `integration`, `experimental`, `flaky`

## New Agent Checklist

1. Create agent class inheriting `Agent`, set `name`/`description`/`icon` with `AgentLocaleString`
2. Add `@step()` methods consuming/producing events
3. Create `AgentConfig` subclass with `as_form()` (form duality)
4. Create custom events inheriting `ControlEvent`/`StartEvent`/`StopEvent`
5. Add i18n translations in `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/`
6. Create `app/my_agent/main.py` entry point with `AgentRunner`
7. (Conversational agents) Add self-awareness: define `detect_meta_question_step` / `answer_meta_question_step`
   (delegating to the shared free functions) and gate raw `UserMessageEvent` entry steps with `NotAMetaQuestionEvent` —
   a required dependency for `UserMessageEvent`-only agents, or `_clear: NotAMetaQuestionEvent | None = None` +
   `check_passed_meta_question_gate` for agents that also accept a programmatic start (see the Built-in Self-Awareness
   section above)
8. Write BDD tests with `AgentTestRunner`
9. Run `make test`

## Essential Files

**SDK Framework**:

- Agent base: `packages/agent/swiss_ai_hub/agent/agents/agent.py`
- Step decorator: `packages/agent/swiss_ai_hub/agent/workflow/decorators/step.py`
- Precondition decorator: `packages/agent/swiss_ai_hub/agent/workflow/decorators/precondition.py`
- AgentDispatcher: `packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`
- AgentRunner: `packages/agent/swiss_ai_hub/agent/runners/agent_runner.py`
- AgentTestRunner: `packages/agent/swiss_ai_hub/agent/runners/agent_test_runner.py`
- RunContext: `packages/agent/swiss_ai_hub/agent/context/run/run_context.py`
- ThreadContext: `packages/agent/swiss_ai_hub/agent/context/thread/thread_context.py`
- AgentLocaleString: `packages/agent/swiss_ai_hub/agent/i18n/agent_locale_string.py`
- AgentRunTracer: `packages/agent/swiss_ai_hub/agent/tracing/agent_run_tracer.py`

**From packages/core** (config & form system):

- DispatchableWorkflow: `packages/core/swiss_ai_hub/core/workflow/dispatchable_workflow.py`
- AgentConfig: `packages/core/swiss_ai_hub/core/agents/agent_config.py`
- Form base: `packages/core/swiss_ai_hub/core/form/form.py`
- FormKit elements: `packages/core/swiss_ai_hub/core/form/elements/`
- Form constraints: `packages/core/swiss_ai_hub/core/form/constraints.py`
- ConfigSpecs (announced schema, shared with processes and ingestors):
  `packages/core/swiss_ai_hub/core/form/config_specs.py`
- AgentConfigClient (RPC): `packages/core/swiss_ai_hub/core/rpc/agent_config_client.py`
- AgentConfigEntityDocument: `packages/core/swiss_ai_hub/core/persistence/agents/agent_config_entity_document.py`
- EventDisplayer: `packages/core/swiss_ai_hub/core/displayers/event_displayer.py`
- AgentMemory: `packages/core/swiss_ai_hub/core/generative_ai/memory/agent_memory.py`
- Topics: `packages/core/swiss_ai_hub/core/topics/agents/`
- Topic managers: `packages/core/swiss_ai_hub/core/topic_managers/agents/`

**From packages/api** (config responder):

- AgentConfigResponder: `packages/api/swiss_ai_hub/api/rpc/agent_config_responder.py`

**Reference implementation**:

- RAGAgent: `packages/agent/swiss_ai_hub/agent/agents/rag_agent/rag_agent.py`
- RAGAgentConfig: `packages/agent/swiss_ai_hub/agent/agents/rag_agent/configs/rag_agent_config.py`
- Self-awareness step functions: `packages/agent/swiss_ai_hub/agent/self_awareness/self_awareness_step_functions.py`
- Shared mailbox step functions: `packages/agent/swiss_ai_hub/agent/imap/step_functions.py` (`do_list_unread`,
  `do_fetch_and_archive`, `do_file_message` for one message, `do_file_messages` for a whole batch on one connection —
  used by both mailbox blueprints). `do_fetch_and_archive` archives and strips each message before fetching the next, so
  the returned `parsed` carries no raw or attachment bytes for a batch caller to hold across its LLM calls; pass
  `skip_vanished=True` to drop a UID another client expunged mid-run instead of failing the whole batch
- Self-awareness gate: `packages/agent/swiss_ai_hub/agent/self_awareness/meta_question_gate.py`

**Playground patterns**: `playground/minimal_workflow/`
