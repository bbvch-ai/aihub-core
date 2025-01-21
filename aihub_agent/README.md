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

<details>
<summary>Example</summary>

```python
from aihub_agent.agents.abstract.Agent import Agent


class RAGAgent(Agent):
    pass
```

</details>

---

### Create an Agent Configuration

Agents require a configuration file to define their settings:

1. Create a Python file for your configuration (e.g., `RAGAgentConfig.py`).
2. Inherit from the `AgentConfig` class.
3. **Use `Field` with meaningful `description`** entries.

<details>
<summary>Example</summary>

```python
from aihub_agent.agents.AgentConfig import AgentConfig
from pydantic import Field


class RAGAgentConfig(AgentConfig):
    number_of_input_tokens: int = Field(
        ...,
        description="Limits the length of the conversation history to reduce costs or prevent context overflow."
    )
```

</details>

---

### Define Start and Stop Methods

Each agent must include a **start step** (triggered by a `StartEvent`) and a **stop step** (producing a `StopEvent`).

- Use the `@step` decorator for these methods.
- Append `_step` to method names for clarity.
- Include docstrings explaining what the step **achieves**.

<details>
<summary>Example</summary>

```python
from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import ControlEvent


class SomeEvent(ControlEvent):
    """
    Example custom event
    """
    pass


class RAGAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> SomeEvent:
        return SomeEvent()

    @step()
    async def stop_step(self, event: SomeEvent) -> StopEvent:
        return StopEvent()
```

</details>

---

### Workflow Design

Design the agent's workflow by defining the sequence of steps it will execute:

1. Identify all the steps required to achieve the agent’s goal.
2. Use events to define the input and output of each step.
3. Start with a step taking a `StartEvent` as input and end with a step outputting a `StopEvent`.

<details>
<summary>Example Workflow</summary>

1. Receive a `StartEvent` with chat history.
2. Limit the chat history to a specific token count.
3. Generate a response based on the chat history.
4. Send the response to the user.
5. Trigger a `StopEvent`.

</details>

---

### Implement Logic for Each Step

#### Define Custom Events

Define custom events (or use general events) to flow between steps, create **Pydantic-based events** with docstrings
that
explain their purpose. Inherit from `ControlEvent`, or use specialized events like `LLMEvent` (avoid inheriting directly
from `SemanticEvent`).

<details>
<summary>Example</summary>

```python
from aihub_lib.nats.events import ControlEvent
from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from typing import List


class LimitChatHistoryEvent(ControlEvent):
    """
    Represents the result of limiting a user's chat history to a specified 
    number of tokens to optimize cost and context usage.
    """
    limited_history: List[ChatMessage] = Field(
        ...,
        description="A trimmed list of messages that fit within the token limit."
    )
```

</details>

#### Use Helper Functions

Leverage helper functions from the `aihub_lib` for reusable logic and keep step docstrings brief yet informative.

<details>
<summary>Example</summary>

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events.control.start import StartEvent


@step()
async def limit_chat_history_step(self, event: StartEvent) -> LimitChatHistoryEvent:
    """
    Reduces the chat history to a predefined token limit.
    """
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=2048,  # Example value; could be from config
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

</details>

#### Incorporate Configs

Use configurations to parameterize agent behavior. This can be done via dedicated step configuration objects or directly
via the main `AgentConfig`. Always give your Pydantic fields **valuable** descriptions.

<details>
<summary>Example Using Step Configurations</summary>

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_agent.workflow.decorators.step import step
from aihub_agent.agents.AgentConfig import AgentConfig, StepConfig
from pydantic import Field


class LimitChatHistoryStepConfig(StepConfig):
    """
    Configuration for the limit_chat_history_step,
    specifying how many tokens to allow in the conversation.
    """
    number_of_input_tokens: int = Field(
        ...,
        description="Specifies the maximum number of tokens permitted in the chat history."
    )


class RAGAgentConfig(AgentConfig):
    limit_chat_history_step_config: LimitChatHistoryStepConfig


