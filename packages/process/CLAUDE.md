# packages/process - Agentic Process SDK

**Purpose**: SDK for orchestrating multi-entity business processes. Two parts: the framework (`packages/process/`), and
playground examples (`playground/`). Processes delegate work to agents, humans, programs, and other processes — they
never execute work themselves. Business logic lives in the entities (agents, human forms, programs), not in the process.

**Note**: No `app/` directory yet (WIP). Will follow the same entry-point pattern as `packages/agent` once processes are
production-ready.

## Folder Structure

```
packages/process/                         # SDK framework
├── agentic_processes/
│   └── agentic_process.py              # Base class (extends DispatchableWorkflow)
├── context/
│   └── walkthrough/walkthrough_context.py  # Per-walkthrough ephemeral state (Redis, 30d TTL)
├── delegators/                        # Entity delegation system (core differentiator)
│   ├── abstract_process_entity.py     # BaseProcessEntity with In/Out inner classes
│   ├── abstract_entity_delegator.py   # Base delegator (subscription management)
│   ├── agent/                         # Agent.In, Agent.Out, AgentDelegator
│   ├── human/                         # Human.In, Human.Out (no delegator — handled by API)
│   ├── process/                       # Process.In, Process.Out, ProcessDelegator
│   └── program/                       # Program.In, Program.Out (WIP, no delegator — handled by API)
├── dispatchers/
│   └── process_dispatcher.py           # Core workflow executor (config fetch, step dispatch, output routing)
├── i18n/
│   ├── process_locale_string.py       # Multi-locale string resolution for processes
│   ├── process_locale_handler.py      # Locale handler with process translation paths
│   └── translations/process/          # Translation files: {name}.{de|en|fr|it}.yml
├── process/
│   ├── decorators/process_step.py     # @process_step() decorator — defines delegation points
│   └── annotations/extractors/        # Extract In/Out annotations from step signatures
└── runners/
    ├── process_runner.py               # Production runner (NATS, Redis, MongoDB, discovery)
    └── process_test_runner.py         # Test runner (sandboxed, event capture, mock config)

playground/                            # Examples and testing
├── AgenticCVProcess/                  # Complex reference: CV submit → agent analyze → human review → program save
├── agents/                            # Test agents (AgentA, AgentB, AgentC) used by playground processes
├── events/                            # Shared work events for playground processes
├── minimal_processes/                 # 7 self-contained pattern showcases (START HERE)
│   ├── agent_only_process/            # Sequential agent chain
│   ├── human_only_process/            # Human approval workflow
│   ├── agent_to_human_process/        # Agent analysis → human decision
│   ├── human_to_agent_process/        # Human input → agent processing
│   ├── fan_out_process/               # Parallel entity delegation
│   ├── multi_input_process/           # Synchronize multiple entity outputs
│   └── process_sequence/              # Chain processes (process-to-process)
└── testing/                           # SDK integration tests
```

## Process Blueprint vs Process Profile

Same concept as agents — separates **what a process can do** (code) from **how it's configured** (data).

**Process Blueprint** (`process_class`): The Python class. Defines steps, entity delegation, form schema, default
config. One per process type. Discovered when processes come online. Stored in MongoDB `process_classes` collection.

**Process Profile** (`process_id`): A user-created configuration of a blueprint. Unique URL-safe slug, name,
description, icon, and specific settings. Multiple profiles from one blueprint. Stored in MongoDB `process_configs`
collection.

**In code**: `ProcessConfig.process_class` is the blueprint name, `ProcessConfig.process_id` is the profile slug.

## Architecture: Entity-Driven Process Orchestration

This is a custom workflow engine — same `DispatchableWorkflow` base as agents, but processes orchestrate instead of
executing. LlamaIndex is not involved.

**Inheritance chain**: `DispatchableWorkflow` → `AgenticProcess` → concrete processes

**Key design property**: Processes are stateless orchestrators. Everything is decentralized via NATS/JetStream:

- No instance state on the process class
- All state lives in Redis (`WalkthroughContext`) and JetStream (event history)
- `ProcessRunner` subscribes to WorkEvents and delegates to `ProcessDispatcher`
- The dispatcher creates a fresh `process()` instance for each step execution
- Steps consume `WorkEvent`s (entity completed work) and produce `WorkRequestEvent`s (delegate to next entity)

## The Four Entity Types

The delegation system is the core differentiator from agents. Each entity has `In` (receive work) and `Out` (delegate
work) configuration classes:

| Entity      | In (receive from)                       | Out (delegate to)                                      |
| ----------- | --------------------------------------- | ------------------------------------------------------ |
| **Agent**   | `Agent.In(agent_class, agent_id)`       | `Agent.Out(agent_class, agent_id)`                     |
| **Human**   | `Human.In(route, method, start_form?)`  | `Human.Out(user_ids, user_emails, user_roles, notify)` |
| **Program** | `Program.In(route, method)`             | `Program.Out(endpoint, method)` — WIP                  |
| **Process** | `Process.In(process_class, process_id)` | `Process.Out()` — sink, terminates the process         |

