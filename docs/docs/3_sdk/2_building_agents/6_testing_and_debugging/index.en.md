---
title: Testing and debugging
---

# Testing and debugging

Testing and debugging agents needs a different approach than traditional applications because of their event-driven,
asynchronous nature.

## Unit testing: direct step invocation

The simplest way to test individual steps is to instantiate the agent and call step methods directly with mocked
dependencies:

```python
from unittest.mock import AsyncMock, Mock

async def test_retrieve_step():
    agent = MyAgent()
    event = UserMessageEvent(messages=[...], user=fake_user(), locale="en")
    memory = Mock(spec=AgentMemory)
    memory.search_user_memory = AsyncMock(return_value=MemorySearchResult(...))

    result = await agent.retrieve_step(event, memory)

    assert isinstance(result, RetrieveUserMemoryEvent)
    memory.search_user_memory.assert_called_once()
```

This approach tests step logic in isolation without the dispatcher, NATS, or any infrastructure. Mock injected
dependencies (`AgentMemory`, `EventDisplayer`, `RunContext`) and assert on the returned event.

## Integration testing: pytest-bdd + AgentTestRunner

Use Behavior-Driven Development (BDD) with `pytest-bdd` for testing full agent workflows.

### Basic test structure

1. **Feature file** - Describe behavior in natural language

```gherkin
# tests/features/iterative_agent.feature
Feature: Iterative Processing Agent
  An agent that performs iterative processing with configurable limits

  Scenario: Agent processes data with iteration limit
    Given an iterative processing agent with maximum 2 iterations
    When I ask the agent to process some data
    Then the agent should complete all iterations
    And the agent should stop after reaching the limit
    And the processing should be successful
```

2. **Test implementation** - Connect Gherkin to code

::: code-group
```python [Test setup]
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

scenarios("./features/iterative_agent.feature")

@given(parsers.parse('an iterative processing agent with maximum {max_iterations:d} iterations'))
def _(max_iterations: int):
    return AgentTestRunner(
        agent_type=BoundedLoopAgent,
        agent_config=BoundedLoopAgentConfig(
            agent_id="iterative_agent",
            loop_max=max_iterations
        )
    )
```

```python [Test execution]
@when("I ask the agent to process some data")
@async_test
async def _(agent_runner: AgentTestRunner):
    async with agent_runner.test_run() as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Process this data", role=MessageRole.USER)],
                user=fake_user()
            )
        )

@then("the agent should complete all iterations")
def _(agent_runner: AgentTestRunner):
    iteration_events = agent_runner.get_events_of_class(BeginEvent)
    assert len(iteration_events) == 3, f"Expected 3 iterations, got {len(iteration_events)}"
```
:::

## AgentTestRunner: core testing tool

`AgentTestRunner` provides a sandboxed environment for testing agents.

### Basic usage

```python
async def test_simple_agent():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(agent_id="test_agent")
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(...)
        )

    # Assertions
    assert runner.has_stop_event
    stop_event = runner.get_stop_event()
    assert "expected content" in stop_event.final_message
```

### Event inspection methods

::: details Available methods
```python
# Check for specific events
assert runner.has_start_event
assert runner.has_stop_event

# Get specific events
stop_event = runner.get_stop_event()
start_event = runner.get_start_event()

# Get events by type
all_events = runner.get_events_of_class(MyCustomEvent)
single_event = runner.get_event_of_class(MyCustomEvent)

# Count events
event_count = len(runner.get_events_of_class(ProcessingEvent))
```
:::

## Debugging strategy: trace-driven development

Traditional debugging with breakpoints doesn't work well for event-driven agents. Use trace-driven debugging instead.

> [!TIP] Your debugging toolkit: Langfuse tracing (primary), comprehensive logging, trigger scripts, event flow
> inspection.

### Essential tool: trigger.py scripts

Create `trigger.py` scripts to test specific scenarios:

```python
# my_agent/trigger.py
import asyncio
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

# ALWAYS enable logging for debugging
enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(
            agent_id="debug_agent"
        )
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="test input", role=MessageRole.USER)],
                user=fake_user()
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Interactive testing: run.py scripts

For agents that need to run continuously:

```python
# my_agent/run.py
import asyncio
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        agent_config=MyAgentConfig(agent_id="interactive_agent")
    )

    # Keeps agent running for interactive testing
    await runner.run_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Langfuse tracing: visual debugging

Langfuse provides step-by-step visualization of agent execution at `http://localhost:6006`.

**Key features:**

- **Trace view** - See complete workflow execution
- **Step details** - Click steps to inspect inputs/outputs
- **Timing analysis** - Identify performance bottlenecks
- **Error tracking** - Pinpoint where failures occur

**Debugging workflow:**

1. Run your `trigger.py` script
2. Open Langfuse UI at `localhost:6006`
3. Find your agent's execution trace
4. Click through steps to inspect event flow
5. Identify where things go wrong

## Running tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_my_agent.py

# Run with verbose output
uv run pytest -v tests/

# Run with coverage
uv run pytest --cov=swiss_ai_hub tests/
```

## Implementation checklist

Use this checklist when building or reviewing agents:

### Before implementation

- [ ] Understand the [execution model](../9_execution_model/) — steps are a dependency graph, not a sequence
- [ ] Review the [memory lifecycle](../5_memory/) if your agent uses memory
- [ ] Study production agents: `packages/agent/swiss_ai_hub/agent/agents/rag_agent/`, `expert_rag_agent/`

### For each step

- [ ] Optional parameters (`T | None = None`) have preconditions checking both config AND event presence
- [ ] Precondition parameter types are a subset of the step's injectable types
- [ ] Return type correctly indicates terminal (`StopEvent`) vs. non-terminal
- [ ] No dependency on `StopEvent` or its subclasses as input parameters

### For memory integration

- [ ] LLM step uses `as_stop_step=False` (returns `LLMEvent`, not `LLMStopEvent`)
- [ ] Storage step depends on `LLMEvent`
- [ ] Final step has a precondition waiting for storage completion

### After implementation

- [ ] Langfuse/Phoenix trace shows expected execution order
- [ ] No duplicate step executions (check for the
  [optional parameter trap](../9_execution_model/#the-optional-parameter-trap))
- [ ] No events after `StopEvent`
- [ ] Tests cover all config flag combinations
