---
name: scaffold-agent
description: >-
  Generate a new AI agent with all boilerplate (agent class, events, config with form duality,
  memory, LLM streaming, i18n, BDD tests, entry point). Includes pattern catalog, execution
  model reference, and implementation checklist. Use when user says "create new agent",
  "scaffold an agent", "generate agent boilerplate", "add AI agent", "new workflow agent",
  or "build an agent for X". Do NOT use for debugging agents (use /debug-agent), event
  infrastructure (use /nats-events), or process orchestration (use /scaffold-process).
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New AI Agent

Generate all boilerplate for a new AI agent. The agent name/description should be provided via `$ARGUMENTS`.

## Before You Start

Read the agent scope guide: `aihub_agent/CLAUDE.md`

Study existing agents for reference patterns:

- **Minimal reference**: `aihub_agent/playground/minimal_workflow/simple_workflow/SimpleWorkflow.py`
- **Production reference**: `aihub_agent/aihub_agent/agents/RagAgent/RAGAgent.py`
- **Pattern index**: `aihub_agent/playground/minimal_workflow/` (20 self-contained examples)

______________________________________________________________________

## Architecture & Mental Model

Agents are **Dispatchable Workflows** — directed acyclic graphs where nodes are `@step` methods and edges are typed
Events. The framework is a custom workflow engine — not LlamaIndex workflows.

**Fundamental invariant**: Steps declare data requirements, not execution order. The dispatcher decides when to execute
each step based on which events are available.

**Inheritance chain**: `DispatchableWorkflow` → `Agent` → your concrete agent

**Key design properties:**

- **Stateless**: Each step gets a fresh `agent()` instance. Never use `self` for state.
- **Distributed**: Consecutive steps may run on different servers via NATS/JetStream load balancing.
- **Event-driven**: All inter-step communication is through typed events. No shared memory, no direct calls.
- **Data-injected**: Step parameters are resolved by the dispatcher via dependency injection (type annotation → value).

**Additional invariant properties:**

- **Any step can depend on any event**, including the original `StartEvent`, regardless of how many steps have executed
  since. Events persist until run completion (Rule R6).
- **Parallel execution is automatic**: Steps with independent dependencies execute concurrently. The workflow is a
  dependency graph, not a sequence.
- **Multiple steps for the same run may execute in parallel** if their dependencies are independently satisfied.

**Critical difference — think data dependencies, not control flow:**

```python
# WRONG mental model (imperative, top-down):
# "First do A, then B, then C"
async def run(self):
    a = await self.step_a()
    b = await self.step_b(a)
    c = await self.step_c(b)

# CORRECT mental model (declarative, bottom-up):
# "C needs B's output. B needs A's output. A needs the start event."
@step()
async def step_a(self, event: StartEvent) -> EventA: ...

@step()
async def step_b(self, event: EventA) -> EventB: ...

@step()
async def step_c(self, event: EventB) -> StopEvent: ...
```

**Avoid pass-through pollution** — each event should contain only the data it semantically represents:

```python
# WRONG (top-down thinking, passing data forward):
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes, user_query=event.user_query)  # Passing query forward!

@step()
async def respond(self, event: RetrieveEvent) -> StopEvent:
    return await generate(event.user_query, event.nodes)  # Using passed-through data

# CORRECT (bottom-up thinking, direct dependencies):
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes)  # Only retrieval-specific data

@step()
async def respond(
    self,
    retrieve_event: RetrieveEvent,
    user_event: UserMessageEvent,  # Direct dependency on original event
) -> StopEvent:
    return await generate(user_event.user_query, retrieve_event.nodes)
```

**Design approach**: Sketch top-down to understand logical flow, then refine bottom-up to identify true data
dependencies. For each step ask: *What is the minimal set of data this step requires?*

Source: `aihub_lib/aihub_lib/nats/workflow/DispatchableWorkflow.py`, `aihub_agent/aihub_agent/agents/Agent.py`

______________________________________________________________________

## Step 1: Choose Your Pattern

Select the pattern that matches your agent's workflow. Each maps to a playground example.

### Pattern 1: Linear Pipeline

Steps execute in sequence, each consuming the previous step's output.

```python
@step()
async def start_step(self, event: UserMessageEvent) -> EventA: ...
@step()
async def process_step(self, event: EventA) -> EventB: ...
@step()
async def end_step(self, event: EventB) -> StopEvent: ...
```

**Playground**: `playground/minimal_workflow/simple_workflow/`

### Pattern 2: Conditional Branching

A step returns one of several event types based on a condition.

```python
@step()
async def start_step(self, event: StartEvent) -> AboveEvent | BelowEvent:
    if condition:
        return AboveEvent()
    return BelowEvent()

@step()
async def end_step(self, event: AboveEvent | BelowEvent) -> StopEvent: ...
```

**Playground**: `playground/minimal_workflow/conditional_workflow/`

### Pattern 3: Fan-Out / Fan-In

Parallel processing: one step produces multiple events, another collects all results.

```python
@step()
async def fan_out(self, _: StartEvent) -> list[TaskEvent]:
    return [TaskEvent(task=t) for t in tasks]

@step()
async def process(self, event: TaskEvent) -> ResultEvent:
    return ResultEvent(result=process(event.task))  # Runs once per TaskEvent

@step()
async def fan_in(self, results: FixedList(ResultEvent, N)) -> StopEvent:
    # Waits for exactly N results, then fires once
    return StopEvent(combined=[r.result for r in results])
```

**Key**: Use `FixedList(EventType, N)` when the count is known at compile time.

**Playground**: `playground/minimal_workflow/fan_out_workflow/`

### Pattern 4: Precondition Sync

Wait for a dynamic number of events using a precondition function.

