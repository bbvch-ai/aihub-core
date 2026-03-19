---
title: Multi-Agent Systems
---

# Multi-Agent Systems

Complex problems are often best solved by breaking them into smaller, manageable parts. The **Agent in the Loop (AITL)**
pattern allows you to create multi-agent systems where a primary **Orchestrator** agent can delegate specific tasks to
one or more specialized **Worker** agents.

**When to use it**:

- To create modular, reusable components (e.g., an agent that only summarizes documents).
- To separate concerns (e.g., one agent for data retrieval, another for analysis).
- To build complex chains or parallel workflows that combine the strengths of multiple agents.

## How It Works

The AITL pattern is managed by a trio of events that orchestrate the delegation, execution, and response between agents.

1. **Orchestrator sends a Request**: The Orchestrator agent returns an `AgentInTheLoop.request` event. This event acts
   as a package, containing the `start_event` for the Worker and the routing information for the response. This pauses
   the Orchestrator's workflow.
2. **Worker executes its task**: The dispatcher delivers the `start_event` to the specified Worker agent. The Worker
   runs its own self-contained workflow, completely unaware that it was called by another agent.
3. **Worker completes and responds**: When the Worker finishes, it returns a `StopEvent` (or an `ExceptionEvent` if it
   fails). The system automatically wraps this final event into either an `AgentInTheLoop.response` or
   `AgentInTheLoop.exception` event.
4. **Orchestrator resumes**: The dispatcher routes the response or exception event back to the Orchestrator, which
   resumes its workflow in a separate step designed to handle the result.

The `AgentInTheLoop` helper class simplifies this process by providing a convenient `invoke` method to create the
request event.

______________________________________________________________________

## Core Pattern: Orchestrator and Worker

This example shows an `OrchestratorAgent` that asks a `WorkerAgent` to perform a simple calculation. Notice that the
`WorkerAgent` is just a standard, self-contained agent.

**Reference**: `playground/minimal_workflow/agent_in_the_loop_workflow/`

::: code-group
```python [OrchestratorAgent.py]
from swiss_ai_hub.core.events.agent.aitl.agent_in_the_loop import AgentInTheLoop

class OrchestratorAgent(Agent):
    @step()
    async def delegate_task(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # 1. Delegate the task to the WorkerAgent
        return AgentInTheLoop.invoke(
            agent_id="worker_agent",
            agent_class="WorkerAgent",
            start_event=event  # Pass the original event to the worker
        )

    @step()
    async def handle_result(self, response: AgentInTheLoop.response) -> StopEvent:
        # 3a. This step runs if the worker succeeds
        result = response.stop_event.result
        return StopEvent(final_message=f"Worker succeeded with result: {result}")

    @step()
    async def handle_error(self, response: AgentInTheLoop.exception) -> StopEvent:
        # 3b. This step runs if the worker fails
        error_message = response.exception_event.message
        return StopEvent(final_message=f"Worker failed: {error_message}")
```

```python [WorkerAgent.py]
class WorkerAgent(Agent):
    @step()
    async def process_number(self, event: UserMessageEvent) -> ExtractNumberEvent:
        # 2. The worker agent performs its logic...
        number = int(event.messages[-1].content)
        return ExtractNumberEvent(number=number)

    @step()
    async def calculate_result(self, event: ExtractNumberEvent) -> WorkerStopEvent:
        # ...and returns its own custom StopEvent with a result.
        return WorkerStopEvent(result=event.number * 2)
```
:::

## Context Sharing

You can control which contexts are shared from the Orchestrator to the Worker. This is useful for maintaining a
consistent conversation or UI experience.

- `share_thread_id=True` (Default): The Worker shares the same conversation memory (`ThreadContext`) as the
  Orchestrator.
- `share_display_id=True` (Default): The Worker's `DisplayEvent`s appear in the same UI stream as the Orchestrator's.
- `share_run_id=False` (Default): The Worker executes in its own independent run.

```python
AgentInTheLoop.invoke(
    agent_id="specialized_agent",
    agent_class="SpecializedAgent",
    start_event=event,
    share_thread_id=True,      # Share conversation memory
    share_display_id=True,     # Share UI context
    share_run_id=False         # Recommended: Keep runs separate
)
```

::: warning
Sharing the `run_id` is an advanced feature and can lead to unexpected behavior, as both agents would be writing to the
same ephemeral `RunContext`. It is almost always better to keep it `False`.
:::

## Common Multi-Agent Patterns

### Specialized Processing (Router)

An orchestrator acts as a router, delegating tasks to different worker agents based on the input.

```python
class DocumentRouterAgent(Agent):
    @step()
    async def route_document(self, event: DocumentEvent) -> AgentInTheLoop.request:
        if event.document_type == "financial":
            # Delegate to the financial analysis agent
            return AgentInTheLoop.invoke(agent_id="financial_analyzer", ...)
        elif event.document_type == "legal":
            # Delegate to the legal analysis agent
            return AgentInTheLoop.invoke(agent_id="legal_analyzer", ...)
```

### Sequential Agent Chain

A workflow where the output of one worker agent becomes the input for the next, creating a processing pipeline.

```python
class ProcessingChainAgent(Agent):
    @step()
    async def extract_data(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        # First agent in the chain
        return AgentInTheLoop.invoke(agent_id="data_extractor", ...)

    @step()
    async def validate_data(self, response: AgentInTheLoop.response) -> AgentInTheLoop.request:
        # The result from the first agent is used to start the second
        extracted_data = response.stop_event.result
        validation_event = ProcessingEvent(data=extracted_data)
        return AgentInTheLoop.invoke(agent_id="data_validator", start_event=validation_event)
```

### Parallel Agent Execution (Fan-Out)

An orchestrator delegates the same task to multiple agents simultaneously and then aggregates their responses.

```python
class ParallelProcessorAgent(Agent):
    @step()
    async def fan_out(self, event: UserMessageEvent) -> list[AgentInTheLoop.request]:
        # Return a list of requests to trigger parallel execution
        return [
            AgentInTheLoop.invoke(agent_id="processor_a", ...),
            AgentInTheLoop.invoke(agent_id="processor_b", ...)
        ]

    @step()
    async def combine_results(self, responses: list[AgentInTheLoop.response]) -> StopEvent:
        # This step waits for all responses before running
        results = [r.stop_event.result for r in responses]
        return StopEvent(final_message=f"Combined results: {results}")
```
