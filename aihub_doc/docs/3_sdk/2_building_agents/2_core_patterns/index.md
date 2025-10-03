---
title: Core patterns
index: 2
---

# Core patterns for agent development

Essential patterns for building agents with `aihub_agent`, based on real playground examples.
In the playground/minimal_workflow directory, you can find examples of each pattern supported by the SDK.

Let's start with the basics and build up to more complex workflows.

## Workflow basics

### Simple linear workflow

Sequential processing from input to output.

**Example**: `playground/minimal_workflow/simple_workflow/`

```python
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step

class SimpleAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> ProcessingEvent:
        content = event.messages[-1].content
        return ProcessingEvent(data=content.upper())

    @step()
    async def end_step(self, event: ProcessingEvent) -> StopEvent:
        return StopEvent(final_message=f"Processed: {event.data}")
```

Use for simple transformations, data validation, single-purpose utilities.

### Conditional workflow

Different processing paths based on input conditions.

**Example**: `playground/minimal_workflow/conditional_workflow/`

```python
class ConditionalAgent(Agent):
    @step()
    async def analyze_input(self, event: UserMessageEvent) -> HighPriorityEvent | LowPriorityEvent:
        content = event.messages[-1].content
        if "urgent" in content.lower():
            return HighPriorityEvent(content=content)
        return LowPriorityEvent(content=content)

    @step()
    async def handle_high_priority(self, event: HighPriorityEvent) -> StopEvent:
        return StopEvent(final_message=f"URGENT: {event.content}")

    @step()
    async def handle_low_priority(self, event: LowPriorityEvent) -> StopEvent:
        return StopEvent(final_message=f"Normal: {event.content}")
```

Use for routing logic, priority handling, different processing modes.

### Context management

Using RunContext and ThreadContext for state management.

**Example**: `playground/minimal_workflow/context_workflow/`

::: code-group

```python [Context tracking]
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext

class ContextAgent(Agent):
    @step()
    async def track_interactions(
        self,
        event: UserMessageEvent,
        run_context: RunContext,
        thread_context: ThreadContext
    ) -> ProcessedEvent:
        # Thread context persists across runs
        count = await thread_context.get("interaction_count", 0)
        await thread_context.set("interaction_count", count + 1)

        # Run context is ephemeral (this run only)
        await run_context.set("current_message", event.messages[-1].content)

        return ProcessedEvent(interaction_number=count + 1)
```

:::

> [!TIP]
> Use for user personalization, conversation continuity, temporary state.

### Bounded loop

Iterative processing with termination conditions.

**Example**: `playground/minimal_workflow/bounded_loop/`

```python
class BoundedLoopAgent(Agent):
    @step()
    async def initialize(self, event: UserMessageEvent, run_context: RunContext) -> LoopEvent:
        await run_context.set("loop_count", 0)
        return LoopEvent(iteration=0)

    @step()
    async def process_iteration(
        self,
        event: LoopEvent,
        config: BoundedLoopAgentConfig,
        run_context: RunContext
    ) -> LoopEvent | CompleteEvent:
        count = await run_context.get("loop_count")

        if count < config.max_iterations:
            await run_context.set("loop_count", count + 1)
            return LoopEvent(iteration=count + 1)

        return CompleteEvent(total_iterations=count)

    @step()
    async def finalize(self, event: CompleteEvent) -> StopEvent:
        return StopEvent(final_message=f"Completed {event.total_iterations} iterations")
```

Use for iterative refinement, retry logic, progressive analysis.



## Display events

Providing user feedback during processing.

```python
from aihub_lib.displayers.EventDisplayer import EventDisplayer

class DisplayAgent(Agent):
    @step()
    async def process_with_feedback(
        self,
        event: UserMessageEvent,
        displayer: EventDisplayer
    ) -> StopEvent:
        await displayer.display_thought("Starting analysis...")
        await asyncio.sleep(1)

        await displayer.display_thought("Analysis 50% complete...")
        await asyncio.sleep(1)

        await displayer.display_chunk("Analysis complete! Here are the results:")

        return StopEvent(final_message="Processing finished")
```

Use for long-running operations, progress updates, transparency.

## Configuration-driven behavior

Using agent configuration to control behavior.

```python
class ConfigurableAgentConfig(AgentConfig):
    processing_mode: Literal["fast", "thorough"] = "fast"
    max_retries: int = 3

class ConfigurableAgent(Agent):
    @step()
    async def configurable_step(
        self,
        event: UserMessageEvent,
        config: ConfigurableAgentConfig
    ) -> StopEvent:
        if config.processing_mode == "fast":
            result = "Quick result"
        else:
            result = "Detailed analysis result"

        return StopEvent(final_message=result)
```

Use for multiple deployment environments, A/B testing, feature flags.



## Next steps

For more advanced patterns, explore:

- [Human in the loop](../3_human_in_the_loop/) - Interactive workflows
- [Multi-agent systems](../4_multi_agent_systems/) - Agent coordination