All entity configs inherit from `BaseProcessEntity.In` / `BaseProcessEntity.Out` (Pydantic `BaseModel`s).

## The AgenticProcess Class

Minimal and stateless. Only class-level attributes — never instantiated by hand.

```python
class MyProcess(AgenticProcess):
    name: ClassVar[ProcessLocaleString] = ProcessLocaleString.from_i18n_path("process.my_process.name")
    description: ClassVar[ProcessLocaleString] = ProcessLocaleString.from_i18n_path("process.my_process.description")
    icon: ClassVar[str] = "mage:broadcast"

    @process_step(name=LocaleString(en="Delegate to Agent"))
    def start(
        self,
        trigger: Annotated[TriggerWork, Program.In(route="/start", method="POST")],
    ) -> Annotated[MyAgentRequest, Agent.Out(agent_class="MyAgent", agent_id="my_agent")]:
        return MyAgentRequest(start_event=UserMessageEvent(content=trigger.data))

    @process_step(name=LocaleString(en="Finish"))
    def finish(
        self,
        result: Annotated[AgentAWork, Agent.In(agent_class="MyAgent", agent_id="my_agent")],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        return CustomProcessStopEvent(output=result.agent_stop_event.result)
```

`AgenticProcess` provides introspection: `get_events_with_agent_in()`, `get_events_with_human_in()`,
`get_events_with_program_in()`, `get_events_with_process_in()`, `get_events_with_agent_out()`,
`get_events_with_human_out()`, `get_events_with_program_out()` — all cached classmethods that scan `@process_step()`
signatures for entity In/Out annotations.

## The @process_step Decorator

```python
@process_step(
    name=LocaleString(en="My Step"),         # UI display name
    description=LocaleString(en="Does X"),   # UI description
    icon="mage:magic-wand",                  # Iconify icon
)
def my_step(self, work: Annotated[SomeWorkEvent, Agent.In(...)]) -> Annotated[SomeRequest, Human.Out(...)]:
    ...
```

Parameters are simpler than `@step()` for agents — no `precondition`, `max_executions_per_run`, or `stop_on_error`. The
decorator extracts both standard event metadata AND process-specific In/Out tuples from type annotations.

## Step Dependency Injection

The dispatcher resolves `@process_step()` parameters by type annotation. Simpler than agents — only two types:

| Type Annotation          | What Gets Injected                     |
| ------------------------ | -------------------------------------- |
| `WorkEvent` subclass     | Matched from event history by type     |
| `ProcessConfig` subclass | The merged runtime config for this run |

Source: `ProcessDispatcher._build_method_kwargs()` in `dispatchers/process_dispatcher.py`.

## Work Events & Work Request Events

Process-specific event hierarchy (all extend `ProcessEvent`):

**WorkEvent** — signals entity completed work:

- `AgentWorkEvent[TEvent: StopEvent]` — wraps agent's `StopEvent` in `agent_stop_event` field + `submitted_by` topic
- `HumanWorkEvent` — also extends `Form` (same form duality: form elements for UI, primitives for data) + `submitted_by`
  UserIdentity
- `ProgramWorkEvent` — from external programs
- `ProcessWorkEvent[TEvent: ProcessStopEvent]` — wraps sub-process `ProcessStopEvent`

**WorkRequestEvent** — delegates work to entity:

- `AgentWorkRequestEvent[TEvent: StartEvent]` — triggers agent run via `start_event` field. `agent_class`/`agent_id`
  auto-injected by dispatcher from `Agent.Out` config.
- `HumanWorkRequestEvent` — requests user form input. Contains `forms: list[HumanWorkEvent]` with form elements.
  `user_ids`/`user_emails`/`user_roles`/`notify` auto-injected from `Human.Out` config.
- `ProgramWorkRequestEvent` — calls external API (WIP). `endpoint`/`method` auto-injected from `Program.Out` config.

**Lifecycle events**: `ProcessStartEvent`, `ProcessStopEvent`, `ProcessExceptionEvent`.

## Entity Delegators

Delegators bridge between process events and entity-specific events. They subscribe to both directions:

**AbstractEntityDelegator**: Base class. Subscribes to all `WorkRequestEvent`s for the process class, filters by entity
type. Provides `_publish_work_event()` to emit work events back to the process.

**AgentDelegator**: Converts `AgentWorkRequestEvent` → creates agent thread + publishes `StartEvent` to agent. Listens
for agent `StopEvent`s → wraps in `AgentWorkEvent` → publishes back to process.