```python
def ensure_enough_events(events: list[ParallelEvent], config: MyConfig) -> bool:
    return len(events) == config.expected_count

@step(precondition=ensure_enough_events)
async def collect_step(self, events: list[ParallelEvent]) -> StopEvent: ...
```

**Key**: The precondition function uses the same DI system as `@step` — it can receive events, config, context. The
precondition re-evaluates on each new event arrival until it returns `True`.

**Playground**: `playground/minimal_workflow/precondition_workflow/`

### Pattern 5: Bounded Loop

Iterative processing with a counter-based exit condition.

```python
@step()
async def start_step(self, event: UserMessageEvent, ctx: RunContext) -> BeginEvent:
    await ctx.set("iteration", 0)
    return BeginEvent()

@step()
async def process_step(self, event: BeginEvent) -> ProcessedEvent: ...

@step()
async def decision_step(self, event: ProcessedEvent, ctx: RunContext) -> DoneEvent | BeginEvent:
    count = await ctx.get("iteration", 0) + 1
    await ctx.set("iteration", count)
    if count >= MAX_ITERATIONS or event.is_good_enough:
        return DoneEvent()
    return BeginEvent()  # Loop back

@step()
async def end_step(self, event: DoneEvent) -> StopEvent: ...
```

**Key**: Use `RunContext` for the loop counter. Set `max_executions_per_run` as a safety limit.

**Playground**: `playground/minimal_workflow/bounded_loop/`

### Pattern 6: Human-in-the-Loop (HITL)

Pause workflow to collect human input, then resume. Four HITL subtypes:

| Subtype          | Use Case                | Request Event Class                  | Playground                                                          |
| ---------------- | ----------------------- | ------------------------------------ | ------------------------------------------------------------------- |
| **Input**        | Collect text/form data  | `HumanInTheLoopInput.request`        | `playground/minimal_workflow/human_in_the_loop_workflow/`           |
| **Confirmation** | Yes/No approval         | `HumanInTheLoopConfirmation.request` | —                                                                   |
| **Chat**         | Multi-turn conversation | `HumanInTheLoopChat.request`         | —                                                                   |
| **Multistep**    | Sequential HITL forms   | Custom per step                      | `playground/minimal_workflow/multistep_human_in_the_loop_workflow/` |

```python
@step()
async def start_step(self, event: StartEvent) -> HumanInTheLoopInput.request:
    return HumanInTheLoopInput.invoke(question="Please enter your feedback:")

@step()
async def end_step(self, event: HumanInTheLoopInput.response) -> StopEvent:
    user_data = event.response  # User's text response
    return StopEvent()
```

Source: `aihub_lib/aihub_lib/nats/events/human_in_the_loop/`

#### Multiple HITL Interactions

For workflows requiring multiple human interactions, create distinct subclasses. The dispatcher differentiates steps by
event type—using the same base type for multiple interactions causes ambiguity.

**Step 1: Define custom HITL event pairs**

```python
# events/FirstStepHumanInTheLoop.py
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
```

```python
# events/SecondStepHumanInTheLoop.py
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
```

**Step 2: Use distinct types in the workflow**

```python
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step

from .events.FirstStepHumanInTheLoop import FirstStepHumanInTheLoop
from .events.SecondStepHumanInTheLoop import SecondStepHumanInTheLoop


class MultistepHumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def second_hitl(
        self, event: FirstStepHumanInTheLoop.response
    ) -> SecondStepHumanInTheLoop.request:
        print(f"First response: {event.response}")
        return SecondStepHumanInTheLoop.invoke(question="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print(f"Second response: {event.response}")
        return StopEvent()
```

#### Dynamic HITL Type Selection

When the HITL type depends on runtime conditions, use union return types:

```python
from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopChat,
    HumanInTheLoopConfirmation,
    HumanInTheLoopInput,
)

class HitlDemoAgent(Agent):
    @step()
    async def select_hitl_type(
        self, event: UserMessageEvent
    ) -> HumanInTheLoopInput.request | HumanInTheLoopConfirmation.request | HumanInTheLoopChat.request:
        choice = event.user_query.lower()
        if "confirmation" in choice:
            return HumanInTheLoopConfirmation.invoke("Do you confirm this action?")
        elif "chat" in choice:
            return HumanInTheLoopChat.invoke("What is your response?")
        else:
            return HumanInTheLoopInput.invoke("Please enter your text input:")

    @step()
    async def handle_response(
        self,
        event: HumanInTheLoopInput.response | HumanInTheLoopConfirmation.response | HumanInTheLoopChat.response,
    ) -> StopEvent:
        if isinstance(event, HumanInTheLoopConfirmation.response):
            result = f"Confirmation: {'Yes' if event.response else 'No'}"
        else:
            result = f"Response: {event.response}"
        return StopEvent()
```

### Pattern 7: Bot-in-the-Loop (BITL)

Delegate to a human via Teams/Slack bot channel, then resume with their response.

#### Channel Configuration

BITL requires platform-specific configuration:

**Microsoft Teams:**

```python
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig

teams_config = TeamsConfig(
    channel_id="19:abc123@thread.tacv2",
    tenant_id="12345678-1234-1234-1234-123456789abc",
    bot_id="87654321-4321-4321-4321-cba987654321",
)
```

**Slack:**

```python
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig

slack_config = SlackConfig(
    channel_id="C0123456789",
    service_url="https://slack.botframework.com",
)
```

#### Basic Usage

```python
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

class BotInTheLoopAgent(Agent):
    @step()
    async def request_approval(self, start_event: MyStartEvent) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=start_event.user,
            question="Should the agent proceed with the deployment?",
            channel_config=start_event.channel_config,  # TeamsConfig or SlackConfig
        )

    @step()
    async def handle_response(self, event: BotInTheLoop.response) -> StopEvent:
        answer = event.response
        if event.responder:
            print(f"Answered by: {event.responder.user_name}")
        return StopEvent()
```