@step()
async def limit_chat_history_step(
        self,
        event: StartEvent,
        limit_chat_history_step_config: LimitChatHistoryStepConfig,
) -> LimitChatHistoryEvent:
    """
    Reduces the chat history to a token limit defined in the step config.
    """
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=limit_chat_history_step_config.number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

</details>

<details>
<summary>Or directly in the <code>AgentConfig</code> class</summary>

```python
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_agent.workflow.decorators.step import step


class RAGAgentConfig(AgentConfig):
    number_of_input_tokens: int = Field(
        ...,
        description="Sets the maximum chat history token length to reduce costs or prevent overflow."
    )


@step()
async def limit_chat_history_step(
        self,
        event: StartEvent,
        agent_config: RAGAgentConfig,
) -> LimitChatHistoryEvent:
    """
    Reduces the chat history to a token limit specified in the agent configuration.
    """
    limited_chat_history = limit_chat_history(
        chat_history=event.messages,
        number_of_input_tokens=agent_config.number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=limited_chat_history)
```

</details>

---

### Testing the Agent

Agents can be tested using the **playground tool** (ensure Docker is running):

1. Load the agent in a controlled environment.
2. Simulate events and validate workflows.
3. Confirm that inputs and outputs align with expectations.

---

#### Using `AgentTestRunner`

- The `AgentTestRunner` provides a controlled test environment.
- Capture events to ensure the agent behaves as expected.
- To test a production-like scenario with the frontend:
    - Create a `run.py` file.
    - Use `run_forever` to keep the agent running.
- To test a limited runtime scenario:
    - Create a `trigger.py` file.
    - Use `test_run` with a specified delay before stopping.
- Leverage Phoenix (localhost:6006) to view traces of each step.

<details>
<summary>Example </summary>

`trigger.py`:

```python
from aihub_lib.nats.events.control.start import StartEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from llama_index.core.base.llms.types import ChatMessage, MessageRole


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

</details>

---

#### Wrting tests with `pytest-bdd`

Agents (and their supporting utility functions) can be tested at two levels using **BDD**:

##### 1. Unit-Like BDD Tests (Helper Functions or Single Steps)

A simplified BDD approach to testing **individual functions** (e.g., helper functions or single steps).  
We want to write a BDD test for a single function or step in isolation.

<details>
<summary>Example</summary> 

`.feature` file: `limit_chat_history.feature`

```gherkin
Feature: limit_chat_history Utility Function
  Tests the limit_chat_history function in isolation.

  Scenario: Limit chat history to 2 messages
    Given a list of 3 chat messages
    When limit_chat_history is called with max tokens that only allow for 2 messages
    Then only 2 messages remain
```

In your `test_limit_chat_history.py`, you might have:

```python
import pytest
from pytest_bdd import scenarios, given, when, then
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history

scenarios("./features/limit_chat_history.feature")


@pytest.fixture
def messages():
    return [
        ChatMessage(content="Message 1", role=MessageRole.USER, token_length=100),
        ChatMessage(content="Message 2", role=MessageRole.USER, token_length=100),
        ChatMessage(content="Message 3", role=MessageRole.USER, token_length=100),
    ]


@given("a list of 3 chat messages", target_fixture="chat_messages")
def _(messages):
    return messages


@when("limit_chat_history is called with max tokens that only allow for 2 messages", target_fixture="result")
def _(chat_messages):
    # Suppose each message is roughly 100 tokens, so we allow for 200 tokens total
    return limit_chat_history(chat_messages, number_of_input_tokens=200)


@then("only 2 messages remain")
def _(result):
    assert len(result) == 2, f"Expected 2 messages, got {len(result)}"
```

</details>
---

##### 2. Full Agent BDD Tests

Validating the **complete workflow** of the agent from start to stop.
We want to write a BDD test for the full workflow of the agent, from start to stop.

<details>
<summary>Example</summary>

**`.feature` file: `simple_agent.feature`**

```gherkin
Feature: Simple Agent
  A minimal agent workflow demonstrating start and stop steps.

  Scenario: Send a user query and receive a simple response
    Given a SimpleAgent runner with a basic configuration
    When the start event is sent with a user query "Hello world"
    Then a StartEvent is present with payload "Hello world"
    And a StopEvent is present