**ProcessDelegator**: Converts `ProcessWorkEvent` from sub-process completion → publishes work event to parent process.
Handles process-to-process chaining.

**Human/Program**: No delegator classes — handled by the API directly.

## ProcessConfig & Config Lifecycle

`ProcessConfig` inherits from `Form` — same duality pattern as `AgentConfig`. See `packages/agent/CLAUDE.md` for the
full Form Duality, FormKit Elements, and Form Constraints documentation (identical system).

Fields: `process_class`, `process_id`, `name` (LocaleString), `description` (LocaleString), `icon`.

**Config Lifecycle** (parallel to agents):

1. **Definition**: Subclass `ProcessConfig`, annotate fields with `type | FormkitElement` unions, implement `as_form()`
2. **Discovery**: `ProcessRunner` publishes `ProcessClassDiscoveryResponseEvent` with form, specs, entity In/Out specs
3. **Storage**: Admin creates profile via UI → saved to `ProcessConfigEntityDocument` (MongoDB `process_configs`
   collection) with `(process_class, process_id)` compound unique index
4. **Runtime Fetch**: On first `WorkEvent`, dispatcher calls
   `ProcessConfigClient.fetch_config(process_class, process_id)` → NATS RPC (`aihub.rpc.config.process.{class}.{id}`) →
   `ProcessConfigResponder` (API side)
5. **Merge**: `Form.deep_merge(non_configurable_values, submitted_config)` → stored in `WalkthroughContext`
6. **Injection**: `process_config_type.model_validate(merged_dict)` → injected into `@process_step()` methods that
   declare a `ProcessConfig` subclass as a parameter

## ProcessRunner & ProcessDispatcher

**ProcessRunner**: Connects process to infrastructure (NATS, JetStream, Redis, MongoDB — no Milvus). Creates dispatcher,
`AgentDelegator`, and `ProcessDelegator`. Responds to discovery requests. Includes health check server.

```python
runner = ProcessRunner(process_type=MyProcess, process_config=MyProcessConfig.as_form())
await runner.run_forever()
```

**ProcessDispatcher** (extends `BaseDispatcher`): The core workflow executor.

- On first `WorkEvent` (process start): fetches config via NATS RPC, deep-merges, stores in `WalkthroughContext`
- For subsequent `WorkEvent`s: loads config from `WalkthroughContext`
- Finds ready steps via `get_steps_waiting_for_event()`, checks readiness, executes ready steps
- Builds kwargs via DI (events from history + ProcessConfig injection)
- Instantiates a fresh `process()` for each step execution (stateless)
- Routes output events: auto-injects entity-specific fields from Out config (`agent_class`/`agent_id`, `user_ids`,
  `endpoint`, etc.) then publishes via JetStream
- On `ProcessStopEvent`/`ProcessExceptionEvent`: cleans up `WalkthroughContext` and event/step stores

## Topic Hierarchy

NATS subject format:

```
process.{process_class}.{process_id}.{process_walkthrough_id}.{event_type}.{event_name}.{event_id}
```

Where `event_type` is either `work` or `work_request`.

Topic classes form a narrowing hierarchy:

| Class                  | Specificity | Description                                          |
| ---------------------- | ----------- | ---------------------------------------------------- |
| `PartialProcessTopic`  | Loose       | Wildcards allowed, for broad subscriptions           |
| `ProcessClassTopic`    | Medium      | `process_class` specified, may wildcard `process_id` |
| `ProcessInstanceTopic` | Tight       | Fully specified including `process_id`               |

Topic managers mirror the hierarchy: `ProcessTopicManager` → `ProcessClassTopicManager` → `ProcessInstanceTopicManager`
→ `ProcessWalkthroughTopicManager`. See `packages/core/nats/topic_managers/process/`.

## WalkthroughContext

Per-walkthrough ephemeral state in Redis/Valkey. Equivalent of `RunContext` for agents.

- Scoped to `walkthrough_id` (store name: `walkthrough_context_{walkthrough_id}`)
- 30-day TTL
- Uses `async get(key, default)` / `async set(key, value)` / `async delete(key)` API (inherited from `BaseContext`)
- Stores merged process config (`_process_config` key) for the duration of the walkthrough
- Cleaned up on `ProcessStopEvent`

## i18n

- `ProcessLocaleString.from_i18n_path()` for process/step `name` and `description`
- Translation files: `packages/process/swiss_ai_hub/process/i18n/translations/process/*.{locale}.yml` (4 locales: de,
  en, fr, it)
- `ProcessLocaleHandler` extends `LocaleHandler` with process-specific translation paths

## Playground

- `playground/AgenticCVProcess/` — Complex reference: human CV submission → agent analysis → human accept/reject →
  program save
- `playground/minimal_processes/` — **START HERE**. 7 self-contained pattern examples: `agent_only_process`,
  `human_only_process`, `agent_to_human_process`, `human_to_agent_process`, `fan_out_process`, `multi_input_process`,
  `process_sequence`