#### Iterative Conversations

BITL supports multi-turn conversations by returning another `BotInTheLoop.request`:

```python
@step()
async def handle_response(
    self, event: BotInTheLoop.response
) -> BotInTheLoop.request | StopEvent:
    if event.response.lower() == "yes":
        return StopEvent()
    else:
        return BotInTheLoop.invoke(
            user=event.request_event.user,
            question="What about now? Ready to proceed?",
            channel_config=event.request_event.channel_config,
        )
```

#### Response Event Structure

| Field           | Type                        | Description                    |
| --------------- | --------------------------- | ------------------------------ |
| `response`      | `str`                       | The user's message text        |
| `request_event` | `BotInTheLoopRequestEvent`  | Original request (for context) |
| `responder`     | `BotInTheLoopResponderInfo` | Who responded                  |

**Responder Information:**

| Field             | Type           | Description                     |
| ----------------- | -------------- | ------------------------------- |
| `user_id`         | `str`          | Platform user ID (Slack/Teams)  |
| `user_name`       | `str`          | Display name                    |
| `additional_info` | `dict \| None` | Platform-specific metadata      |
| `aad_object_id`   | `str \| None`  | Azure AD object ID (Teams only) |

#### BITL vs HITL

| Aspect                | HumanInTheLoop            | BotInTheLoop                                   |
| --------------------- | ------------------------- | ---------------------------------------------- |
| **Platform**          | Agent UI (web/mobile)     | Teams / Slack                                  |
| **User context**      | Same session user         | External channel users                         |
| **UI options**        | Input, Confirmation, Chat | Text message only                              |
| **Response tracking** | Implicit (same user)      | Explicit (`responder` field)                   |
| **Use case**          | In-app approvals          | Cross-platform notifications, team escalations |

**Requires**: A bot agent configured with the appropriate channel. See `/bot-framework` for bot setup.

**Playground**: `playground/agent/BotInTheLoopAgent/`

### Pattern 8: Agent-in-the-Loop (AITL)

Delegate to another agent, then resume with their result.

```python
@step()
async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
    return AgentInTheLoop.invoke(
        agent_class="WorkerAgent",
        agent_id="worker-1",
        start_event=UserMessageEvent(message=event.message),
    )

@step()
async def handle_response(self, response: AgentInTheLoop.response) -> StopEvent:
    worker_result = response.stop_event
    return StopEvent()

@step()
async def handle_exception(self, exception: AgentInTheLoop.exception) -> StopEvent:
    return StopEvent(error=str(exception.exception_event))
```

**Key**: Always handle both `.response` and `.exception` from the delegated agent.

**Playground**: `playground/minimal_workflow/agent_in_the_loop_workflow/`

______________________________________________________________________

## Step 2: Create Directory Structure

Extract the agent name from `$ARGUMENTS`. Convert to `CamelCase` for classes, `snake_case` for directories.

```
aihub_agent/aihub_agent/agents/{AgentName}/
├── {AgentName}.py              # Agent class
├── configs/
│   └── {AgentName}Config.py    # AgentConfig subclass with form duality
├── events/
│   └── {EventName}.py          # One file per custom event (one class per file)
└── tests/
    ├── features/
    │   └── {agent_name}.feature  # BDD scenario
    └── test_{agent_name}.py      # Test implementation

aihub_agent/app/{agent_name}/
└── main.py                     # Entry point with AgentRunner

aihub_agent/i18n/translations/agent/
├── {agent_name}.de.yml
├── {agent_name}.en.yml
├── {agent_name}.fr.yml
└── {agent_name}.it.yml
```

**Naming conventions:**

- One class per file, file name matches class name: `MyAgent.py` contains `class MyAgent`
- Events: `{AgentName}{Action}Event.py` — e.g., `SummaryGeneratedEvent.py`
- Config: `{AgentName}Config.py`

______________________________________________________________________

## Step 3: Define Events

### Choosing the Right Base Event

| Base Class                    | When to Use                                        | Dispatched Via        |
| ----------------------------- | -------------------------------------------------- | --------------------- |
| `ControlEvent`                | Internal workflow state transitions                | JetStream (durable)   |
| `DisplayEvent`                | UI-only feedback (progress, status)                | NATS Core (ephemeral) |
| `ControlAndDisplayEvent`      | Workflow transition + visible to user              | Both                  |
| `StartEvent` (extends C&D)    | Run lifecycle: entry point                         | Both                  |
| `StopEvent` (extends C&D)     | Run lifecycle: termination                         | Both                  |
| `SemanticEvent` (extends C&D) | OpenInference observability (LLM, Retriever, etc.) | Both                  |
| `HumanInTheLoopRequestEvent`  | HITL pause request                                 | Both                  |
| `BotInTheLoopRequestEvent`    | BITL delegation                                    | Both                  |
| `AgentInTheLoopRequestEvent`  | AITL delegation                                    | Both                  |

**Complete event selection guide** (from the report):

