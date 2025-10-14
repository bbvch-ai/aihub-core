---
title: Core Workflow Patterns
index: 2
---

# Core Workflow Patterns

This page covers the fundamental, reusable patterns for building agent workflows. By combining these building blocks, you can create sophisticated and robust agents. Each pattern includes a concise code example and an explanation of its purpose.

For complete, runnable examples, see the `playground/minimal_workflow/` directory.


## Workflow Control Patterns

These patterns define the fundamental flow of execution in an agent, from simple sequences to complex branching and parallel processing.

### Simple Linear Workflow

A **linear workflow** is the most basic pattern, where steps execute in a direct sequence from a start event to a stop event.

  * **When to use it**: Ideal for simple, sequential tasks like processing a single input to produce a single output.
  * **How it works**: One step returns a `ControlEvent` that is consumed by the next step, forming a direct chain.

```python
class SimpleAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> SimpleEventA:
        return SimpleEventA(payload=event.messages[-1].content)

    @step()
    async def end_step(self, event: SimpleEventA) -> StopEvent:
        return StopEvent()
```

### Conditional Workflow (Branching)

A **conditional workflow** creates decision points, allowing the agent to follow different paths based on runtime conditions.

  * **When to use it**: For routing logic, handling different user intents, or classifying data.
  * **How it works**: A step's return type hint includes multiple event types (e.g., `EventA | EventB`). The dispatcher routes the workflow to the step that handles the specific event type that was returned.

<!-- end list -->

```python
class ConditionalAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> AboveThresholdEvent | BelowThresholdEvent:
        if random.random() > 0.5:
            return AboveThresholdEvent()
        return BelowThresholdEvent()

    @step()
    async def end_step(self, event: AboveThresholdEvent | BelowThresholdEvent) -> StopEvent:
        # This step runs for either outcome of the start_step
        return StopEvent()
```

### Bounded Loops (Iteration)

A **looping workflow** executes a step or a series of steps multiple times. It's crucial to ensure loops have a clear exit condition.

  * **When to use it**: Ideal for retry logic, iterative refinement, or processing a batch of items.
  * **How it works**: A step returns an event that routes the flow back to an earlier step, using `RunContext` to track state. Use the `@step(max_executions_per_run=N)` parameter as a safety guard against infinite loops.


```python
class BoundedLoopAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent, run_context: RunContext) -> BeginEvent:
        await run_context.set("loop_count", 0) # Initialize counter
        return BeginEvent(count=0)

    # ... other steps in the loop ...

    @step()
    async def decision_step(self, event: BoundedLoopAEvent, run_context: RunContext) -> DecisionEvent | BeginEvent:
        loop_count = await run_context.get("loop_count")
        if loop_count < 5:
            await run_context.set("loop_count", loop_count + 1)
            return BeginEvent(count=loop_count + 1) # Loop back to start_step
        return DecisionEvent() # Break the loop
```

### Fan-Out / Fan-In (Parallel Processing)

This powerful pattern allows an agent to split a task into multiple parallel branches (**fan-out**) and then aggregate the results (**fan-in**).

  * **When to use it**: For processing multiple documents, making parallel API calls, or any task that can be broken down into independent sub-tasks.
  * **How it works**:
      * **Fan-Out**: A step returns a `list` of events. The dispatcher then triggers the next step *once for each event in the list*, creating parallel execution branches.
      * **Fan-In**: A later step uses a **precondition** to wait until all parallel branches have produced their result events before it runs.


```python
# The precondition function checks if all results are ready
@precondition()
async def ensure_enough_events(events: list[ParallelEvent], config: PreconditionAgentConfig) -> bool:
    return len(events) == config.number_of_events

class ParallelProcessingAgent(Agent):
    @step()
    async def fan_out_step(self, _: StartEvent, config: PreconditionAgentConfig) -> list[ParallelEvent]:
        # 1. Fan-Out: Return a list of events to start parallel branches
        return [ParallelEvent(payload=str(i)) for i in range(config.number_of_events)]

    @step()
    async def process_in_parallel(self, event: ParallelEvent) -> ResultEvent:
        # 2. This step runs in parallel for each ParallelEvent
        # ... process the event ...
        return ResultEvent(...)

    @step(precondition=ensure_enough_events)
    async def fan_in_step(self, _: list[ResultEvent]) -> StopEvent:
        # 3. Fan-In: This step only runs after the precondition is met
        # (i.e., all parallel branches have produced a ResultEvent)
        return StopEvent()
```

## State and Configuration Patterns

These patterns focus on managing an agent's memory and behavior dynamically.

### Context Management (The Agent's Memory)

The SDK provides injectable **context objects** to store information during and between runs. 

  * **When to use it**: For tracking progress, remembering user preferences, or passing data between non-sequential steps.
  * **How it works**:
      * **`RunContext`**: Ephemeral memory for a *single* workflow run. It's created on a `StartEvent` and destroyed on a `StopEvent`.
      * **`ThreadContext`**: Persistent memory for a conversation *thread*. It survives across multiple agent runs.

```python
class ContextAgent(Agent):
    @step()
    async def start_step(self, event: CustomStartEvent, thread_context: ThreadContext, run_context: RunContext) -> ContextEvent:
        thread_count = await thread_context.get("count", 0) # Persists across runs
        run_count = await run_context.get("count", 0)     # Resets each run
        
        await thread_context.set("count", thread_count + 1)
        await run_context.set("count", run_count + 1)
        return ContextEvent(thread_count=thread_count + 1, run_count=run_count + 1)
```

### Configuration-Driven Behavior

Separate your agent's logic from its settings using `AgentConfig` and `StepConfig` classes.

  * **When to use it**: To create reusable agents, manage settings for different environments.
  * **How it works**: The dispatcher injects the entire `AgentConfig` or a specific `StepConfig` into your step based on its type hint.


```python
class ConfiguredAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, config: StartStepConfig) -> EventConfiguredA:
        # Injects only the specific configuration for this step
        return EventConfiguredA(payload=config.some_step_value)

    @step()
    async def middle_step(self, event: EventConfiguredA, config: ConfiguredAgentConfig) -> EventConfiguredB:
        # Injects the entire agent's configuration
        return EventConfiguredB(payload=config.some_agent_value)
```


## User Interaction and Feedback

This pattern is essential for creating transparent and user-friendly agents.

### Displaying Information

Agents can provide real-time feedback to the user without interrupting the workflow's logic.

  * **When to use it**: To show "chain-of-thought" reasoning, provide status updates for long-running tasks, or stream back partial results.
  * **How it works**: Inject the `EventDisplayer` into a step. Use its methods (`display_thought`, `display_chunk`) to send `DisplayEvent`s to the user interface. These events do not affect the control flow.


```python
class DisplayingAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, displayer: EventDisplayer) -> StopEvent:
        await displayer.display_thought("Let me think....")
        await displayer.display_chunk("This is a partial result sent to the user.", model_name="gpt-4")
        # ... continue processing ...
        return StopEvent()
```