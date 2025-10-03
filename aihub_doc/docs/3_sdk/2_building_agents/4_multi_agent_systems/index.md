---
title: Multi-agent systems
index: 4
---

# Multi-agent systems

Agents can coordinate work by delegating tasks to specialized agents. This pattern lets you build complex workflows where different agents handle specific domains or capabilities.

## Core pattern: agent-in-the-loop

One agent (orchestrator) invokes another agent (worker) and waits for its result:

```python
from aihub_lib.nats.events.agent_in_the_loop.AgentInTheLoop import AgentInTheLoop

class OrchestratorAgent(Agent):
    @step()
    async def delegate_task(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_id="worker_agent",
            agent_class="WorkerAgent",
            start_event=event
        )

    @step()
    async def handle_result(self, response: AgentInTheLoop.response) -> StopEvent:
        result = response.stop_event.result
        return StopEvent(final_message=f"Task completed with result: {result}")

    @step()
    async def handle_error(self, response: AgentInTheLoop.exception) -> StopEvent:
        return StopEvent(final_message="Task failed, handled gracefully")
```

**Reference**: `playground/minimal_workflow/agent_in_the_loop_workflow/`

## Event flow

::: details Steps
1. **Request** - Orchestrator emits `AgentInTheLoop.request`
2. **Delegation** - Worker agent receives and processes the task
3. **Response** - Worker completes and returns `AgentInTheLoop.response`
4. **Resume** - Orchestrator continues with the result
:::

## Context sharing

Control what context gets shared between agents:

```python
AgentInTheLoop.invoke(
    agent_id="specialized_agent",
    agent_class="SpecializedAgent",
    start_event=event,
    share_thread_id=True,      # Conversation context (default: True)
    share_display_id=True,     # UI context (default: True)
    share_run_id=False         # Run context (default: False, rarely needed)
)
```

> [!WARNING]
> Rarely share run context between agents. It can cause unexpected behavior.

## Common patterns

### Specialized processing

Delegate specific tasks to domain experts:

```python
class DocumentAgent(Agent):
    @step()
    async def analyze_document(self, event: DocumentEvent) -> AgentInTheLoop.request:
        if event.document_type == "financial":
            return AgentInTheLoop.invoke(
                agent_id="financial_analyzer",
                agent_class="FinancialAnalyzerAgent",
                start_event=event
            )
        elif event.document_type == "legal":
            return AgentInTheLoop.invoke(
                agent_id="legal_analyzer",
                agent_class="LegalAnalyzerAgent",
                start_event=event
            )
```

### Sequential agent chain

Chain multiple agents for complex workflows:

::: code-group

```python [Chain processing]
class ProcessingChainAgent(Agent):
    @step()
    async def extract_data(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_id="data_extractor",
            agent_class="DataExtractorAgent",
            start_event=event
        )

    @step()
    async def validate_data(self, response: AgentInTheLoop.response) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_id="data_validator",
            agent_class="DataValidatorAgent",
            start_event=ProcessingEvent(data=response.stop_event.result)
        )

    @step()
    async def finalize(self, response: AgentInTheLoop.response) -> StopEvent:
        return StopEvent(final_message="Processing chain completed")
```

:::

### Parallel agent execution

Fan out to multiple agents for parallel processing:

```python
class ParallelProcessorAgent(Agent):
    @step()
    async def fan_out(self, event: UserMessageEvent) -> list[AgentInTheLoop.request]:
        return [
            AgentInTheLoop.invoke(
                agent_id="agent_a",
                agent_class="ProcessorA",
                start_event=event
            ),
            AgentInTheLoop.invoke(
                agent_id="agent_b",
                agent_class="ProcessorB",
                start_event=event
            )
        ]

    @step()
    async def combine_results(self, responses: list[AgentInTheLoop.response]) -> StopEvent:
        results = [r.stop_event.result for r in responses]
        return StopEvent(final_message=f"Combined results: {results}")
```

### Error handling

Handle agent failures gracefully:

```python
class ResilientOrchestratorAgent(Agent):
    @step()
    async def try_primary_agent(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        return AgentInTheLoop.invoke(
            agent_id="primary_agent",
            agent_class="PrimaryAgent",
            start_event=event
        )

    @step()
    async def handle_success(self, response: AgentInTheLoop.response) -> StopEvent:
        return StopEvent(final_message=response.stop_event.result)

    @step()
    async def handle_failure(self, response: AgentInTheLoop.exception) -> AgentInTheLoop.request:
        # Fallback to backup agent
        return AgentInTheLoop.invoke(
            agent_id="backup_agent",
            agent_class="BackupAgent",
            start_event=response.original_start_event
        )
```

## Testing

```python
async def test_agent_coordination():
    orchestrator_runner = AgentTestRunner(
        agent_type=OrchestratorAgent,
        agent_config=orchestrator_config
    )

    # Test the orchestrator delegates correctly
    async with orchestrator_runner.test_run() as topic:
        await orchestrator_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(...)
        )

    assert orchestrator_runner.has_stop_event
    result = orchestrator_runner.get_stop_event()
    assert "completed" in result.final_message
```

## When to use

::: details Use cases
- **Domain specialization** - Different agents handle specific expertise areas
- **Separation of concerns** - Break complex workflows into focused components
- **Reusability** - Specialized agents can be reused across workflows
- **Scalability** - Distribute processing across multiple agent instances
- **Fault tolerance** - Fallback agents for resilient systems
:::

## Best practices

> [!TIP]
> Define clear input/output contracts between agents. Only share necessary context.

- Always handle agent failures and exceptions
- Test agent interactions both in isolation and integration
- Use Phoenix tracing to observe multi-agent workflows
- Keep individual agents focused on single responsibilities

Multi-agent systems enable sophisticated workflows while maintaining simplicity and testability.