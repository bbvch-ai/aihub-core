---
name: debug-agent
description: >-
  Debug an AI agent using code analysis and MCP-powered runtime inspection (NATS streams,
  MongoDB events, Langfuse traces). Covers execution semantics, race conditions, engineering
  constraint violations, and a symptom-driven diagnostic cookbook. Use when user says 'my agent
  is broken', 'agent not responding', 'debug the agent', 'agent stuck', 'step executes twice',
  'step never runs', 'events after stop', 'agent produces wrong output', or 'agent throws error'.
  Do NOT use for creating new agents (use /scaffold-agent), event infrastructure reference
  (use /nats-events), or pipeline debugging (use /debug-pipeline).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, mcp__nats__stream_list, mcp__nats__stream_info, mcp__nats__stream_subjects, mcp__nats__stream_view, mcp__nats__stream_get, mcp__nats__stream_state, mcp__nats__stream_report, mcp__nats__server_info, mcp__nats__kv_ls, mcp__nats__kv_get, mcp__mongodb__find, mcp__mongodb__aggregate, mcp__mongodb__count, mcp__mongodb__collection-schema, mcp__mongodb__list-collections, mcp__langfuse__getPrompt, mcp__langfuse__listPrompts
---

# Agent Debugging Guide

Debug an AI agent. Agent name or issue description via `$ARGUMENTS`.

## Before You Start

Read the agent scope guide: `packages/agent/CLAUDE.md`

## Debugging Mental Model

Agents are **Dispatchable Workflows** — directed acyclic graphs where nodes are `@step` methods and edges are typed
Events. The dispatcher (not the developer) decides execution order based on data availability.

**Key properties that cause bugs:**

- **No shared state**: Each step gets a fresh `agent()` instance. Instance variables are always empty.
- **Distributed execution**: Consecutive steps on the same run may execute on different servers.
- **Data-driven execution**: Steps declare data requirements, not execution order. Order is emergent.
- **Minimum Viable Input**: A step fires the moment its required inputs are satisfied (Rule R1).
- **Re-execution on new data**: A new event matching an already-consumed parameter triggers re-execution (Rule R2).
- **Parallel step execution**: Multiple steps for the same run may execute in parallel if their dependencies are
  independently satisfied.

**The Dispatcher's Role** (AgentDispatcher):

1. **Ingestion:** Subscribes to the agent's NATS JetStream subject
2. **Evaluation:** Upon receiving event *e*, identifies all steps *S* where *e* ∈ *input_types(S)*
3. **Trigger:** Invokes step *S* if and only if all required inputs are present in the `EventStore`

Source: `packages/core/swiss_ai_hub/core/dispatcher/base_dispatcher.py`,
`packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`

______________________________________________________________________

## Step 1: Locate & Map the Agent

1. Search `packages/agent/swiss_ai_hub/agent/agents/` and `packages/agent/playground/` for the agent class
2. Extract all `@step` methods with their signatures:

```python
# For each @step method, note:
# - Input params: event types, optional params (| None), list params, FixedList params
# - Output type: return type annotation (single event, list, or None)
# - Decorator args: precondition, max_executions_per_run, stop_on_error
```

3. Map the event DAG: `StartEvent → step_1() → EventA → step_2() → ... → StopEvent`
4. Find the `AgentConfig` subclass and its `as_form()` method
5. Find the entry point in `packages/agent/app/*/main.py`

**Output**: Complete step/event chain with parameter types and decorator options.

______________________________________________________________________

## Step 2: Classify Symptom

Use this triage table to jump to the right diagnostic section:

| Symptom                          | Go To                                             |
| -------------------------------- | ------------------------------------------------- |
| Step executes multiple times     | [Issue 1: Step Executes Multiple Times](#issue-1) |
| Step never executes              | [Issue 2: Step Never Executes](#issue-2)          |
| Events emitted after stop        | [Issue 3: Events After Stop](#issue-3)            |
| Precondition params don't match  | [Issue 4: Precondition Mismatch](#issue-4)        |
| Agent won't start at all         | [Issue 5: Agent Won't Start](#issue-5)            |
| Config validation errors         | [Issue 6: Configuration Errors](#issue-6)         |
| Agent stores state on self       | [Constraint: Context Smuggle](#context-smuggle)   |
| Step returns after StopEvent     | [Constraint: Dangling Stop](#dangling-stop)       |
| Config doesn't match form        | [Constraint: Config Lie](#config-lie)             |
| Step called by multiple triggers | [Constraint: Double-Dip](#double-dip)             |
| Optional param causes re-run     | [Constraint: Optional Param Trap](#optional-trap) |

______________________________________________________________________

## Execution Semantics Deep Dive

Understanding these rules is essential for diagnosing most agent bugs.

### The Six Execution Rules

| Rule | Name                     | What It Means                                                                                       |
| ---- | ------------------------ | --------------------------------------------------------------------------------------------------- |
| R1   | Minimum Viable Input     | Step fires when ALL required params have at least one matching event                                |
| R2   | Re-execution on New Data | New event matching an already-consumed param → step re-executes with updated data                   |
| R3   | List Parameter Semantics | `list[EventType]` collects ALL available events at trigger time (doesn't wait for a specific count) |
| R4   | StopEvent Constraint     | `StopEvent` must be the LAST event emitted — nothing may follow                                     |
| R5   | Precondition Override    | `@precondition` re-evaluates on each new event arrival AFTER R1 — deadlock if never satisfied       |
| R6   | Event Persistence        | Every `ControlEvent` persisted in JetStream, replayed on dispatcher restart                         |

Source: `packages/core/swiss_ai_hub/core/dispatcher/base_dispatcher.py`
(`BaseDispatcher._step_meets_basic_execution_requirements()`)

### Parameter Types and Their Execution Behavior

| Declaration                    | Required? | Waits For              | Re-executes on New? | Source                                  |
| ------------------------------ | --------- | ---------------------- | ------------------- | --------------------------------------- |
| `event: MyEvent`               | Yes       | 1 event of type        | Yes (R2)            | Latest event or trigger event preferred |
| `event: MyEvent \| None`       | No        | Nothing (optional)     | Yes (R2)            | Latest event or `None`                  |
| `events: list[MyEvent]`        | No\*      | Nothing (collects all) | Yes (R2)            | All events of type at trigger time      |
| `events: FixedList(MyEvent,N)` | Yes       | Exactly N events       | No (fires once)     | `ListOfSize` with size enforcement      |

\*`list[T]` is treated as optional — an empty list doesn't block execution.

Source: `packages/core/swiss_ai_hub/core/dispatcher/base_dispatcher.py` (`BaseDispatcher._get_event_value()`)

### Race Condition Problem

**The classic bug**: A step with `(required: A, optional: B | None)`.

```
Timeline:
  t=0: A arrives → step fires with (A, None)     ← R1: minimum viable input
  t=1: B arrives → step fires AGAIN with (A, B)  ← R2: re-execution on new data
```

**The developer expected**: One execution with both A and B. **What happened**: Two executions — one without B, one with
B.

**Synchronization solutions:**

| Technique                              | When to Use                   | Code Pattern                                           |
| -------------------------------------- | ----------------------------- | ------------------------------------------------------ |
| `@precondition` function               | Dynamic count / complex logic | `@step(precondition=check_fn)` where `check_fn → bool` |
| `FixedList(EventType, N)`              | Known count at compile time   | `events: FixedList(MyEvent, 3)` — waits for exactly 3  |
| Make param required (remove `\| None`) | Always needed                 | `event: B` instead of `event: B \| None`               |
| `max_executions_per_run=1`             | Run once regardless           | `@step(max_executions_per_run=1)` — idempotency guard  |

Source: `packages/agent/swiss_ai_hub/agent/workflow/decorators/precondition.py`,
`packages/core/swiss_ai_hub/core/workflow/annotations/custom_types/list_of_size.py`

### List Parameter Behavior

When a step parameter is typed as `list[EventType]`, the step executes on each new event arrival:

| Event Arrival | List Contents                              | Step Executes |
| ------------- | ------------------------------------------ | ------------- |
| ResultEvent₁  | [ResultEvent₁]                             | Yes           |
| ResultEvent₂  | [ResultEvent₁, ResultEvent₂]               | Yes           |
| ResultEvent₃  | [ResultEvent₁, ResultEvent₂, ResultEvent₃] | Yes           |

The step executes 3 times. This follows from the Minimum Viable Input Rule: a list of length 1 satisfies `list[T]`.

**Ordering Guarantee:** Events in the list are ordered by arrival time.

**Mitigation strategies:**

1. **Precondition with expected count:**
   `@step(precondition=lambda results, config: len(results) >= config.expected_count)`
2. **FixedList for compile-time known count:** `results: FixedList(ResultEvent, N)` — executes once when exactly N
   events available

### Event Resolution Strategy

When binding events to step parameters:

1. **Fixed Collection:** `FixedList(Event, N)` blocks until exactly *N* events available, then returns all *N*
2. **Unbounded List:** `list[Event]` returns all events of that type currently available; step re-executes on each new
   arrival
3. **Single Instance:**
   - If the triggering event matches the parameter type, that instance is used
   - Otherwise, the most recently created event of that type is used

### Idempotency Check

The dispatcher tracks which events were used as input for each step execution. If a step is triggered again with the
exact same set of input events (by event ID), the execution is silently skipped.

Source: `StepStore.was_called_with_events()` in `packages/core/swiss_ai_hub/core/dispatcher/stores/step/step_store.py`

______________________________________________________________________

## Diagnostic Cookbook

### Issue 1: Step Executes Multiple Times {#issue-1}

**Symptom**: A step runs more than expected (duplicated output, repeated LLM calls, duplicate costs).

**Static analysis:**

1. Check parameter declarations — any `event: EventType | None` (optional) params?
2. Check if multiple event types arrive asynchronously that satisfy the same step
3. Check `max_executions_per_run` — is it set? If None, unlimited executions allowed
4. Check if a loop pattern exists where the step both consumes and produces an event that triggers itself

**Root causes:**

- **Optional parameter trap**: Optional param + required param → R1 fires on required, R2 fires again when optional
  arrives
- **Missing max_executions_per_run**: Unbounded re-execution on each new matching event
- **Multiple producers**: Two or more upstream steps produce events that match the same param → step fires for each

**Fix patterns:**

```python
# Problem: optional param causes double execution
@step()
async def my_step(self, required: A, optional: B | None) -> StopEvent:
    ...

# Fix 1: Use precondition to wait for both
def wait_for_both(required: A, optional: B | None) -> bool:
    return optional is not None

@step(precondition=wait_for_both)
async def my_step(self, required: A, optional: B | None) -> StopEvent:
    ...

# Fix 2: Make it required if it always arrives
@step()
async def my_step(self, required: A, also_required: B) -> StopEvent:
    ...

# Fix 3: Limit to one execution
@step(max_executions_per_run=1)
async def my_step(self, required: A, optional: B | None) -> StopEvent:
    ...
```

#### MCP Diagnosis

1. **Check event stream**: Use `mcp__nats__stream_view` with stream `agent_{AgentClass}_stream`

   - Look for: Multiple events of the same type arriving at different times
   - Normal: One event per type per step invocation
   - Abnormal: Multiple events matching the same step parameter arriving in rapid succession

2. **Query persisted events**: Use `mcp__mongodb__find` on `persisted_agent_events` collection:

   ```json
   {"filter": {"run_id": "<run_id>", "event.event_name": "<StepOutputEvent>"}}
   ```

   - Look for: Multiple documents with same `event_name` from the same step
   - Count duplicates to confirm re-execution count

______________________________________________________________________

### Issue 2: Step Never Executes {#issue-2}

**Symptom**: A step is defined but its output events never appear. The workflow stalls.

**Static analysis:**

1. Check all required params — does the step expect an event that no other step produces?
2. Check `FixedList` sizes — does it expect N events but only N-1 are produced?
3. Check precondition — does it return `False` indefinitely?
4. Check `max_executions_per_run` — has the limit already been reached?
5. Check `stop_on_error=True` (default) — did a previous step crash the run?

**Root causes:**

- **Missing upstream event**: The event type listed in the step's params is never published by any step
- **FixedList count mismatch**: `FixedList(MyEvent, 5)` but only 3 events are produced (fan-out didn't complete)
- **Precondition always false**: The precondition function never sees the state it expects
- **Run crashed**: A prior step threw an exception with `stop_on_error=True`, marking the execution context as crashed

**Fix patterns:**

```python
# Problem: FixedList expects 5 but only 3 fan-out steps exist
events: FixedList(ResultEvent, 5)  # ← Wrong count

# Fix: Match the actual fan-out count
events: FixedList(ResultEvent, 3)  # ← Matches actual producers

# Problem: Precondition checks RunContext that was never set
def my_precondition(ctx: RunContext) -> bool:
    data = await ctx.get("my_key")  # ← Never set by any step
    return data is not None

# Fix: Ensure upstream step sets the context
@step()
async def upstream(self, event: A, ctx: RunContext) -> B:
    await ctx.set("my_key", "value")  # ← Set it here
    return B()
```

#### MCP Diagnosis

1. **Check stream subjects**: Use `mcp__nats__stream_subjects` with stream `agent_{AgentClass}_stream`

   - Look for: Missing event subjects that the stalled step expects
   - Compare expected input event names against actual published subjects

2. **Query upstream events**: Use `mcp__mongodb__find` on `persisted_agent_events`:

   ```json
   {"filter": {"run_id": "<run_id>"}, "sort": {"event.sequence_number": 1}}
   ```

   - Look for: The last event in the sequence — which step produced it? What should come next?
   - Check if an `ExceptionEvent` terminated the run early

3. **Check if run is crashed**: Use `mcp__nats__kv_ls` to list KV buckets, then `mcp__nats__kv_get` for the step store

   - Look for: `crashed=true` entry indicating the execution context was marked crashed

______________________________________________________________________

### Issue 3: Events After Stop {#issue-3}

**Symptom**: Events appear in the stream after a `StopEvent` was published. May cause UI glitches, orphaned data, or
state corruption.

**Rule R4 violated**: `StopEvent` MUST be the last event. The dispatcher cleans up `RunContext`, `EventStore`, and
`StepStore` on receiving `StopEvent` or `ExceptionEvent`.

**Static analysis:**

1. Find all steps that return `StopEvent` — does any also return other events in a list?
2. Check for fire-and-forget patterns: `asyncio.create_task()` that publishes events after stop
3. Check for `DisplayEvent` publishing after stop (allowed but unusual)

**Root causes:**

- **List return with StopEvent**: `return [DisplayEvent(...), StopEvent()]` — display event may arrive after stop
  depending on publish ordering
- **Async leak**: A background task continues publishing after the run terminates
- **Parallel step timing**: Two steps race — one publishes StopEvent, the other publishes a result after

**Fix**: Ensure the step returning `StopEvent` returns it alone, or that all other events are published before it.

#### MCP Diagnosis

1. **Check event ordering**: Use `mcp__nats__stream_view` with stream `agent_{AgentClass}_stream`
   - Look for: Events with sequence numbers AFTER the StopEvent sequence number
   - Normal: StopEvent has the highest sequence number
   - Abnormal: Any event after StopEvent in the stream

______________________________________________________________________

### Issue 4: Precondition Parameter Mismatch {#issue-4}

**Symptom**: Precondition function receives wrong types or missing parameters. May silently return False (step never
fires) or throw TypeError.

**Static analysis:**

1. Compare the precondition function's parameter annotations with what the dispatcher can inject
2. The precondition function uses the SAME DI system as `@step` methods — all injectable types are available
3. Check that event type params in the precondition match event types from the step itself

**Root causes:**

- **Wrong parameter type**: Precondition declares `config: MyConfig` but the agent uses `OtherConfig`
- **Missing event type**: Precondition expects `event: B` but event B isn't in the step's input events
- **Non-injectable type**: Precondition declares a parameter that isn't in the DI table

**DI-injectable types** (available in both `@step` methods and precondition functions):

| Type Annotation                        | What Gets Injected                    |
| -------------------------------------- | ------------------------------------- |
| Event subclass (e.g., `MyEvent`)       | Matched from event history by type    |
| `AgentConfig` subclass                 | Merged runtime config for this run    |
| `StepConfig` subclass                  | Step-specific config from AgentConfig |
| `RunContext`                           | Per-run ephemeral state (Redis)       |
| `ThreadContext`                        | Per-thread persistent state (Redis)   |
| `EventDisplayer`                       | Emit display events for frontend      |
| `LocaleHandler` / `AgentLocaleHandler` | i18n handler in the run's locale      |
| `AgentMemory`                          | User and organization memory access   |
| `AgentInstanceTopic`                   | NATS topic info for this event        |

Source: `AgentDispatcher._get_parameter_value()` in `packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`

______________________________________________________________________

### Issue 5: Agent Won't Start {#issue-5}

**Symptom**: Agent doesn't respond to any events. No logs. No errors. Nothing happens.

**Static analysis:**

1. Check `app/{agent_name}/main.py` — does it instantiate `AgentRunner` with the correct class and config?
2. Check that `AgentConfig.as_form()` doesn't throw (misconfigured form elements)
3. Check that the agent class has at least one `@step` that accepts a `StartEvent` subclass
4. Check NATS connectivity settings in environment variables

**Common causes:**

- **No start step**: No `@step` method accepts `UserMessageEvent` or custom `StartEvent` subclass
- **Config `as_form()` error**: A FormKit element is misconfigured (wrong type, missing label)
- **NATS not running**: Docker dev stack not started or NATS container unhealthy
- **Stream not created**: The agent's JetStream stream doesn't exist yet

#### MCP Diagnosis

1. **Check NATS server**: Use `mcp__nats__server_info`

   - Look for: Server running, connections active
   - If this fails: Docker dev stack isn't running (`docker compose -f infra/docker-compose.dev.yml up -d`)

2. **Check streams exist**: Use `mcp__nats__stream_list`

   - Look for: `agent_{AgentClass}_stream` in the stream list
   - If missing: Agent hasn't connected yet — check runner logs

3. **Check stream health**: Use `mcp__nats__stream_info` with stream `agent_{AgentClass}_stream`

   - Look for: Consumer count, message count, last sequence
   - Zero consumers = no dispatcher is subscribed

______________________________________________________________________

### Issue 6: Configuration Errors {#issue-6}

**Symptom**: Agent starts but throws validation errors, wrong model names, or unexpected config values.

**Static analysis:**

1. Check `AgentConfig` subclass — do field types match their `as_form()` FormKit elements?
2. Check `Field(description=...)` annotations and form constraints (`Ge()`, `Le()`, `MinLen()`, etc.)
3. Check `get_non_configurable_values()` — are deployment-specific values correct?
4. Check that `to_configurable_submission_model()` generates the expected JSON schema

**Root causes:**

- **Form/data type mismatch**: Field declared as `int | InputNumber` but `as_form()` provides `InputText`
- **Missing non-configurable value**: A field expected at runtime wasn't set in `as_form()`
- **Deep merge order wrong**: Non-configurable values overwritten by submitted config (should be the reverse)
- **FormKit constraint issue**: Using Pydantic's `ge=` instead of `Ge()` form constraint — breaks form mode validation

#### MCP Diagnosis

1. **Query agent config**: Use `mcp__mongodb__find` on `agent_configs` collection:

   ```json
   {"filter": {"agent_class": "<AgentClass>", "agent_id": "<agent_id>"}}
   ```

   - Look for: Config values stored in MongoDB — compare against what the agent expects

2. **Query agent class discovery**: Use `mcp__mongodb__find` on `agent_classes` collection:

   ```json
   {"filter": {"agent_class": "<AgentClass>"}}
   ```

   - Look for: `config_schema` field — does the JSON schema match the AgentConfig class?
   - Check `form` field — do FormKit elements render correctly?

______________________________________________________________________

## Engineering Constraint Violations

Five common violations that produce subtle, hard-to-diagnose bugs.

### Dangling Stop {#dangling-stop}

**Constraint**: A step that returns `StopEvent` must not also return other control events in the same list.

**Symptom**: Unpredictable behavior — some events processed, some lost. RunContext cleaned up mid-execution.

**Detection pattern:**

```python
# BAD: StopEvent in a list with other events
@step()
async def final_step(self, event: A) -> list[StopEvent | SomeOtherEvent]:
    return [SomeOtherEvent(data="..."), StopEvent()]  # ← Dangling stop!

# GOOD: Return StopEvent alone
@step()
async def final_step(self, event: A) -> StopEvent:
    return StopEvent()
```

**Why it breaks**: The dispatcher publishes events sequentially. When `StopEvent` arrives, it triggers cleanup
(`RunContext.delete_all()`, `EventStore.delete_all()`, `StepStore.delete_all()`). Any events published after may find
their state already cleaned up.

Source: `AgentDispatcher.handle_event()` lines 154-166

### Context Smuggle {#context-smuggle}

**Constraint**: Never store state on `self` (the agent instance). The dispatcher creates a fresh instance per step.

**Symptom**: State is always `None` or default. Works in tests (single process), fails in production (distributed).

**Detection pattern:**

```python
# BAD: Instance state
class MyAgent(Agent):
    def __init__(self):
        self.my_data = []  # ← Always empty in each step!

    @step()
    async def step_1(self, event: A) -> B:
        self.my_data.append(event.value)  # ← Lost after this step
        return B()

    @step()
    async def step_2(self, event: B) -> StopEvent:
        print(self.my_data)  # ← Always [] — fresh instance!
        return StopEvent()

# GOOD: Use RunContext
@step()
async def step_1(self, event: A, ctx: RunContext) -> B:
    await ctx.set("my_data", [event.value])
    return B()

@step()
async def step_2(self, event: B, ctx: RunContext) -> StopEvent:
    data = await ctx.get("my_data", [])  # ← Persisted in Redis
    return StopEvent()
```

**Why it breaks**: `AgentDispatcher.execute_step()` calls `agent_instance = self.agent()` — a fresh instance every time.

Source: `AgentDispatcher.execute_step()` line 287

### Config Lie {#config-lie}

**Constraint**: Do not check `AgentConfig` inside a step to determine if you should have waited for an event.

**Symptom**: Step executes prematurely, processes data before optional events arrive. Config-based `if` checks inside
step bodies that try to decide whether optional data "should" be present.

**Why it breaks**: By execution time, the dispatcher has already made the scheduling decision. The race condition has
occurred. Checking config inside the step is too late.

**Detection pattern:**

```python
# BAD: Checking config inside step body
@step()
async def process(self, required: A, optional: B | None = None, config: Config) -> Out:
    if config.enable_b and optional is None:
        return Out(partial=True)  # ← Too late! Step already fired without B
    ...

# GOOD: Use @precondition to prevent scheduling
@precondition()
async def check_ready(optional: B | None, config: Config) -> bool:
    if config.enable_b and optional is None:
        return False  # Delay execution until B arrives
    return True

@step(precondition=check_ready)
async def process(self, required: A, optional: B | None = None, config: Config) -> Out:
    # Guaranteed: if config.enable_b, optional is not None
    ...
```

#### Form/Config Type Mismatch

The `as_form()` method must produce FormKit elements for all configurable fields and primitive values for all
non-configurable fields. The types must match the field annotations.

```python
# BAD: as_form() returns wrong element type for field
class MyConfig(AgentConfig):
    temperature: Annotated[float | InputNumber, Field(description="Temperature")] = 0.7

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            **base.model_dump(),
            temperature=InputText(label=LocaleString(en="Temperature")),  # ← InputText, not InputNumber!
        )

# GOOD: Element type matches field annotation
    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            **base.model_dump(),
            temperature=InputNumber(label=LocaleString(en="Temperature"), min=0.0, max=2.0),
        )
```

### Double-Dip {#double-dip}

**Constraint**: Do not reuse the same event type for multiple distinct logical stages.

**Symptom**: Downstream steps trigger unpredictably or process the wrong event instance. A step meant for "stage 2"
fires during "stage 1" because both stages emit the same event type.

**Detection pattern:**

```python
# BAD: Same event type for two logical stages
@step()
async def stage_1(self, event: StartEvent) -> ResultEvent:
    return ResultEvent(data="stage 1 output")

@step()
async def stage_2(self, event: ResultEvent) -> ResultEvent:  # Reuses ResultEvent!
    return ResultEvent(data="stage 2 output")

@step()
async def final(self, event: ResultEvent) -> StopEvent:
    # Which ResultEvent? Stage 1 or Stage 2? Unpredictable.
    ...

# GOOD: Subclass Event for each distinct logical state
class Stage1Result(ControlEvent):
    data: str

class Stage2Result(ControlEvent):
    data: str

@step()
async def stage_1(self, event: StartEvent) -> Stage1Result:
    return Stage1Result(data="stage 1 output")

@step()
async def stage_2(self, event: Stage1Result) -> Stage2Result:
    return Stage2Result(data="stage 2 output")

@step()
async def final(self, event: Stage2Result) -> StopEvent:
    ...  # Unambiguous
```

#### Same Type in Multiple Parameters

A step should not accept the same event type through multiple parameters, as event resolution behavior becomes
ambiguous.

```python
# BAD: Same event type in two params
@step()
async def my_step(self, first: MyEvent, second: MyEvent) -> StopEvent:
    # first and second may both be the same event instance!
    ...

# GOOD: Use a list if you need multiple
@step()
async def my_step(self, events: list[MyEvent]) -> StopEvent:
    first, second = events[0], events[1]
    ...

# GOOD: Or use FixedList for deterministic count
@step()
async def my_step(self, events: FixedList(MyEvent, 2)) -> StopEvent:
    first, second = events[0], events[1]
    ...
```

### Optional Parameter Trap {#optional-trap}

**Constraint**: Optional parameters (`event: T | None`) don't block execution (R1) but DO trigger re-execution (R2).

**Symptom**: Step executes once with `None` for the optional param, then again when the optional event arrives.

**Detection**: Search for `| None` in step parameter annotations where only one execution was intended.

**Fix options:**

1. Add a `@precondition` that checks if the optional param has arrived
2. Use `max_executions_per_run=1` if only one execution is intended
3. Make the param required if it always arrives
4. Use `FixedList` if you need to wait for a specific count

See [Issue 1: Step Executes Multiple Times](#issue-1) for detailed fix patterns.

______________________________________________________________________

## Runtime Environment (Diagnostic View)

### Dependency Injection Table

When a step receives unexpected values, verify the DI resolution chain:

| Type Annotation                        | Resolved By                              | Where to Check                           |
| -------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| Event subclass                         | `BaseDispatcher._get_event_value()`      | Event store (JetStream) + trigger event  |
| `AgentConfig` subclass                 | `AgentDispatcher._get_parameter_value()` | `RunContext._agent_config` key           |
| `StepConfig` subclass                  | `agent_config.get_step_configs()`        | Nested config on AgentConfig             |
| `RunContext`                           | `RunContext.for_topic(redis, topic)`     | Redis keys: `run:{thread_id}:{run_id}:*` |
| `ThreadContext`                        | `ThreadContext.for_topic(redis, topic)`  | Redis keys: `thread:{thread_id}:*`       |
| `EventDisplayer`                       | Created with JSPublisher + TopicManager  | Check NATS Core subscriber on API side   |
| `LocaleHandler` / `AgentLocaleHandler` | `RunContext.get("locale")` → handler     | Check locale in RunContext               |
| `AgentMemory`                          | Created with config + locale handler     | Check mem0 settings + neo4j connectivity |
| Topic types                            | Passed through from dispatcher           | Check NATS subject format                |

### Context Anti-Patterns

**The Context Smuggle Violation**: Data must flow between steps via Events, not `RunContext`. Context-based data passing
creates invisible dependencies, breaks the DAG, and causes race conditions.

```python
# VIOLATION: Context as data bus
@step()
async def step_a(self, event: E, run_context: RunContext) -> EventA:
    await run_context.set("query", event.query)  # Wrong
    return EventA()

@step()
async def step_b(self, event: EventA, run_context: RunContext) -> Out:
    query = await run_context.get("query")  # Wrong
    ...

# CORRECT: Direct event dependency
@step()
async def step_b(self, event_a: EventA, original: E) -> Out:
    query = original.query  # Correct
    ...
```

**Exception:** `RunContext` is valid only for control flow state (loop counters, recursion depth).

| Anti-Pattern                   | Why It Fails                           | Correct Approach                     |
| ------------------------------ | -------------------------------------- | ------------------------------------ |
| `self.data = ...`              | Fresh instance per step execution      | Use `RunContext` or `ThreadContext`  |
| Global variable                | Multiple dispatchers share the process | Use `RunContext`                     |
| `RunContext` after `StopEvent` | Context deleted on stop                | Read before returning StopEvent      |
| `ThreadContext` for run-scoped | Persists across runs (30d TTL)         | Use `RunContext` for run-scoped data |
| Large objects in context       | Redis serialization overhead           | Store reference, not data            |

______________________________________________________________________

## MCP Tools Reference

### NATS MCP Tools

| Tool                         | Use For                                      | Key Parameters                           |
| ---------------------------- | -------------------------------------------- | ---------------------------------------- |
| `mcp__nats__stream_list`     | List all JetStream streams                   | —                                        |
| `mcp__nats__stream_info`     | Stream health: consumers, messages, state    | `stream_name`                            |
| `mcp__nats__stream_subjects` | What event types have been published         | `stream_name`                            |
| `mcp__nats__stream_view`     | Read actual events in order                  | `stream_name`, `count` (last N messages) |
| `mcp__nats__stream_get`      | Get specific message by sequence             | `stream_name`, `sequence`                |
| `mcp__nats__stream_state`    | Detailed stream state (first/last seq, etc.) | `stream_name`                            |
| `mcp__nats__stream_report`   | All streams summary                          | —                                        |
| `mcp__nats__server_info`     | NATS server health and config                | —                                        |
| `mcp__nats__kv_ls`           | List KV buckets (step stores, run contexts)  | —                                        |
| `mcp__nats__kv_get`          | Read specific KV entry                       | `bucket`, `key`                          |

**Stream naming convention**: `agent_{AgentClass}_stream` (e.g., `agent_RAGAgent_stream`)

**NATS subject format**: `agent.{class}.{id}.{thread_id}.{display_id}.{run_id}.{event_type}.{event_name}.{event_id}`

### MongoDB MCP Tools (Read-Only)

| Tool                              | Use For                        | Key Parameters                 |
| --------------------------------- | ------------------------------ | ------------------------------ |
| `mcp__mongodb__find`              | Query events, configs, classes | `collection`, `filter`, `sort` |
| `mcp__mongodb__aggregate`         | Complex event analysis         | `collection`, `pipeline`       |
| `mcp__mongodb__count`             | Count events by type/run       | `collection`, `filter`         |
| `mcp__mongodb__collection-schema` | Inspect collection structure   | `collection`                   |
| `mcp__mongodb__list-collections`  | List all collections           | —                              |

**Key collections:**

| Collection               | Contains                             | Useful Filters                              |
| ------------------------ | ------------------------------------ | ------------------------------------------- |
| `persisted_agent_events` | All agent events (control + display) | `run_id`, `event.event_name`, `agent_class` |
| `agent_configs`          | Agent profile configs (data mode)    | `agent_class`, `agent_id`                   |
| `agent_classes`          | Agent blueprint discovery data       | `agent_class`                               |
| `threads`                | Conversation threads                 | `thread_id`, `agent_class`                  |

### Langfuse MCP Tools

| Tool                         | Use For                     | Key Parameters    |
| ---------------------------- | --------------------------- | ----------------- |
| `mcp__langfuse__listPrompts` | List all managed prompts    | —                 |
| `mcp__langfuse__getPrompt`   | Get specific prompt by name | `name`, `version` |

For trace inspection (LLM calls, costs, latencies), use the Langfuse web UI at http://localhost:6006.

______________________________________________________________________

## Testing for Verification

After identifying and fixing the issue, verify with tests.

### Running Tests

```bash
cd packages/agent && uv run pytest tests/ -k "<agent_name>" -v
```

### AgentTestRunner Assertions

```python
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

async with AgentTestRunner(agent_type=MyAgent, agent_config=MyConfig.as_form()).test_run() as runner:
    await runner.send_event_from_topic(UserMessageEvent(message="test"))

    # Wait for specific events
    stop = await runner.wait_for_event(StopEvent, timeout=30)
    assert stop is not None

    # Check event history
    events = runner.get_events_of_class(MyCustomEvent)
    assert len(events) == 1

    # Check no duplicate executions
    assert runner.has_stop_event
    assert not runner.has_exception_event
```

### BDD Pattern

```gherkin
Feature: My Agent
  Scenario: Happy path
    Given an agent "MyAgent" is running
    When the user sends "test message"
    Then the agent produces a "StopEvent"
    And the agent does not produce an "ExceptionEvent"
```

Source: `packages/agent/runners/AgentTestRunner.py`, `packages/core/testing/asyncio_utils/bdd.py`

______________________________________________________________________

## Report Template

After debugging, provide a structured report:

```markdown
## Debug Report: {AgentClass}

### Agent
- **Class**: {class name} at {file path}
- **Config**: {config class} at {file path}
- **Steps**: {count} steps, {count} events

### Event DAG
{Step-by-step event chain with types}

### Symptom
{What the user reported}

### Root Cause
{Which rule was violated (R1-R6) or which constraint was broken}
{Specific file and line}

### Evidence
{MCP query results or code analysis that confirms the diagnosis}

### Fix
{Specific code change with before/after}

### Verification
{Test command or assertion to confirm the fix}
```

______________________________________________________________________

## Formal Specification

### Definitions

Let *W* be a workflow defined by:

- *S* = {s₁, s₂, ..., sₙ} : set of steps
- *E* = {e₁, e₂, ..., eₘ} : set of event types
- *I(s)* : E → {required, optional, none} : input signature of step s
- *O(s)* ⊆ E : output types of step s

### Execution Semantics

**State:** At time *t*, the workflow state is *σₜ* = (Eₜ, Sₜ) where:

- *Eₜ* ⊆ E × V : set of (event_type, value) pairs in the event store
- *Sₜ* : S → ℕ : execution count per step

**Dependency Injection:** Parameters are resolved by type, not by name. For a parameter with type *T*, the injector
provides the instance of *T* available in the current context.

**Transition:** Upon event arrival *e* at time *t*:

1. For each *s* ∈ *S*:

   - Let *R(s)* = {e ∈ E : I(s)(e) = required}
   - Let *P(s)* = precondition function (default: λ\_.True)
   - Let *types(P(s))* ⊆ *types(s)* (precondition injectables must be subset of step injectables)
   - If *R(s)* ⊆ types(Eₜ) ∧ P(s)(Eₜ) = True ∧ Sₜ(s) < max_exec(s):
     - Execute *s* asynchronously
     - Sₜ₊₁(s) = Sₜ(s) + 1
     - Eₜ₊₁ = Eₜ ∪ O(s)

2. If ∃e ∈ Eₜ : e ∈ StopEvent:

   - Terminate workflow
   - Reject further event publications

### Race Condition Theorem

**Theorem:** A step *s* with |{e : I(s)(e) = optional}| > 0 and no precondition will execute |{e : I(s)(e) = optional}|
\+ 1 times in the worst case.

**Proof:** By the Minimum Viable Input Rule, *s* executes when R(s) ⊆ Eₜ. Each optional event arrival satisfies this
condition anew. □

**Corollary:** Production agents with optional features require preconditions.

### List Parameter Theorem

**Theorem:** A step *s* with parameter `p: list[T]` executes once for each event of type *T* that arrives.

**Proof:** Let *n* = |{e ∈ Eₜ : type(e) = T}|. A list of length ≥ 1 satisfies the type constraint `list[T]`. When the
first event of type *T* arrives, |list| = 1, which satisfies the constraint, triggering execution. Each subsequent
arrival of type *T* creates a new state Eₜ₊₁ where the constraint is again satisfied with an updated list. □

**Corollary:** To execute exactly once after *N* events of type *T*, use either:

1. `FixedList(T, N)` when *N* is compile-time constant
2. Precondition checking `len(list) >= expected_count` when *N* is runtime-determined

### Validity Conditions

A workflow *W* is valid iff:

1. **Reachability:** ∀s ∈ S, ∃ execution path from StartEvent to s
2. **Termination:** ∀ execution paths eventually reach StopEvent
3. **No Stop Dependencies:** ∀s ∈ S, StopEvent ∉ R(s)
4. **Acyclicity:** The event dependency graph is acyclic (bounded loops via RunContext are valid)

______________________________________________________________________

## Cross-References

- **Building agents correctly**: `/scaffold-agent` — pattern catalog, execution model, implementation checklist
- **NATS infrastructure**: `/nats-events` — event hierarchy, subject format, dispatcher architecture, formal protocol
  specification
- **Event display components**: `/scaffold-event-display` — frontend visualization for new event types
