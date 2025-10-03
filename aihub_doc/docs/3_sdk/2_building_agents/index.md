---
title: Building agents
index: 2
---

# Building agents with the AI-Hub SDK

An agent in the Swiss AI-Hub is a workflow defined by a series of steps that process events. 
Agents can interact with users, call external services, and coordinate with other agents.

> [!NOTE]
> Complete the [development environment setup](../1_quick_start/1_dev_environment_setup/) and [your first agent](../1_quick_start/3_your_first_agent/) before starting.

## What's covered

1. [Agent fundamentals](./1_agent_fundamentals/) - Core architecture and concepts
2. [Core patterns](./2_core_patterns/) - Essential workflow patterns
3. [Human in the loop](./3_human_in_the_loop/) - Interactive workflows
4. [Multi-agent systems](./4_multi_agent_systems/) - Agent coordination
5. [Testing and debugging](./5_testing_and_debugging/) - Quality assurance
6. [Production deployment](./6_production_deployment/) - Going live
7. [Agent observation](./7_agent_observation/) - Monitoring and tracing

## Core concepts

### Agent class

Agents inherit from the `Agent` base class and define their workflow through steps:

```python
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step

class MyAgent(Agent):
    @step()
    async def process_input(self, event: UserMessageEvent) -> ProcessedEvent:
        return ProcessedEvent(result="processed")

    @step()
    async def generate_output(self, event: ProcessedEvent) -> StopEvent:
        return StopEvent(final_message=event.result)
```

### Event-driven workflow

Agents communicate through events:

::: details Event types
- **Control events** - Direct workflow execution (`StartEvent`, `StopEvent`)
- **Semantic events** - Carry domain-specific data
- **Display events** - Present information to users
:::

### @step decorator

Steps are functions decorated with `@step()` that consume one input event and return one output event:

```python
@step(
    max_executions_per_run=3,
    stop_on_error=True,
    name=LocaleString(en="Process Data"),
    description=LocaleString(en="Processes incoming data")
)
async def process_data(self, event: DataEvent) -> ProcessedEvent:
    return ProcessedEvent(data=event.data.upper())
```

### Configuration system

Agents use strongly-typed configuration:

```python
from aihub_lib.agents.AgentConfig import AgentConfig

from pydantic import Field
from typing import Annotated

class MyAgentConfig(AgentConfig):
    temperature: Annotated[float, Field(description="The LLM temperature")] = 0.7
    max_tokens: Annotated[int, Field(description="Max tokens for LLM")] = 512
    model_name: Annotated[str, Field(description="LLM model name")] = "gpt-4"
```

### Testing framework

Test agents with `AgentTestRunner`:

```python
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

async def test_my_agent():
    runner = AgentTestRunner(agent_type=MyAgent, agent_config=config)
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=test_event)
    assert runner.has_stop_event
```

## Development workflow

The typical flow for building an agent:

1. **Design** your agent's purpose and event flow
2. **Configure** with strongly-typed configuration classes
3. **Implement** steps that transform events
4. **Test** using `AgentTestRunner` for isolated testing
5. **Debug** with Phoenix tracing to monitor execution
6. **Deploy** by packaging and integrating with the platform

> [!TIP]
> Each agent should do one thing well. Agents can work as assistants, process components, or services for other agents.

## Next steps

Start with [agent fundamentals](./1_agent_fundamentals/) to understand the core architecture, then explore the specific patterns and techniques in the following sections.