| If your event represents...      | Inherit from                                                  |
| -------------------------------- | ------------------------------------------------------------- |
| Workflow start condition         | `StartEvent`                                                  |
| User message initiating workflow | `UserMessageEvent`                                            |
| Workflow termination             | `StopEvent`                                                   |
| Error/failure                    | `ExceptionEvent`                                              |
| LLM invocation result            | `LLMEvent`                                                    |
| LLM terminal response            | `LLMStopEvent`                                                |
| Document retrieval               | `RetrieverEvent`                                              |
| Reranking operation              | `RerankerEvent`                                               |
| Embedding generation             | `EmbeddingEvent`                                              |
| Tool/function call               | `ToolEvent`                                                   |
| Guardrail check                  | `GuardEvent`                                                  |
| Chain execution                  | `ChainEvent`                                                  |
| Human approval needed            | `HumanInTheLoopRequestEvent`                                  |
| Agent delegation                 | `AgentInTheLoopRequestEvent`                                  |
| Memory retrieval                 | `RetrieveUserMemoryEvent` / `RetrieveOrganizationMemoryEvent` |
| Memory storage                   | `StoreUserMemoryEvent` / `StoreOrganizationMemoryEvent`       |
| Streaming text chunk             | `ChunkEvent`                                                  |
| Agent thought/reasoning          | `ThoughtEvent`                                                |
| Cost information                 | `LLMCostEvent`                                                |
| Generic workflow state           | `ControlAndDisplayEvent`                                      |
| Generic UI update                | `DisplayEvent`                                                |

**Rule of thumb**: If a step consumes it → `ControlEvent`. If only the UI needs it → `DisplayEvent`. If both →
`ControlAndDisplayEvent`. Most custom agent events are `ControlEvent`.

### The Stop Event Constraint

**No step may depend on `StopEvent` or any subclass as an input.** When `StopEvent` is emitted, the run terminates.

```python
# ILLEGAL: Depending on stop event
@step()
async def cleanup(self, stop: LLMStopEvent) -> CleanupEvent:
    ...  # Never executes

# CORRECT: Use non-stop intermediate event, then explicit stop
@step()
async def respond(self, event: Input) -> LLMEvent:  # Not LLMStopEvent
    return await displayer.display_llm_stream(..., as_stop_step=False)

@step()
async def cleanup(self, llm: LLMEvent) -> CleanupEvent:
    ...

@step(precondition=cleanup_complete)
async def finalize(self, cleanup: CleanupEvent) -> StopEvent:
    return StopEvent()
```

### Custom Event Template

Create one file per event in `agents/{AgentName}/events/`:

```python
# aihub_agent/aihub_agent/agents/{AgentName}/events/{EventName}.py
from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class {EventName}(ControlEvent):
    """Carries {description} from step X to step Y."""
    field_name: str
    another_field: list[str] = []
```

Events auto-register on import — no manual registration needed. See `/nats-events` for the full event hierarchy.

### Events as Flow Carriers

Events serve two distinct purposes:

1. **Data carriers:** Transporting values between steps
2. **Flow carriers:** Controlling execution order independent of data

A step may depend on an event solely to ensure execution ordering:

```python
class PathA(Event):
    pass  # No fields - pure flow control

@step()
async def handle_path_a(self, _: PathA, original: StartEvent) -> StopEvent:
    # Underscore signals: "I need this event for flow control, not data"
    process(original.data)
    return StopEvent()
```

The `_: EventType` convention indicates dependency on an event's existence rather than its contents. Essential for
conditional branching, sequencing without data coupling, and synchronization barriers.

______________________________________________________________________

## Step 4: Create Agent Class

```python
# aihub_agent/aihub_agent/agents/{AgentName}/{AgentName}.py
from typing import ClassVar

from aihub_lib.nats.events.control.stop.StopEvent import StopEvent
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.i18n.AgentLocaleString import AgentLocaleString
from aihub_agent.workflow.decorators.step import step

from .events.{EventName} import {EventName}


class {AgentName}(Agent):
    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.{agent_name}.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.{agent_name}.metadata.description"
    )
    icon: ClassVar[str] = "mage:robot"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.start"),
        description=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.start_description"),
        icon="mage:play",
    )
    async def start_step(self, event: UserMessageEvent) -> {EventName}:
        return {EventName}(field_name=event.message)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.end"),
        icon="mage:check",
    )
    async def end_step(self, event: {EventName}) -> StopEvent:
        return StopEvent()
```

### @step Decorator Parameters

| Parameter                | Type                          | Default | Purpose                                          |
| ------------------------ | ----------------------------- | ------- | ------------------------------------------------ |
| `name`                   | `LocaleString \| None`        | `None`  | UI display name for the step                     |
| `description`            | `LocaleString \| None`        | `None`  | UI description                                   |
| `icon`                   | `str \| None`                 | `None`  | Iconify icon name                                |
| `precondition`           | `Callable[..., bool] \| None` | `None`  | Async guard function — delays execution if False |
| `max_executions_per_run` | `int \| None`                 | `None`  | Limits re-execution count (None = unlimited)     |
| `stop_on_error`          | `bool`                        | `True`  | Publish ExceptionEvent on error                  |

Source: `aihub_agent/aihub_agent/workflow/decorators/step.py`

### Step Return Types

| Return Type        | Behavior                            |
| ------------------ | ----------------------------------- |
| `EventA`           | Single event published              |
| `EventA \| EventB` | One event published (branching)     |
| `list[EventA]`     | Multiple events published (fan-out) |
| `None`             | Side-effect only, no event          |

### Step Parameter Types

The dispatcher resolves parameters by type annotation. Declare what you need:

| Type Annotation                        | What Gets Injected                               |
| -------------------------------------- | ------------------------------------------------ |
| Event subclass (e.g., `MyEvent`)       | Matched from event history by type               |
| `MyEvent \| None`                      | Optional — `None` if not yet available           |
| `list[MyEvent]`                        | All events of that type (may be empty)           |
| `FixedList(MyEvent, N)`                | Exactly N events (blocks until all arrive)       |
| `AgentConfig` subclass                 | Merged runtime config for this run               |
| `StepConfig` subclass                  | Step-specific config from AgentConfig            |
| `RunContext`                           | Per-run ephemeral state (Redis, cleaned on stop) |
| `ThreadContext`                        | Per-thread persistent state (Redis, 30d TTL)     |
| `EventDisplayer`                       | Emit display events for frontend streaming       |
| `LocaleHandler` / `AgentLocaleHandler` | i18n handler in the run's locale                 |
| `AgentMemory`                          | User and organization memory access              |
| `AgentInstanceTopic`                   | NATS topic info for this event                   |