- `playground/agents/` — Test agents (AgentA, AgentB, AgentC) used by playground processes
- `playground/events/` — Shared work events for playground

## Testing

- BDD with pytest-bdd: `.feature` files (Gherkin) + `test_*.py` (step implementations)
- `ProcessTestRunner` (extends `ProcessRunner`): sandboxed test environment with `test_run()` context manager
- `send_event(work_event, process_walkthrough_id)` to inject events
- Pattern: `Given` creates runner → `When` sends work event via `send_event()` → `Then` asserts
  `has_start_event`/`has_stop_event`/`has_exception_event`/`get_events_of_class()`
- `wait_for_event(event_class, timeout)` for async assertions
- `has_event_of_class(event_class)`, `get_event_of_class(event_class)`, `get_topics(event_class)`
- Test markers: `self_hosted`, `slow`, `integration`, `experimental`, `flaky`

## New Process Checklist

1. Create process class inheriting `AgenticProcess`, set `name`/`description`/`icon` with `ProcessLocaleString`
2. Define custom `WorkEvent`s and `WorkRequestEvent`s (subclass the entity-specific ones)
3. Add `@process_step()` methods with entity `In`/`Out` annotations
4. Create `ProcessConfig` subclass with `as_form()` if custom config needed
5. Add i18n translations in `packages/process/swiss_ai_hub/process/i18n/translations/process/`
6. Write BDD tests with `ProcessTestRunner`
7. Run `make test`

## Essential Files

**SDK Framework**:

- AgenticProcess base: `packages/process/swiss_ai_hub/process/agentic_processes/agentic_process.py`
- Step decorator: `packages/process/swiss_ai_hub/process/process/decorators/process_step.py`
- ProcessDispatcher: `packages/process/swiss_ai_hub/process/dispatchers/process_dispatcher.py`
- ProcessRunner: `packages/process/swiss_ai_hub/process/runners/process_runner.py`
- ProcessTestRunner: `packages/process/swiss_ai_hub/process/runners/process_test_runner.py`
- WalkthroughContext: `packages/process/swiss_ai_hub/process/context/walkthrough/walkthrough_context.py`
- ProcessLocaleString: `packages/process/swiss_ai_hub/process/i18n/process_locale_string.py`

**Entity Delegation**:

- BaseProcessEntity: `packages/process/swiss_ai_hub/process/delegators/abstract_process_entity.py`
- AbstractEntityDelegator: `packages/process/swiss_ai_hub/process/delegators/abstract_entity_delegator.py`
- Agent (In/Out): `packages/process/swiss_ai_hub/process/delegators/agent/agent.py`
- AgentDelegator: `packages/process/swiss_ai_hub/process/delegators/agent/agent_delegator.py`
- Human (In/Out): `packages/process/swiss_ai_hub/process/delegators/human/human.py`
- Program (In/Out): `packages/process/swiss_ai_hub/process/delegators/program/program.py`
- Process (In/Out): `packages/process/swiss_ai_hub/process/delegators/process/process.py`
- ProcessDelegator: `packages/process/swiss_ai_hub/process/delegators/process/process_delegator.py`

**From packages/core** (config, events & topics):

- DispatchableWorkflow: `packages/core/swiss_ai_hub/core/nats/workflow/dispatchable_workflow.py`
- ProcessConfig: `packages/core/swiss_ai_hub/core/processes/process_config.py`
- Form base: `packages/core/swiss_ai_hub/core/nats/events/form/form.py`
- ProcessConfigSpecs: `packages/core/swiss_ai_hub/core/nats/events/discovery/process/process_config_specs.py`
- ProcessConfigClient (RPC): `packages/core/swiss_ai_hub/core/nats/rpc/process_config_client.py`
- ProcessConfigEntityDocument: `packages/core/swiss_ai_hub/core/persistence/process/process_config_entity_document.py`
- WorkEvent: `packages/core/swiss_ai_hub/core/nats/events/work/work_event.py`
- WorkRequestEvent: `packages/core/swiss_ai_hub/core/nats/events/work_request/work_request_event.py`
- AgentWorkEvent: `packages/core/swiss_ai_hub/core/nats/events/work/agent/agent_work_event.py`
- HumanWorkEvent: `packages/core/swiss_ai_hub/core/nats/events/work/human/human_work_event.py`
- Topics: `packages/core/swiss_ai_hub/core/nats/topics/process/`
- Topic managers: `packages/core/swiss_ai_hub/core/nats/topic_managers/process/`

**From packages/api** (config responder):

- ProcessConfigResponder: `packages/api/swiss_ai_hub/api/rpc/process_config_responder.py`

**Playground patterns**: `playground/minimal_processes/`
