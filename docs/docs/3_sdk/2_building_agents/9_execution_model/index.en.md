---
title: Execution Model
---

# Execution Model

Understanding the execution model is essential for building correct agents. Most bugs in agent development stem from
misunderstanding how the dispatcher schedules steps. This page explains the mechanics in detail.

## The DAG mental model

An agent is not a sequence of function calls. It is a **Directed Acyclic Graph (DAG)** where nodes are **steps** and
edges are **events**. The workflow topology is implicit, derived entirely from type hints on your `@step` methods.

**Steps declare data requirements, not execution order.**

A step executes when the workflow engine can provide all its required parameters — not when a prior step "calls" it.
This has three critical implications:

1. Any step can depend on any event, including the original `StartEvent`, regardless of how many steps have executed
   since
2. Parallel execution is automatic: steps with independent dependencies execute concurrently
3. The workflow is a dependency graph, not a sequence

### The dispatcher's three-phase cycle

The `AgentDispatcher` operates as a reactive state machine:

1. **Ingestion**: Subscribes to the agent's NATS JetStream subject and receives events
2. **Evaluation**: Upon receiving event *e*, identifies all steps *S* where *e* matches an input type of *S*
3. **Trigger**: Invokes step *S* if and only if all required inputs are present in the event store

Execution order is emergent, not prescriptive.

## Data dependency thinking

### Two perspectives

#### Top-down: "What do I have, what do I do next?"

Start with input, proceed toward output. Natural for sequential pipelines but encourages linear chains and unnecessary
data passing.

#### Bottom-up: "What do I need, what provides it?"

Start with desired output, work backward. Naturally identifies all data dependencies and makes direct dependencies on
`StartEvent` obvious.

### The critical difference

**Top-down produces this (problematic):**

```python
@step()
async def retrieve(self, event: UserMessageEvent) -> RetrieveEvent:
    nodes = await retriever.retrieve(event.user_query)
    return RetrieveEvent(nodes=nodes, user_query=event.user_query)  # Passing query forward

@step()
async def respond(self, event: RetrieveEvent) -> StopEvent:
    return await generate(event.user_query, event.nodes)  # Accessing passed-through data
```

The `user_query` field on `RetrieveEvent` is **pass-through pollution** — the event carries data it doesn't semantically
represent just to shuttle it downstream.

**Bottom-up produces this (correct):**

```python
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

Each event contains only the data it semantically represents. The `respond` step declares exactly what it needs: the
retrieved nodes *and* the original user message.

### The unified approach

1. **Sketch top-down** to understand logical flow
2. **Refine bottom-up** to identify true dependencies
3. **Validate** both directions

For each step, ask:

- *Top-down:* What transformation does this step perform?
- *Bottom-up:* What is the minimal set of data this step requires?

## Step execution isolation

::: warning
A fresh `Agent` instance is created for **every** step execution. Do not store state on `self` — it will be lost between
steps. Multiple steps for the same run may execute in parallel on different instances.
:::

Use events to pass data between steps, `RunContext` for loop counters, and `ThreadContext` for cross-run state.

## Execution rules

### The minimum viable input rule

A step executes the moment its minimum required inputs are satisfied.

Given a step *S* with:

- **R(S)** = set of required parameters (no default value)
- **O(S)** = set of optional parameters (typed as `T | None = None`)
- **E** = set of available events

**Trigger condition:** Execution occurs when **R(S) ⊆ E** — all required parameter types are available in the event
store.

- Required parameters: injected from matching events
- Optional parameters: injected if present, otherwise `None`

### The race condition problem

Consider a step with both required and optional event parameters:

```python
@step()
async def merge(self, primary: EventA, secondary: EventB | None = None) -> OutputEvent:
    ...
```

**Execution sequence:**

| Time | Event arrives | R(S) satisfied | O(S) satisfied | Result                                          |
| ---- | ------------- | -------------- | -------------- | ----------------------------------------------- |
| t1   | EventA        | Yes            | No             | Step executes with `(EventA, None)`             |
| t2   | EventB        | Yes            | Yes            | Step executes **again** with `(EventA, EventB)` |

The step executed twice. This is not a bug — it is the defined behavior. The minimum viable input rule triggers
execution as soon as required parameters are satisfied, and again when optional parameters arrive.

::: warning
Do not use optional event parameters to "wait" for data that might arrive later. Use `@precondition` instead.
:::

### The six execution rules

| Rule   | Statement                                          | Violation consequence                                       |
| ------ | -------------------------------------------------- | ----------------------------------------------------------- |
| **R1** | Steps execute when R(S) ⊆ E                        | Race conditions with optional parameters                    |
| **R2** | Steps may execute multiple times per run           | Duplicate processing, wasted resources                      |
| **R3** | `list[Event]` parameters trigger on each new event | Unexpected re-execution without precondition or `FixedList` |
| **R4** | No events may be published after `StopEvent`       | Illegal workflow state                                      |
| **R5** | Preconditions gate execution                       | Deadlock if precondition never satisfies                    |
| **R6** | All events persist until run completion            | Late steps can access early events                          |

## Synchronization primitives

### The `@precondition` decorator

A precondition is a gatekeeper function that executes before step logic.

**Mechanics:**

- The dispatcher invokes the precondition using the same dependency injection as steps
- If it returns `False`, the step is not scheduled
- The precondition re-evaluates on each new event arrival

**Critical constraint:** Precondition parameters must be a **subset** of the step's injectable types. Parameter names
are irrelevant; dependency injection resolves by type.

```python
from aihub_agent.workflow.decorators.precondition import precondition