Source: `AgentDispatcher._get_parameter_value()` in `aihub_agent/dispatchers/AgentDispatcher.py`

### Event Resolution Strategy

When binding events to parameters:

1. **Fixed Collection:** `FixedList(Event, N)` blocks until exactly *N* events available, then returns all *N*
2. **Unbounded List:** `list[Event]` returns all events of that type currently available; step re-executes on each new
   arrival
3. **Single Instance:**
   - If the triggering event matches the parameter type, that instance is used
   - Otherwise, the most recently created event of that type is used

**Ordering Guarantee:** Events in list parameters are ordered by arrival time.

### The Six Execution Rules

| Rule | Name                     | Implication for Your Code                                                                                                           |
| ---- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| R1   | Minimum Viable Input     | Step fires as soon as required params are satisfied — don't assume order                                                            |
| R2   | Re-execution on New Data | Optional params cause re-execution when they arrive — use preconditions                                                             |
| R3   | List Parameter Semantics | `list[E]` triggers on each new event arrival — a list of length 1 satisfies list[T]. Use `FixedList(E, N)` for deterministic fan-in |
| R4   | StopEvent Constraint     | No events may be published after StopEvent. No step may depend on StopEvent as input                                                |
| R5   | Precondition Override    | Preconditions re-evaluate on each new event arrival, delaying execution until satisfied. Deadlock if never satisfied                |
| R6   | Event Persistence        | All events persist until run completion. Late steps can access early events                                                         |

For debugging execution issues, see `/debug-agent`.

______________________________________________________________________

## Step 5: Create Config

```python
# aihub_agent/aihub_agent/agents/{AgentName}/configs/{AgentName}Config.py
from typing import Annotated, Self

from pydantic import Field

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.constraints import Ge, Le
from aihub_lib.nats.events.form.elements.InputNumber import InputNumber
from aihub_lib.nats.events.form.elements.InputText import InputText
from aihub_lib.nats.events.form.elements.ModelSelect import ModelSelect


class {AgentName}Config(AgentConfig):
    model_name: Annotated[str | ModelSelect, Field(description="LLM model")] = "gpt-4o"
    temperature: Annotated[float | InputNumber, Field(description="LLM temperature"), Ge(0.0), Le(2.0)] = 0.7
    system_prompt: Annotated[str | InputText, Field(description="System prompt")] = "You are a helpful assistant."

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            **base.model_dump(),
            model_name=ModelSelect(label=LocaleString(en="Model", de="Modell", fr="Modèle", it="Modello")),
            temperature=InputNumber(
                label=LocaleString(en="Temperature", de="Temperatur", fr="Température", it="Temperatura"),
                min=0.0,
                max=2.0,
                step=0.1,
            ),
            system_prompt=InputText(
                label=LocaleString(en="System Prompt", de="Systemprompt", fr="Prompt système", it="Prompt di sistema"),
            ),
        )
```

### Form Duality Rules

- **Field types**: Always `primitive_type | FormkitElement` union (e.g., `str | InputText`)
- **Constraints**: Use `Ge()`, `Le()`, `Gt()`, `Lt()`, `MinLen()`, `MaxLen()`, `Pattern()` from
  `aihub_lib.nats.events.form.constraints` — NOT Pydantic's `ge=`, `le=`
- **Configurable fields**: Set to a FormkitElement in `as_form()` → editable in Admin UI
- **Non-configurable fields**: Set to a primitive in `as_form()` → deployment-fixed, baked in
- **Labels**: All labels must be `LocaleString` with de, en, fr, it

### StepConfig

For step-specific configuration, nest a `StepConfig` subclass:

```python
from aihub_lib.agents.AgentConfig import StepConfig

class MyStepConfig(StepConfig):
    threshold: Annotated[float | InputNumber, Field(description="Threshold")] = 0.5

class {AgentName}Config(AgentConfig):
    my_step_settings: MyStepConfig = MyStepConfig()
```

The dispatcher auto-extracts `StepConfig` fields and injects them into steps that declare the matching type.

### FormKit Elements Reference

From `aihub_lib/nats/events/form/elements/`:

- **Input**: `InputText`, `InputNumber`, `Textarea`, `Password`, `InputMask`, `InputOtp`
- **Selection**: `Select`, `MultiSelect`, `CascadeSelect`, `Checkbox`, `ToggleSwitch`, `ToggleButton`, `RadioButton`,
  `SelectButton`, `Listbox`
- **Specialized**: `ModelSelect` (LLM picker), `AgentSelector`, `KnowledgeDatabaseSelector`, `VectorStoreInput`,
  `IconSelector`, `LocaleInput` (multi-language), `ColorPicker`, `DatePicker`, `Knob`, `Rating`, `Slider`
- **Layout**: `Group` (auto-created from nested `Form`), `Repeater` (auto-created from `list[Form]`)

Source: `aihub_lib/aihub_lib/agents/AgentConfig.py`, `aihub_lib/aihub_lib/nats/events/form/Form.py`

______________________________________________________________________

## Step 6: Create Entry Point

