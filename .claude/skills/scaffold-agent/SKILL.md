---
name: scaffold-agent
description: >-
  Generate a new AI agent with all boilerplate (agent class, events, config with form duality,
  memory, LLM streaming, i18n, BDD tests, entry point). Includes pattern catalog, execution
  model reference, and implementation checklist. Use when user says "create new agent",
  "scaffold an agent", "generate agent boilerplate", "add AI agent", "new workflow agent",
  or "build an agent for X". Do NOT use for debugging agents (use /debug-agent), event
  infrastructure (use /nats-events), or process orchestration (see packages/process/CLAUDE.md).
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New AI Agent

Generate all boilerplate for a new AI agent. The agent name/description should be provided via `$ARGUMENTS`.

## Before You Start

Read the agent scope guide: `packages/agent/CLAUDE.md`

Study existing agents for reference patterns:

- **Minimal reference**: `packages/agent/playground/minimal_workflow/simple_workflow/simple_agent.py`
- **Smallest chat blueprint** (capabilities):
  `packages/agent/swiss_ai_hub/agent/agents/llm_wrapping_agent/llm_wrapping_agent.py`
- **Production reference**: `packages/agent/swiss_ai_hub/agent/agents/rag_agent/rag_agent.py`
- **Pattern index**: `packages/agent/playground/minimal_workflow/` (20+ self-contained examples)

**Agent classes hold steps only.** A class derived from `Agent` defines `@step` methods and class attributes, nothing
else — helpers go into standalone classes the steps import (or dispatcher-injected dependencies), never onto `self`.
`swiss_ai_hub/agent/agents/tests/test_agent_classes_hold_steps_only.py` fails otherwise.

**Conversational agents (chat UI) use capabilities, not hand-written steps.** Title, follow-ups, meta-question gate,
query condensing, memory, attached files, `#` knowledge references, tool loops and the final stop come from
`Conversation`, `Memory`, `AttachedFiles`, `Knowledge` and `ToolLoop` under
`packages/agent/swiss_ai_hub/agent/capabilities/` — see "Step 4b" below.

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

Source: `packages/core/swiss_ai_hub/core/workflow/dispatchable_workflow.py`,
`packages/agent/swiss_ai_hub/agent/agents/agent.py`

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

Source: `packages/core/swiss_ai_hub/core/events/agent/hitl/`

#### Multiple HITL Interactions

For workflows requiring multiple human interactions, create distinct subclasses. The dispatcher differentiates steps by
event type—using the same base type for multiple interactions causes ambiguity.

**Step 1: Define custom HITL event pairs**

```python
# events/first_step_human_in_the_loop.py
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopInput,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
)


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
```

```python
# events/second_step_human_in_the_loop.py
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopInput,
    HumanInTheLoopInputRequestEvent,
    HumanInTheLoopInputResponseEvent,
)


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
from swiss_ai_hub.core.events.agent import StartEvent, StopEvent

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

from .events.first_step_human_in_the_loop import FirstStepHumanInTheLoop
from .events.second_step_human_in_the_loop import SecondStepHumanInTheLoop


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
from swiss_ai_hub.core.events.agent import (
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
from swiss_ai_hub.core.events.agent import TeamsConfig

teams_config = TeamsConfig(
    channel_id="19:abc123@thread.tacv2",
    tenant_id="12345678-1234-1234-1234-123456789abc",
    bot_id="87654321-4321-4321-4321-cba987654321",
)
```

**Slack:**

```python
from swiss_ai_hub.core.events.agent import SlackConfig

slack_config = SlackConfig(
    channel_id="C0123456789",
    service_url="https://slack.botframework.com",
)
```

#### Basic Usage