@precondition()
async def check_ready(
    evt: EventB | None,  # Name differs from step parameter — that's fine
    cfg: AgentConfig,    # Resolved by type, not name
) -> bool:
    if cfg.enable_feature and evt is None:
        return False  # Wait for optional event
    return True

@step(precondition=check_ready)
async def process(
    self,
    required: EventA,
    optional: EventB | None = None,  # Type matches precondition's 'evt'
    config: AgentConfig,             # Type matches precondition's 'cfg'
) -> OutputEvent:
    # Guaranteed: if config.enable_feature, optional is not None
    ...
```

### List parameters

When a step parameter is typed as `list[EventType]`, the step executes on **each new event arrival**:

```python
@step()
async def aggregate(self, results: list[ResultEvent]) -> StopEvent:
    # Executes every time a ResultEvent arrives
    ...
```

**Execution sequence for 3 produced events:**

| Event arrival  | List contents                                    | Step executes |
| -------------- | ------------------------------------------------ | ------------- |
| ResultEvent #1 | [ResultEvent #1]                                 | Yes           |
| ResultEvent #2 | [ResultEvent #1, ResultEvent #2]                 | Yes           |
| ResultEvent #3 | [ResultEvent #1, ResultEvent #2, ResultEvent #3] | Yes           |

The step executes 3 times. This follows from the minimum viable input rule: a list of length 1 satisfies `list[T]`.
Events in the list are ordered by arrival time.

### FixedList for compile-time known counts

When you know the exact number of events at definition time, use `FixedList` to block until all events are available:

```python
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import FixedList

N = 5

@step()
async def aggregate(self, results: FixedList(ResultEvent, N)) -> StopEvent:
    # Executes once when exactly N ResultEvents are available
    ...
```

`FixedList` requires *N* to be known at definition time.

### Precondition with expected count

When the count is determined at runtime (e.g., from configuration), use a precondition:

```python
@precondition()
async def check_all_arrived(results: list[ResultEvent], config: AgentConfig) -> bool:
    return len(results) >= config.expected_count

@step(precondition=check_all_arrived)
async def aggregate(self, results: list[ResultEvent], config: AgentConfig) -> StopEvent:
    # Executes once when expected count reached
    ...
```

### Event resolution strategy

When binding events to step parameters:

1. **Fixed collection:** `FixedList(Event, N)` blocks until exactly *N* events are available, then returns all *N*
2. **Unbounded list:** `list[Event]` returns all events of that type currently available; step re-executes on each new
   arrival
3. **Single instance:** If the triggering event matches the parameter type, that instance is used. Otherwise, the most
   recently created event of that type is used.

## Engineering constraints (anti-patterns)

### The dangling stop violation

**Constraint:** No step may depend on `StopEvent` or any subclass as an input parameter.

When a `StopEvent` is emitted, the run terminates. Subsequent steps are not scheduled.

```python
# VIOLATION: depending on stop event
@step()
async def cleanup(self, stop: LLMStopEvent) -> CleanupEvent:
    ...  # Never executes

# CORRECT: use non-stop event, then explicit stop
@step()
async def respond(self, event: InputEvent, displayer: EventDisplayer) -> LLMEvent:
    return await displayer.display_llm_stream(..., as_stop_step=False)

@step()
async def cleanup(self, llm: LLMEvent) -> CleanupEvent:
    ...

@step(precondition=cleanup_complete)
async def finalize(self, cleanup: CleanupEvent) -> StopEvent:
    return StopEvent()
```

### The context smuggle violation

**Constraint:** Data must flow between steps via events, not `RunContext`.

Context-based data passing creates invisible dependencies, breaks the DAG, and causes race conditions.

```python
# VIOLATION: using context as data bus
@step()
async def step_a(self, event: InputEvent, run_context: RunContext) -> EventA:
    await run_context.set("query", event.query)  # Wrong
    return EventA()

@step()
async def step_b(self, event: EventA, run_context: RunContext) -> OutputEvent:
    query = await run_context.get("query")  # Wrong — invisible dependency
    ...