```python
# aihub_agent/app/{agent_name}/main.py
import asyncio

from aihub_agent.agents.{AgentName}.{AgentName} import {AgentName}
from aihub_agent.agents.{AgentName}.configs.{AgentName}Config import {AgentName}Config
from aihub_agent.runners.AgentRunner import AgentRunner


async def main():
    runner = AgentRunner(agent_type={AgentName}, agent_config={AgentName}Config.as_form())
    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
```

Source: `aihub_agent/aihub_agent/runners/AgentRunner.py`

______________________________________________________________________

## Step 7: Add i18n

Create translation files in `aihub_agent/i18n/translations/agent/`:

```yaml
# {agent_name}.en.yml
en:
  agent:
    {agent_name}:
      metadata:
        name: "{Agent Display Name}"
        description: "{Agent description for Admin UI}"
      steps:
        start: "Start"
        start_description: "Receives user message and begins processing"
        end: "Finish"
```

Create matching files for `de`, `fr`, `it` locales with translated strings.

Translation lookup order: Local → Agent Scope → Library → English fallback

**Usage in agent class:**

```python
name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.{agent_name}.metadata.name")
```

**Usage in step methods** (via DI):

```python
@step()
async def my_step(self, event: MyEvent, t: LocaleHandler) -> StopEvent:
    localized_text = t("agent.{agent_name}.some_key")
    return StopEvent()
```

Source: `aihub_agent/i18n/AgentLocaleString.py`, `aihub_agent/i18n/translations/agent/`

______________________________________________________________________

## Step 8: LLM Integration

Use `EventDisplayer` for streaming LLM output to the frontend:

```python
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events.semantic.LLMEvent import LLMEvent

@step()
async def llm_step(
    self,
    event: MyEvent,
    config: MyAgentConfig,
    displayer: EventDisplayer,
) -> LLMEvent:
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=config.system_prompt),
        ChatMessage(role=MessageRole.USER, content=event.message),
    ]

    # Stream LLM response with automatic ChunkEvent emission
    llm_response = await displayer.display_llm_stream(
        messages=messages,
        model=config.model_name,
    )

    # Report LLM costs
    await displayer.display_llm_costs(
        model=config.model_name,
        response=llm_response,
    )

    return LLMEvent.from_response(llm_response)
```

**Key**: `display_llm_stream()` handles token-by-token streaming, `<think>` tag parsing, and `ChunkEvent` emission
automatically. `display_llm_costs()` emits `LLMCostEvent` for billing.

### Display Methods

| Method                            | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `display_thought(text)`           | Show internal reasoning                  |
| `display_chunk(text, model_name)` | Stream output incrementally              |
| `display_llm_stream(...)`         | Complete LLM response with cost tracking |

Source: `aihub_lib/displayers/EventDisplayer.py`, `aihub_lib/displayers/stream/StreamProcessor.py`

______________________________________________________________________

## Step 9: Memory Integration

For agents that need to remember across conversations:

```python
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory

@step()
async def retrieve_memory(self, event: UserMessageEvent, memory: AgentMemory) -> MemoryEvent:
    # 1. Retrieve relevant memories
    user_memories = await memory.search_user_memory(query=event.message)
    org_memories = await memory.search_organization_memory(query=event.message)
    return MemoryEvent(user_memories=user_memories, org_memories=org_memories)

@step()
async def respond(self, event: MemoryEvent, ...) -> LLMEvent:
    # 2. Inject memories into chat context
    # 3. Call LLM with memory-augmented context
    ...

@step()
async def store_memory(
    self,
    user_event: UserMessageEvent,
    llm_event: LLMEvent,
    memory: AgentMemory,
    topic: AgentInstanceTopic,
) -> StoreMemoryEvent:
    # 4. Store the exchange as new memory
    await memory.add_user_memory(
        messages=[user_event.message, llm_event.response],
        user_id=topic.agent_id,
    )
    return StoreMemoryEvent()

@step()
async def stop(self, _: StoreMemoryEvent) -> StopEvent:
    # 5. MUST stop AFTER memory is stored (R4: StopEvent is last)
    return StopEvent()
```

**Memory lifecycle**: Retrieve → Inject → Respond → Store → Stop

**Termination constraint**: `StopEvent` must come AFTER memory storage. The memory store step produces an intermediate
event, and the stop step consumes it.

**Playground**: `playground/minimal_workflow/user_memory_workflow/`,
`playground/minimal_workflow/organization_memory_workflow/`

Source: `aihub_lib/generative_ai/memory/AgentMemory.py`

### Complete Memory Pattern with Preconditions

For production agents with configurable memory features:

