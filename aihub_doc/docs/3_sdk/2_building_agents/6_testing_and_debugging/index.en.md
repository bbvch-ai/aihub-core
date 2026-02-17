---
title: Testing and debugging
---

# Testing and debugging

Testing and debugging agents needs a different approach than traditional applications because of their event-driven,
asynchronous nature.

## Testing framework: pytest-bdd + AgentTestRunner

Use Behavior-Driven Development (BDD) with `pytest-bdd` for testing agent workflows.

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
from aihub_lib.testing.asyncio_utils.bdd import async_test
from pytest_bdd import given, parsers, scenarios, then, when
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/iterative_agent.feature")

@given(parsers.parse('an iterative processing agent with maximum {max_iterations:d} iterations'))
def _(max_iterations: int):
    return AgentTestRunner(
        agent_type=BoundedLoopAgent,
        default_agent_config=BoundedLoopAgentConfig(
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
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

# ALWAYS enable logging for debugging
enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        default_agent_config=MyAgentConfig(
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
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=MyAgent,
        default_agent_config=MyAgentConfig(agent_id="interactive_agent")
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
# Run all tests (excluding cloud dependencies)
poetry run pytest -k "not azure"

# Run specific test file
poetry run pytest tests/test_my_agent.py

# Run with verbose output
poetry run pytest -v tests/

# Run with coverage
poetry run pytest --cov=aihub_agent tests/
```