```python
from swiss_ai_hub.core.events.agent import BotInTheLoop

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

**Playground**: `playground/agent/bot_in_the_loop_agent/`

### Pattern 8: Agent-in-the-Loop (AITL)

Delegate to another agent, then resume with their result.

```python
@step()
async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
    return AgentInTheLoop.invoke(
        agent_class="WorkerAgent",
        agent_id="worker-1",
        start_event=UserMessageEvent(messages=event.messages, user=event.user, locale=event.locale),
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

Extract the agent name from `$ARGUMENTS`. Convert to `CamelCase` for classes, `snake_case` for files and directories.

```
packages/agent/swiss_ai_hub/agent/agents/{agent_name}/
├── __init__.py                 # Exports {AgentName} and {AgentName}Config
├── {agent_name}.py             # Agent class (@step methods only)
├── configs/
│   └── {agent_name}_config.py  # AgentConfig subclass with form duality
├── events/
│   └── {event_name}.py         # One file per custom event (one class per file)
└── tests/
    ├── features/
    │   └── {agent_name}.feature  # BDD scenario
    └── test_{agent_name}.py      # Test implementation

packages/agent/app/{agent_name}/
├── main.py                     # Entry point with AgentRunner
└── Dockerfile

packages/agent/swiss_ai_hub/agent/i18n/translations/agent/
├── {agent_name}.de.yml
├── {agent_name}.en.yml
├── {agent_name}.fr.yml
└── {agent_name}.it.yml
```

Production agents also get a `run-{agent-name}` target in `packages/agent/Makefile` and a service in the compose
template (`infra/deployment/templates/docker-compose.yml.j2`, then `make generate-compose`). Look at how
`llm_wrapping_agent` is wired through `app/llm_wrapping_agent/` for a complete example. Playground agents live under
`packages/agent/playground/` and use `LocaleString` instead of i18n files.

**Naming conventions:**

- One class per file, snake_case file name matches the class: `my_agent.py` contains `class MyAgent`
- Events: `{action}_event.py` — e.g., `summary_generated_event.py` contains `SummaryGeneratedEvent`
- Config: `{agent_name}_config.py` containing `{AgentName}Config`
- Helper logic that is not a step goes into its own class next to the agent, imported by the steps

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

**`UserMessageEvent` is a chat UI contract.** It is the canonical entry point for chat interfaces (OpenWebUI, Teams,
Slack). Keep its payload minimal — every field added to it (or to a subclass) raises the bar for every chat client. If
your agent needs a richer entry payload and the publisher is not a generic chat UI (e.g. a custom domain front-end or
another agent delegating via `AgentInTheLoop`), subclass `StartEvent` directly and accept
`UserMessageEvent | YourStartEvent` on the relevant steps.

**Complete event selection guide** (from the report):

| If your event represents...     | Inherit from                                                  |
| ------------------------------- | ------------------------------------------------------------- |
| Workflow start condition        | `StartEvent`                                                  |
| User message from a **chat UI** | `UserMessageEvent`                                            |
| Workflow termination            | `StopEvent`                                                   |
| Error/failure                   | `ExceptionEvent`                                              |
| LLM invocation result           | `LLMEvent`                                                    |
| LLM terminal response           | `LLMStopEvent`                                                |
| Document retrieval              | `RetrieverEvent`                                              |
| Reranking operation             | `RerankerEvent`                                               |
| Embedding generation            | `EmbeddingEvent`                                              |
| Tool/function call              | `ToolEvent`                                                   |
| Guardrail check                 | `GuardEvent`                                                  |
| Chain execution                 | `ChainEvent`                                                  |
| Human approval needed           | `HumanInTheLoopRequestEvent`                                  |
| Agent delegation                | `AgentInTheLoopRequestEvent`                                  |
| Memory retrieval                | `RetrieveUserMemoryEvent` / `RetrieveOrganizationMemoryEvent` |
| Memory storage                  | `StoreUserMemoryEvent` / `StoreOrganizationMemoryEvent`       |
| Streaming text chunk            | `ChunkEvent`                                                  |
| Agent thought/reasoning         | `ThoughtEvent`                                                |
| Cost information                | `LLMCostEvent`                                                |
| Generic workflow state          | `ControlAndDisplayEvent`                                      |
| Generic UI update               | `DisplayEvent`                                                |
| Meta-question about the agent   | `MetaQuestionDetectedEvent` / `NotAMetaQuestionEvent`         |

**Rule of thumb**: If a step consumes it → `ControlEvent`. If only the UI needs it → `DisplayEvent`. If both →
`ControlAndDisplayEvent`. Most custom agent events are `ControlEvent`.

**Chat-UI agents do not wire self-awareness, titles or follow-ups by hand.** The meta-question gate ("What can you
do?"), the thread title and the follow-up questions belong to the `Conversation` capability (`contextualize` runs the
gate and titles the thread, `complete` generates follow-ups and ends the run). See "Step 4b".

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

Create one file per event in `agents/{agent_name}/events/`:

```python
# packages/agent/swiss_ai_hub/agent/agents/{agent_name}/events/{event_name}.py
from swiss_ai_hub.core.events.agent import ControlEvent


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
# packages/agent/swiss_ai_hub/agent/agents/{agent_name}/{agent_name}.py
from typing import ClassVar

from swiss_ai_hub.core.events.agent import StopEvent, UserMessageEvent

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.{agent_name}.events.{event_name} import {EventName}
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class {AgentName}(Agent):
    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.{agent_name}.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.{agent_name}.metadata.description"
    )
    icon: ClassVar[str] = "mage:robot"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.start.name"),
        description=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.start.description"),
        icon="mage:play",
    )
    async def start_step(self, event: UserMessageEvent) -> {EventName}:
        return {EventName}(field_name=event.user_query)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.{agent_name}.steps.end.name"),
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

Source: `packages/agent/swiss_ai_hub/agent/workflow/decorators/step.py`

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

Source: `AgentDispatcher._get_parameter_value()` in `packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`

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

## Step 4b: Chat Blueprints Use Capabilities

A conversational agent (chat UI, bots) is assembled from **capabilities**
(`packages/agent/swiss_ai_hub/agent/capabilities/`), not from hand-written retrieval, memory, title or stop steps. A
step returns a capability's request event through its typed helper; a later step declares the result event as a
parameter. The reference is `agents/llm_wrapping_agent/llm_wrapping_agent.py`; the full contract is in
`packages/agent/CLAUDE.md` ("Capabilities").

| Capability      | Config mixin          | Request helper (returns)                                     | Result (declare as parameter) |
| --------------- | --------------------- | ------------------------------------------------------------ | ----------------------------- |
| `Conversation`  | `ConversationFields`  | `contextualize(history, message)` -> `ContextualizeRequest`  | `Conversation.Contextualized` |
|                 |                       | `compose(history, blocks)` -> `ComposeRequest`               | `Conversation.Composed`       |
|                 |                       | `complete(answer, stop=None)` -> `CompleteRequest` (last)    | ends the run                  |
| `Memory`        | `MemoryFields`        | `recall(query)` / `remember(...)` (returned before complete) | `Memory.Recalled`             |
| `AttachedFiles` | `AttachedFilesFields` | `read(files, history, query, reserve_tokens)`                | `AttachedFiles.Contents`      |
| `Knowledge`     | `KnowledgeFields`     | `search(references, query)` (`#` references)                 | `Knowledge.Searched`          |
| `ToolLoop`      | `ToolLoopFields`      | `<Agent>.tools.run(history)` (`tools = ToolLoop.over(...)`)  | `ToolLoop.Finished`           |

Typical spine of a chat blueprint (each line is one `@step`):

1. `limit_chat_history_step(UserMessageEvent) -> Conversation.ContextualizeRequest` (`Conversation.contextualize(...)`)
2. `gather_context_step(Conversation.Contextualized, UserMessageEvent) -> list[Memory.RecallRequest | AttachedFiles.ReadRequest | Knowledge.SearchRequest]`
   (fan-out by returning a list)
3. `assemble_prompt_step(Conversation.Contextualized, Memory.Recalled, AttachedFiles.Contents, Knowledge.Searched) -> Conversation.ComposeRequest`
4. `respond_step(Conversation.Composed, Conversation.Contextualized, ...) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]`:
   stream with `displayer.display_llm_stream(..., as_stop_step=False)`, then return `Memory.remember(...)` first and
   `Conversation.complete(answer=...)` last

Rules:

- The config class inherits the mixins of every capability it calls
  (`class MyConfig(MemoryFields, ConversationFields, AgentConfig)`) and spreads their `*_form_elements()` in `as_form()`
  (see `LLMWrappingAgentConfig`). The runner refuses to start otherwise.
- Annotate steps with the scoped names (`Conversation.Composed`, `Memory.Recalled`); requests carry a `Request` suffix.
- Do not write your own steps for the meta-question gate, query condensing, title, follow-ups, memory storage or the
  terminal stop event.
- A model that picks its own tools (Universal Agent pattern): declare
  `tools = ToolLoop.over(Knowledge, AttachedFiles, Memory, MyToolSpec)` on the class and call
  `MyAgent.tools.run(history)`; capabilities are offered as tools and `BaseToolSpec` classes (LlamaIndex) add custom
  ones. Example: `playground/minimal_workflow/tool_loop_workflow/`.
- All validation is in `Agent.validate_workflow` (run by `AgentRunner`);
  `capabilities/tests/test_capability_composition.py` shows what it rejects.
- Protocol events of capabilities and the tool loop are `ControlAndDisplayEvent`s with their own frontend component (see
  `/scaffold-event-display`).

______________________________________________________________________

## Step 5: Create Config

```python
# packages/agent/swiss_ai_hub/agent/agents/{agent_name}/configs/{agent_name}_config.py
from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber, InputText, ModelSelect
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.i18n import LocaleString


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
  `swiss_ai_hub.core.form.constraints` — NOT Pydantic's `ge=`, `le=`
- **Configurable fields**: Set to a FormkitElement in `as_form()` → editable in Admin UI
- **Non-configurable fields**: Set to a primitive in `as_form()` → deployment-fixed, baked in
- **Labels**: All labels must be `LocaleString` with de, en, fr, it

### StepConfig

For step-specific configuration, nest a `StepConfig` subclass:

```python
from swiss_ai_hub.core.agents import StepConfig

class MyStepConfig(StepConfig):
    threshold: Annotated[float | InputNumber, Field(description="Threshold")] = 0.5

class {AgentName}Config(AgentConfig):
    my_step_settings: MyStepConfig = MyStepConfig()
```

The dispatcher auto-extracts `StepConfig` fields and injects them into steps that declare the matching type.

### FormKit Elements Reference

From `packages/core/swiss_ai_hub/core/form/elements/`:

- **Input**: `InputText`, `InputNumber`, `Textarea`, `Password`, `InputMask`, `InputOtp`
- **Selection**: `Select`, `MultiSelect`, `CascadeSelect`, `Checkbox`, `ToggleSwitch`, `ToggleButton`, `RadioButton`,
  `SelectButton`, `Listbox`
- **Specialized**: `ModelSelect` (LLM picker), `AgentSelector`, `KnowledgeDatabaseSelector`, `VectorStoreInput`,
  `IconSelector`, `LocaleInput` (multi-language), `ColorPicker`, `DatePicker`, `Knob`, `Rating`, `Slider`
- **Layout**: `Group` (auto-created from nested `Form`), `Repeater` (auto-created from `list[Form]`)

For a chat blueprint, add the capability mixins (`ConversationFields`, `MemoryFields`, ...) as bases and spread their
`*_form_elements()` into `as_form()` — see `LLMWrappingAgentConfig`.

Source: `packages/core/swiss_ai_hub/core/agents/agent_config.py`, `packages/core/swiss_ai_hub/core/form/form.py`

______________________________________________________________________

## Step 6: Create Entry Point

```python
# packages/agent/app/{agent_name}/main.py
# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.{agent_name} import {AgentName}, {AgentName}Config
from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(agent_type={AgentName}, agent_config={AgentName}Config.as_form())
    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
```

Model on `packages/agent/app/llm_wrapping_agent/main.py` (it also passes `templates=` for agent profile templates,
optional).

Source: `packages/agent/swiss_ai_hub/agent/runners/agent_runner.py`

______________________________________________________________________

## Step 7: Add i18n

Create translation files in `packages/agent/swiss_ai_hub/agent/i18n/translations/agent/`. The file name is the path
segment after `agent.`, so no locale root key is needed:

```yaml
# {agent_name}.en.yml
metadata:
  name: "{Agent Display Name}"
  description: "{Agent description for Admin UI}"
steps:
  start:
    name: "Start"
    description: "Receives user message and begins processing"
  end:
    name: "Finish"
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

Source: `packages/agent/swiss_ai_hub/agent/i18n/agent_locale_string.py`,
`packages/agent/swiss_ai_hub/agent/i18n/translations/agent/`

______________________________________________________________________

## Step 8: LLM Integration

Use `EventDisplayer` for streaming LLM output to the frontend. `AgentConfig` carries the `LLMConfig` (`config.llm`);
`cost_reporting_llm` yields an LLM that reports its costs as `LLMCostEvent`s:

```python
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent

@step()
async def llm_step(
    self,
    event: MyEvent,
    config: MyAgentConfig,
    displayer: EventDisplayer,
    user: UserIdentity | None = None,
) -> LLMEvent:
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content=config.system_prompt),
        ChatMessage(role=MessageRole.USER, content=event.message),
    ]
    async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
        return await displayer.display_llm_stream(config.llm, llm, messages, as_stop_step=False)
```

**Key**: `display_llm_stream()` handles token-by-token streaming, `<think>` tag parsing, and `ChunkEvent` emission
automatically. With `as_stop_step=True` it returns an `LLMStopEvent` that ends the run; a chat blueprint passes `False`
and hands the answer to `Conversation.complete(...)`. Pass `tools=` only inside the tool loop.

### Display Methods

| Method                            | Purpose                                  |
| --------------------------------- | ---------------------------------------- |
| `display_thought(text)`           | Show internal reasoning                  |
| `display_chunk(text, model_name)` | Stream output incrementally              |
| `display_llm_stream(...)`         | Complete LLM response with cost tracking |

Source: `packages/core/swiss_ai_hub/core/displayers/event_displayer.py`,
`packages/core/swiss_ai_hub/core/displayers/stream/stream_processor.py`

______________________________________________________________________

## Step 9: Memory Integration

**Chat blueprints**: use the `Memory` capability (see "Step 4b"): `Memory.recall(ctx.query)` ahead of the prompt,
`Memory.remember(...)` returned before `Conversation.complete(...)` so the storage request is published before the run
tears down. The config needs `MemoryFields`; the profile decides which scopes are read and written.

**Non-chat agents** that talk to memory directly inject `AgentMemory` (built from the profile's own extraction model)
and call `search_user_memory` / `search_organization_memory` / `add_user_memory`:

```python
from swiss_ai_hub.core.generative_ai import AgentMemory

@step()
async def retrieve_memory(self, event: UserMessageEvent, memory: AgentMemory) -> MemoryEvent:
    user_memories = await memory.search_user_memory(query=event.user_query, user_id=event.user.id)
    return MemoryEvent(user_memories=user_memories)
```

**Termination constraint**: `StopEvent` must come AFTER memory storage — the store step produces an intermediate event
and the stop step consumes it.

**Playground**: `playground/minimal_workflow/user_memory_workflow/`,
`playground/minimal_workflow/organization_memory_workflow/`

Source: `packages/core/swiss_ai_hub/core/generative_ai/memory/agent_memory.py`

______________________________________________________________________

## Step 10: Create Tests

Runner-backed tests need the Docker dev stack (NATS, API for config RPC). Stop any locally running agent of the same
class first — it shares the test runner's NATS queue group and eats its events.

### BDD Feature File

```gherkin
# packages/agent/swiss_ai_hub/agent/agents/{agent_name}/tests/features/{agent_name}.feature
Feature: {Agent Display Name}

  Scenario: Happy path
    Given a {AgentName} runner
    When the start event is sent with payload "test message"
    Then a StartEvent is present with payload "test message"
    And a StopEvent is present
```

### Test Implementation

Model on `packages/agent/playground/minimal_workflow/simple_workflow/tests/test_simple_agent.py`:

```python
# packages/agent/swiss_ai_hub/agent/agents/{agent_name}/tests/test_{agent_name}.py
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.{agent_name} import {AgentName}, {AgentName}Config
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/{agent_name}.feature")


@given("a {AgentName} runner", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type={AgentName},
        agent_config={AgentName}Config(agent_id="{agent_name}", name=LocaleString(en="{Agent Display Name}"),
                                       description=LocaleString(en="Test")),
    )


@when(parsers.parse('the start event is sent with payload "{payload}"'))
@async_test
async def _(agent_runner: AgentTestRunner, payload: str):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=payload, role=MessageRole.USER)], user=fake_user()
            ),
            topic=topic,
        )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not receive stop event"
```

A blueprint that uses memory or other agents needs `await agent_runner.ensure_dependent_agent_stream(...)` inside the
`test_run()` block (see `rag_agent/tests/test_rag_agent.py`).

### Key Test Assertions

| Method                                                 | Purpose                              |
| ------------------------------------------------------ | ------------------------------------ |
| `runner.has_start_event`                               | Check if StartEvent was received     |
| `runner.has_stop_event`                                | Check if StopEvent was received      |
| `runner.has_exception_event`                           | Check if ExceptionEvent was received |
| `runner.get_events_of_class(cls)`                      | Get all events of a specific type    |
| `runner.get_event_of_class(cls)`                       | First event of that type (raises)    |
| `runner.wait_for_event(cls, timeout)`                  | Wait for a specific event (async)    |
| `runner.send_event_from_topic(start_event=e, topic=t)` | Send an event to the agent           |

For AITL tests, use `runner.ensure_dependent_agent_stream(agent_class)`.

### Unit Testing (Direct Step Invocation)

Individual steps can be tested by calling them directly, bypassing the dispatcher (see
`llm_wrapping_agent/tests/test_llm_wrapping_input_too_large_guard.py`):

```python
result = await MyAgent().retrieve_step(event=event, memory=memory)
```

Helper classes the steps import are tested on their own. Capability composition (a blueprint that stalls or crashes) is
pinned by `capabilities/tests/test_capability_composition.py`.

Source: `packages/agent/swiss_ai_hub/agent/runners/agent_test_runner.py`

______________________________________________________________________

## Step 11: Register & Verify

Agent discovery is automatic — `AgentRunner` responds to `AgentClassDiscoveryRequestEvent` with the agent's metadata,
form schema, event specs, and workflow graph. No manual registration needed.

**Verify the agent is discoverable:**

```bash
cd packages/agent && uv run python -c "from swiss_ai_hub.agent.agents.{agent_name} import {AgentName}; print({AgentName}.get_steps())"
```

______________________________________________________________________

## Implementation Checklist

### Before Coding

- [ ] Read `packages/agent/CLAUDE.md`
- [ ] Identified the pattern from the catalog above
- [ ] Studied the matching playground example
- [ ] Sketched the event DAG on paper (events as edges, steps as nodes)

### During Coding

- [ ] Agent class extends `Agent` with `name`, `description`, `icon` as `ClassVar[AgentLocaleString]`
- [ ] All `@step` methods are `async`, use type annotations, return events
- [ ] No instance state on `self` and no helper methods on the class — state in `RunContext` / `ThreadContext`, helpers
  in imported classes
- [ ] Events inherit from the correct base class (see table above)
- [ ] One class per file, file name matches class name
- [ ] Config uses form duality pattern with `as_form()` classmethod
- [ ] Form constraints use `Ge()`, `Le()` etc. — not Pydantic's `ge=`, `le=`
- [ ] i18n translations in all 4 locales (de, en, fr, it)
- [ ] Entry point in `app/{agent_name}/main.py`; chat agent: config carries the capability mixins

### After Coding

- [ ] Every event produced by a step is consumed by another step (no dead ends)
- [ ] Every execution path reaches `StopEvent`
- [ ] `StopEvent` is returned alone (not in a list with other events)
- [ ] Optional params have synchronization (precondition or max_executions_per_run)
- [ ] BDD tests pass: `cd packages/agent && uv run pytest swiss_ai_hub/agent/agents/{agent_name} -v`
- [ ] Agent is importable: `uv run python -c "from swiss_ai_hub.agent.agents.{agent_name} import {AgentName}"`

______________________________________________________________________

## File Reference

### Framework Files

| File                                                                                | Purpose                               |
| ----------------------------------------------------------------------------------- | ------------------------------------- |
| `packages/agent/swiss_ai_hub/agent/agents/agent.py`                                 | Agent base class                      |
| `packages/agent/swiss_ai_hub/agent/workflow/decorators/step.py`                     | `@step()` decorator                   |
| `packages/agent/swiss_ai_hub/agent/workflow/decorators/precondition.py`             | `@precondition()` decorator           |
| `packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`                 | Core workflow executor (DI, dispatch) |
| `packages/agent/swiss_ai_hub/agent/runners/agent_runner.py`                         | Production runner                     |
| `packages/agent/swiss_ai_hub/agent/runners/agent_test_runner.py`                    | Test runner                           |
| `packages/agent/swiss_ai_hub/agent/context/run/run_context.py`                      | Per-run ephemeral state               |
| `packages/agent/swiss_ai_hub/agent/context/thread/thread_context.py`                | Per-thread persistent state           |
| `packages/agent/swiss_ai_hub/agent/i18n/agent_locale_string.py`                     | Agent i18n strings                    |
| `packages/core/swiss_ai_hub/core/agents/agent_config.py`                            | Config base with form duality         |
| `packages/core/swiss_ai_hub/core/form/form.py`                                      | Form system                           |
| `packages/core/swiss_ai_hub/core/form/elements/`                                    | FormKit elements (28 types)           |
| `packages/core/swiss_ai_hub/core/form/constraints.py`                               | Form-aware validators                 |
| `packages/core/swiss_ai_hub/core/displayers/event_displayer.py`                     | LLM streaming + display events        |
| `packages/core/swiss_ai_hub/core/generative_ai/memory/agent_memory.py`              | User + org memory                     |
| `packages/core/swiss_ai_hub/core/workflow/annotations/custom_types/list_of_size.py` | FixedList for fan-in                  |

### Playground Patterns Index

| Directory                               | Pattern                | Key Concept                             |
| --------------------------------------- | ---------------------- | --------------------------------------- |
| `simple_workflow/`                      | Linear pipeline        | Basic step chaining                     |
| `tool_loop_workflow/`                   | Tool loop              | `ToolLoop.over`, tool specs, approvals  |
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
make pr-ready    # Format + lint (also run by the stop hook)
make test        # Run pytest in the scope (from packages/agent or the root)
```

______________________________________________________________________

## Cross-References

- **Debugging agents**: `/debug-agent` — execution semantics, race conditions, MCP-powered diagnostics
- **Event infrastructure**: `/nats-events` — event hierarchy, subject format, dispatcher architecture
- **Event display components**: `/scaffold-event-display` — frontend visualization for new event types
- **Bot integration**: `/bot-framework` — CompletionHandler, channel setup for BITL patterns
- **Process orchestration**: see `packages/process/CLAUDE.md` — multi-entity workflows (agents + humans + programs)