```python
def check_memory_ready(
    user_event: UserMessageEvent,
    user_memory: RetrieveUserMemoryEvent | None,
    org_memory: RetrieveOrganizationMemoryEvent | None,
    config: AgentConfig,
) -> bool:
    if config.enable_user_memory and user_memory is None:
        return False
    if config.enable_org_memory and org_memory is None:
        return False
    return config.enable_user_memory or config.enable_org_memory

def check_storage_complete(
    llm: LLMEvent,
    stored: StoreUserMemoryEvent | None,
    config: AgentConfig,
) -> bool:
    if config.enable_memory_storage and stored is None:
        return False
    return True


class MemoryAgent(Agent):
    @step(precondition=lambda config: config.enable_user_memory)
    async def retrieve_user_memory(
        self, event: UserMessageEvent, memory: AgentMemory
    ) -> RetrieveUserMemoryEvent:
        result = await memory.search_user_memory(query=event.user_query, user_id=event.user.id)
        return RetrieveUserMemoryEvent.from_memory_search_result(result)

    @step(precondition=lambda config: config.enable_org_memory)
    async def retrieve_org_memory(
        self, event: UserMessageEvent, memory: AgentMemory, config: AgentConfig
    ) -> RetrieveOrganizationMemoryEvent:
        result = await memory.search_organization_memory(
            query=event.user_query, tenant_id=config.tenant_id, tenant_namespace=config.tenant_namespace,
        )
        return RetrieveOrganizationMemoryEvent.from_memory_search_result(result)

    @step(precondition=check_memory_ready)
    async def extend_history(
        self,
        user_event: UserMessageEvent,
        user_memory: RetrieveUserMemoryEvent | None,
        org_memory: RetrieveOrganizationMemoryEvent | None,
        config: AgentConfig,
        t: LocaleHandler,
    ) -> ExtendedHistoryEvent:
        history = user_event.messages
        if config.enable_user_memory and user_memory:
            history = extend_chat_history_with_user_memory(history, user_memory, t)
        if config.enable_org_memory and org_memory:
            history = extend_chat_history_with_organization_memory(history, org_memory, t)
        return ExtendedHistoryEvent(history=history)

    @step()
    async def respond(
        self, event: ExtendedHistoryEvent, displayer: EventDisplayer, config: AgentConfig
    ) -> LLMEvent:
        async with config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                config.llm, llm, event.history, as_stop_step=False
            )

    @step(precondition=lambda config: config.enable_memory_storage)
    async def store_memory(
        self, user_event: UserMessageEvent, llm: LLMEvent, memory: AgentMemory, topic: AgentInstanceTopic,
    ) -> StoreUserMemoryEvent:
        result = await memory.add_user_memory(
            memory=llm.response, user_id=user_event.user.id,
            thread_id=topic.thread_id, display_id=topic.display_id, run_id=topic.run_id,
        )
        return StoreUserMemoryEvent.from_memory_added_object(result)

    @step(precondition=check_storage_complete)
    async def finalize(
        self, llm: LLMEvent, stored: StoreUserMemoryEvent | None, config: AgentConfig
    ) -> StopEvent:
        return StopEvent()
```

______________________________________________________________________

## Step 10: Create Tests

### BDD Feature File

```gherkin
# aihub_agent/aihub_agent/agents/{AgentName}/tests/features/{agent_name}.feature
Feature: {Agent Display Name}

  Scenario: Happy path
    Given an agent "{AgentName}" is running
    When the user sends "test message"
    Then the agent produces a "StopEvent"
    And the agent does not produce an "ExceptionEvent"
```

### Test Implementation

```python
# aihub_agent/aihub_agent/agents/{AgentName}/tests/test_{agent_name}.py
import pytest
from pytest_bdd import given, scenario, then, when

from aihub_lib.nats.events.control.stop.StopEvent import StopEvent
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test

from aihub_agent.agents.{AgentName}.{AgentName} import {AgentName}
from aihub_agent.agents.{AgentName}.configs.{AgentName}Config import {AgentName}Config
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


@scenario("features/{agent_name}.feature", "Happy path")
def test_happy_path():
    pass


@given('an agent "{AgentName}" is running')
@async_test
async def runner(request):
    config = {AgentName}Config.as_form()
    async with AgentTestRunner(agent_type={AgentName}, agent_config=config).test_run() as runner:
        request.node.runner = runner
        yield runner


@when('the user sends "test message"')
@async_test
async def send_message(runner):
    await runner.send_event_from_topic(UserMessageEvent(message="test message"))


@then('the agent produces a "StopEvent"')
@async_test
async def check_stop(runner):
    stop = await runner.wait_for_event(StopEvent, timeout=30)
    assert stop is not None


@then('the agent does not produce an "ExceptionEvent"')
@async_test
async def check_no_exception(runner):
    assert not runner.has_exception_event
```

### Key Test Assertions

| Method                                | Purpose                              |
| ------------------------------------- | ------------------------------------ |
| `runner.has_start_event`              | Check if StartEvent was received     |
| `runner.has_stop_event`               | Check if StopEvent was received      |
| `runner.has_exception_event`          | Check if ExceptionEvent was received |
| `runner.get_events_of_class(cls)`     | Get all events of a specific type    |
| `runner.wait_for_event(cls, timeout)` | Wait for a specific event (async)    |
| `runner.send_event_from_topic(e)`     | Send an event to the agent           |

For AITL tests, use `runner.ensure_dependent_agent_stream(agent_class)`.

### Unit Testing (Direct Step Invocation)

Individual steps can be tested by calling them directly, bypassing the dispatcher:

```python
async def test_retrieve_step():
    agent = MyAgent()
    event = UserMessageEvent(messages=[...], user=..., locale="en")
    memory = Mock(spec=AgentMemory)
    memory.search_user_memory.return_value = MemorySearchResult(...)

    result = await agent.retrieve_step(event, memory)

    assert isinstance(result, RetrieveUserMemoryEvent)
    memory.search_user_memory.assert_called_once()
```

### Integration Testing (Full Workflow)

```python
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

async def test_full_workflow():
    runner = AgentTestRunner(MyAgent, MyAgentConfig())

    async with runner.test_run() as topic:
        await runner.send_event(UserMessageEvent(...))
        stop_event = await runner.wait_for_event(StopEvent, timeout=30)

        assert stop_event is not None
        events = runner.get_events_of_type(RetrieveEvent)
        assert len(events) == 1
```

Source: `aihub_agent/runners/AgentTestRunner.py`

______________________________________________________________________

## Step 11: Register & Verify

Agent discovery is automatic — `AgentRunner` responds to `AgentClassDiscoveryRequestEvent` with the agent's metadata,
form schema, event specs, and workflow graph. No manual registration needed.

**Verify the agent is discoverable:**

```bash
cd aihub_agent && uv run python -c "from aihub_agent.agents.{AgentName}.{AgentName} import {AgentName}; print({AgentName}.get_steps())"
```

______________________________________________________________________