# CORRECT: direct event dependency
@step()
async def step_b(self, event_a: EventA, original: InputEvent) -> OutputEvent:
    query = original.query  # Explicit, visible dependency
    ...
```

**Exception:** `RunContext` is valid for control flow state only (loop counters, recursion depth, retry tracking).

### The config lie violation

**Constraint:** Do not check `AgentConfig` inside a step to determine if you should have waited for an event.

By execution time, the dispatcher has already made the scheduling decision. The race condition has already occurred.

```python
# VIOLATION: config check inside step
@step()
async def process(self, required: EventA, optional: EventB | None = None, config: AgentConfig) -> OutputEvent:
    if config.enable_feature and optional is None:
        return None  # Too late — step already executed with None

# CORRECT: precondition prevents premature scheduling
@step(precondition=check_ready)
async def process(self, required: EventA, optional: EventB | None = None, config: AgentConfig) -> OutputEvent:
    # If config.enable_feature, precondition guarantees optional is not None
    ...
```

### The double-dip violation

**Constraint:** Do not reuse the same event type for multiple distinct logical stages.

The dispatcher queries by type. Downstream steps may trigger unpredictably or process the wrong instance.

```python
# VIOLATION: same event type for different stages
@step()
async def validate(self, event: InputEvent) -> ProcessedEvent:
    return ProcessedEvent(data="validated")

@step()
async def enrich(self, event: ProcessedEvent) -> ProcessedEvent:  # Same type!
    return ProcessedEvent(data="enriched")

# CORRECT: distinct types for each logical state
@step()
async def validate(self, event: InputEvent) -> ValidatedEvent:
    return ValidatedEvent(data="validated")

@step()
async def enrich(self, event: ValidatedEvent) -> EnrichedEvent:
    return EnrichedEvent(data="enriched")
```

### The optional parameter trap

**Constraint:** Optional parameters without preconditions cause re-execution.

```python
# Executes twice: once with b=None, again with b=EventB
@step()
async def process(self, a: EventA, b: EventB | None = None) -> OutputEvent:
    ...

# Executes once when precondition satisfied
@step(precondition=check_b_ready)
async def process(self, a: EventA, b: EventB | None = None, config: AgentConfig) -> OutputEvent:
    ...
```

## Troubleshooting

### Step executes multiple times

**Symptom:** Phoenix/Langfuse trace shows duplicate step executions.

**Root cause:** Optional parameters without precondition. Step triggers when R(S) ⊆ E, then again when optional events
arrive.

**Diagnosis:**

1. Check step signature for `param: T | None = None`
2. Verify `@step(precondition=...)` is present
3. Verify precondition checks both config AND event presence

**Fix:** Add a precondition that returns `False` until all expected events arrive.

### Step never executes

**Symptom:** Step absent from trace.

**Root cause:** Precondition never returns `True`, or required event never emitted by an upstream step.

**Diagnosis:**

1. Add logging to precondition
2. Verify upstream steps emit expected events
3. Check config flags — a disabled feature may prevent event emission

**Fix:** Ensure precondition handles disabled features: `if not config.enable_feature: return True`

### Events after StopEvent

**Symptom:** Trace shows events timestamped after `StopEvent`.

**Root cause:** A step depends on `StopEvent` or a subclass (like `LLMStopEvent`), or an async step completes after
termination.

**Fix:** Use `LLMEvent` (not `LLMStopEvent`) with `as_stop_step=False`, then add an explicit final step with a
precondition.

### Precondition parameter mismatch

**Symptom:** Runtime error about unresolvable parameters.

**Root cause:** Precondition requests a type not injectable in the step's context.

**Fix:** Ensure precondition parameter types are a subset of the step's injectable types. Parameter names are
irrelevant; only types must match.

## Implementation checklist

### Before implementation

- [ ] Understand execution semantics (this page)
- [ ] Review the [memory lifecycle](../5_memory/) if using memory
- [ ] Study production agents in `aihub_agent/agents/RagAgent/` and `ExpertRagAgent/`

### For each step

- [ ] Optional parameters have preconditions checking config AND event presence
- [ ] Precondition parameter types are a subset of step's injectable types
- [ ] Return type correctly indicates terminal (`StopEvent`) vs. non-terminal
- [ ] No dependency on `StopEvent` or its subclasses

### For memory integration

- [ ] LLM step uses `as_stop_step=False` (returns `LLMEvent`, not `LLMStopEvent`)
- [ ] Storage step depends on `LLMEvent`
- [ ] Final step has precondition waiting for storage completion

### After implementation

- [ ] Trace shows expected execution order (Langfuse or Phoenix)
- [ ] No duplicate step executions
- [ ] No events after `StopEvent`
- [ ] Tests cover all config flag combinations
