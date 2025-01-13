# AI-Hub Agents

`aihub_agent` contains **general-purpose AI agents** that follow predefined workflows. These agents are not
customer-specific and can utilize various tools, including large language models (LLMs), to perform their tasks. Each
agent is composed of multiple workflow steps, adhering to a well-defined process to achieve its objectives.

Agents in this repository are modular and workflow-driven. Each agent consists of:

- **Steps**: Discrete operations that the agent performs in sequence.
- **Events**: Signals used to trigger specific steps and define inputs/outputs.
- **Configurations**: Parameterized settings to control agent behavior.

---

## Developing New Agents - Guide

### Create a New Agent

To create a new agent:

1. Navigate to the `aihub_agent/aihub_agent/agents` directory.
    - For customer-specific agents, use the `agents` directory in the respective customer repository.
2. Create a new Python file named after your agent (e.g., `RAGAgent.py`).
3. Inherit from the `Agent` class or a specific base agent class.

Example:

```python
from aihub_agent.agents.abstract.Agent import Agent


class RAGAgent(Agent):
    pass
```

---

### Create an Agent Configuration

Agents require a configuration file to define their settings:

1. Create a Python file for your configuration (e.g., `RAGAgentConfig.py`).
2. Inherit from the `AgentConfig` class.

Example:

```python
from aihub_lib.generative_ai.agent.AgentConfig import AgentConfig


class RAGAgentConfig(AgentConfig):
    pass
```

---

### Define Start and Stop Methods

Each agent must include a **start step** (triggered by a `StartEvent`) and a **stop step** (producing a `StopEvent`).

- Use the `@step` decorator for these methods.
- Append `_step` to method names for clarity.

Example:

```python
from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import ControlEvent


class SomeEvent(ControlEvent):
    """ Example custom event. Move custom events to a separate file. """
    pass


class RAGAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> SomeEvent:
        return SomeEvent()

    @step()
    async def stop_step(self, event: SomeEvent) -> StopEvent:
        return StopEvent()
```

---

### Workflow Design

Design the agent's workflow by defining the sequence of steps it will execute:

1. Identify all the steps required to achieve the agent’s goal.
2. Use events to define the input and output of each step.
3. Start with a step taking a `StartEvent` as input and end with a step outputting a `StopEvent`..

Example Workflow:

1. Receive a `StartEvent` with chat history.
2. Limit the chat history to a specific token count.
3. Generate a response based on the chat history.
4. Send the response to the user.
5. Trigger a `StopEvent`.

---

### Implement Logic for Each Step

#### Define Custom Events

Custom events should usually inherit from `ControlEvent` and define specific attributes for the event.
There are other event types `DisplayEvent` and `SemanticEvent`. Generally you should not need to inherit
from `SemanticEvent` directly but use e.g. `LLMEvent` inherting from it.

Example:

```python
from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from typing import List


class LimitChatHistoryEvent(ControlEvent):
    limited_history: List[ChatMessage]
```

#### Use Helper Functions

Leverage helper functions from the `aihub_lib` for reusable logic.

Example:

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history


@step()
async def limit_chat_history_step(self, event: StartEvent) -> LimitChatHistoryEvent:
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=2048,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

#### Incorporate Configurations

Use configurations to parameterize agent behavior. Configurations can be passed:

1. **Directly in the `AgentConfig` class**.
2. **Via a separate step-specific configuration class**.

Example Using Step Configurations:

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_agent.workflow.decorators.step import step


class LimitChatHistoryStepConfig(StepConfig):
    number_of_input_tokens: int = Field(..., description="Max tokens for chat history")


class RAGAgentConfig(AgentConfig):
    limit_chat_history_step_config: LimitChatHistoryStepConfig


@step()
async def limit_chat_history_step(
        self,
        event: StartEvent,
        limit_chat_history_step_config: LimitChatHistoryStepConfig,
) -> LimitChatHistoryEvent:
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=limit_chat_history_step_config.number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

Or directly in the `AgentConfig` class:

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_agent.workflow.decorators.step import step


class RAGAgentConfig(AgentConfig):
    number_of_input_tokens: int = Field(..., description="Max tokens for chat history")


@step()
async def limit_chat_history_step(
        self,
        event: StartEvent,
        agent_config: RAGAgentConfig,
) -> LimitChatHistoryEvent:
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=agent_config.number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

---

### Testing the Agent

Agents can be tested using the **playground tool** (ensure Docker is running):

1. Load the agent in a controlled environment.
2. Simulate events and validate workflows.
3. Confirm that inputs and outputs align with expectations.

#### Using `AgentTestRunner`

The `AgentTestRunner` is designed to facilitate testing by providing a controlled environment to observe and verify
agent behavior. It captures events during test execution for validation. If used with `run_forever`, it can simulate
frontend-like scenarios where the agent continuously listens and responds. Alternatively, you can define specific events
and a limited runtime for isolated testing without a frontend.

Example:

```python
from aihub_lib.nats.events import StartEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    runner = AgentTestRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig(
            agent_id="rag_agent",
            name="RAG Agent",
            description="Agent for frontend development",
            system_prompt="You are an agent",
            # Additional configuration parameters...
        ),
    )

    # Example for limited runtime testing
    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(
                messages=[
                    ChatMessage(
                        content="You're an agent answering user requests. Only use the context information provided.",
                        role=MessageRole.SYSTEM,
                    ),
                    ChatMessage(content="Hey! What is AI?", role=MessageRole.USER),
                ]
            ),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

```