## Implementation Checklist

### Before Coding

- [ ] Read `aihub_agent/CLAUDE.md`
- [ ] Identified the pattern from the catalog above
- [ ] Studied the matching playground example
- [ ] Sketched the event DAG on paper (events as edges, steps as nodes)

### During Coding

- [ ] Agent class extends `Agent` with `name`, `description`, `icon` as `ClassVar[AgentLocaleString]`
- [ ] All `@step` methods are `async`, use type annotations, return events
- [ ] No instance state on `self` — all state in `RunContext` / `ThreadContext`
- [ ] Events inherit from the correct base class (see table above)
- [ ] One class per file, file name matches class name
- [ ] Config uses form duality pattern with `as_form()` classmethod
- [ ] Form constraints use `Ge()`, `Le()` etc. — not Pydantic's `ge=`, `le=`
- [ ] i18n translations in all 4 locales (de, en, fr, it)
- [ ] Entry point in `app/{agent_name}/main.py`

### After Coding

- [ ] Every event produced by a step is consumed by another step (no dead ends)
- [ ] Every execution path reaches `StopEvent`
- [ ] `StopEvent` is returned alone (not in a list with other events)
- [ ] Optional params have synchronization (precondition or max_executions_per_run)
- [ ] BDD tests pass: `cd aihub_agent && uv run pytest tests/ -k "{agent_name}" -v`
- [ ] Agent is importable: `uv run python -c "from aihub_agent.agents.{AgentName}.{AgentName} import {AgentName}"`

______________________________________________________________________

## File Reference

### Framework Files

| File                                                                       | Purpose                               |
| -------------------------------------------------------------------------- | ------------------------------------- |
| `aihub_agent/aihub_agent/agents/Agent.py`                                  | Agent base class                      |
| `aihub_agent/aihub_agent/workflow/decorators/step.py`                      | `@step()` decorator                   |
| `aihub_agent/aihub_agent/workflow/decorators/precondition.py`              | `@precondition()` decorator           |
| `aihub_agent/aihub_agent/dispatchers/AgentDispatcher.py`                   | Core workflow executor (DI, dispatch) |
| `aihub_agent/aihub_agent/runners/AgentRunner.py`                           | Production runner                     |
| `aihub_agent/aihub_agent/runners/AgentTestRunner.py`                       | Test runner                           |
| `aihub_agent/aihub_agent/context/run/RunContext.py`                        | Per-run ephemeral state               |
| `aihub_agent/aihub_agent/context/thread/ThreadContext.py`                  | Per-thread persistent state           |
| `aihub_agent/aihub_agent/i18n/AgentLocaleString.py`                        | Agent i18n strings                    |
| `aihub_lib/aihub_lib/agents/AgentConfig.py`                                | Config base with form duality         |
| `aihub_lib/aihub_lib/nats/events/form/Form.py`                             | Form system                           |
| `aihub_lib/aihub_lib/nats/events/form/elements/`                           | FormKit elements (28 types)           |
| `aihub_lib/aihub_lib/nats/events/form/constraints.py`                      | Form-aware validators                 |
| `aihub_lib/aihub_lib/displayers/EventDisplayer.py`                         | LLM streaming + display events        |
| `aihub_lib/aihub_lib/generative_ai/memory/AgentMemory.py`                  | User + org memory                     |
| `aihub_lib/aihub_lib/nats/workflow/annotations/custom_types/ListOfSize.py` | FixedList for fan-in                  |

### Playground Patterns Index

| Directory                               | Pattern                | Key Concept                             |
| --------------------------------------- | ---------------------- | --------------------------------------- |
| `simple_workflow/`                      | Linear pipeline        | Basic step chaining                     |
| `conditional_workflow/`                 | Branching              | Union return types                      |
| `fan_out_workflow/`                     | Fan-out / fan-in       | `list[E]` return + `FixedList(E, N)`    |
| `precondition_workflow/`                | Precondition sync      | Dynamic event count guard               |
| `bounded_loop/`                         | Bounded loop           | RunContext counter + decision step      |
| `human_in_the_loop_workflow/`           | HITL input             | Form-based human input                  |
| `multistep_human_in_the_loop_workflow/` | HITL multistep         | Sequential human interactions           |
| `context_workflow/`                     | Context management     | RunContext + ThreadContext              |
| `configured_workflow/`                  | Config injection       | AgentConfig + StepConfig DI             |
| `displaying_workflow/`                  | Display events         | EventDisplayer streaming                |
| `semantic_workflow/`                    | Semantic/OpenInference | LLMEvent, RetrieverEvent, RerankerEvent |
| `user_memory_workflow/`                 | User memory            | AgentMemory lifecycle                   |
| `organization_memory_workflow/`         | Org memory             | Organization-scoped memory              |
| `multi_locale_workflow/`                | Internationalization   | LocaleHandler DI                        |
| `agent_in_the_loop_workflow/`           | AITL delegation        | Agent-to-agent delegation               |
| `optional_workflow/`                    | Optional parameters    | `EventType \| None` handling            |

______________________________________________________________________

## Commands

```bash
make pr-ready    # Format + lint + type check
make test        # Run tests (excluding Azure)
make test-all    # Run all tests
```

______________________________________________________________________

## Cross-References

- **Debugging agents**: `/debug-agent` — execution semantics, race conditions, MCP-powered diagnostics
- **Event infrastructure**: `/nats-events` — event hierarchy, subject format, dispatcher architecture
- **Event display components**: `/scaffold-event-display` — frontend visualization for new event types
- **Bot integration**: `/bot-framework` — CompletionHandler, channel setup for BITL patterns
- **Process orchestration**: `/scaffold-process` — multi-entity workflows (agents + humans + programs)