```

**Test file: `test_simple_agent.py`**

```python
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from aihub_lib.nats.events.control.start import StartEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from .simple_agent import SimpleAgent, SimpleAgentConfig  # Example imports

scenarios("./features/simple_agent.feature")


@given("a SimpleAgent runner with a basic configuration", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name="Simple Agent",
            description="A minimal agent demo",
        ),
    )


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@pytest.mark.asyncio
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=5) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content=query, role=MessageRole.USER)])
        )


@then(parsers.parse('a StartEvent is present with payload "{payload}"'))
def _(agent_runner: AgentTestRunner, payload: str):
    assert agent_runner.has_start_event, "Agent did not receive a StartEvent"
    start_event = agent_runner.get_start_event
    assert start_event.messages[0].content == payload, f"Expected {payload}, got {start_event.messages[0].content}"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce a StopEvent"
```

Here’s what’s happening:

1. **`@given`** sets up a `SimpleAgent` with a minimal config.
2. **`@when`** sends a `StartEvent` with the query `"Hello world"`.
3. **`@then`** checks that a `StartEvent` with the correct payload was received and that the agent produced a
   `StopEvent`.

</details>

---

## Documentation Guidelines

### 1. Docstrings for Agents

- **What**: Provide a docstring at the class level describing what the agent does and when it is used.
- **Why**: Helps future developers quickly grasp the agent’s purpose, usage scenarios, and workflow overview.
- **How**: For agents with special start or stop events, consider adding a small coding example illustrating usage.

<details>
<summary>Example</summary>

```python
class PersonaAgent(Agent):
    """
    Imitates a given persona by fetching similar personas from a knowledge base 
    and responding in a style consistent with that persona.

    This agent is used when a user wants to chat with a particular persona. 
    The workflow typically includes:
    1. Fetching similar personas from an index.
    2. Generating a persona-consistent response.
    3. Returning the response to the user.

    Example:
        >>> # Code usage example
        >>> ... 
    """
    pass
```

</details>

---

### 2. Docstrings for Steps

- **What**: Provide a simple docstring for each step method explaining what the step **achieves** (its purpose).
- **Why**: Keeps step-level logic understandable without overexposing implementation details.

<details>
<summary>Example</summary>

```python
@step()
async def retrieve_documents_step(self, event: SomeEvent) -> RetrieveEvent:
    """
    Retrieves documents similar to the user query from the vector database.
    """
    # Step logic ...
    return RetrieveEvent(documents=similar_docs)
```

</details>

---

### 3. Docstrings and Field Descriptions for Pydantic Objects

1. **Fields**: Always provide a meaningful `description` that adds value. Avoid trivial descriptions like
   `"Number of input tokens"` if you can provide more context, e.g.
   `"Limits the length of the conversation history to reduce costs or prevent context overflow."`

2. **Class-Level Docstring**: For non-trivial classes, add a docstring that explains:
    - **Why** this Pydantic model exists (its purpose).
    - **How** it can be used within the agent or events workflow.

<details>
<summary>Examples</summary>

```python
from pydantic import BaseModel, Field
from typing import List


class RetrieveEvent(BaseModel):
    """
    Represents a set of documents that were retrieved from a vector database 
    because they were most similar to a given query. This event should be used 
    whenever the agent needs to pass relevant documents down the workflow 
    (e.g., for summarizing or for further analysis).
    """
    documents: List[str] = Field(
        ...,
        description="List of retrieved documents ranked by similarity."
    )
```

```python
class RAGAgentConfig(AgentConfig):
    """
    Configuration for the Retrieval-Augmented Generation (RAG) Agent.

    This configuration controls how many tokens to allow in the conversation 
    history, as well as other RAG-specific parameters like number of retrieved 
    documents or the vector index to query.
    """
    number_of_input_tokens: int = Field(
        ...,
        description="Limits the length of the conversation history to reduce costs or prevent context overflow."
    )
    max_retrieved_docs: int = Field(
        5,
        description="Defines how many documents should be retrieved for context augmentation."
    )
```

</details>
