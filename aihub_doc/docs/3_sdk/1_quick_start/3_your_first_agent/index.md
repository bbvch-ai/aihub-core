---
title: Your First Agent
index: 3
---

# Your First Agent

Build your first agent using the AI-Hub Agent (`aihub_agent`) SDK - a simple message processing agent with a 2-step
workflow.

## What you'll learn

This quickstart covers the essential building blocks:

- **Agent structure**: How agents process messages in steps
- **Event flow**: Data flowing between workflow steps
- **Configuration**: Settings that control agent behavior
- **Testing**: Running your agent locally

## Prerequisites

You need the AI-Hub development environment running. Before you start, make sure you completed the
[Development Environment Setup](/3_sdk/1_quick_start/1_dev_environment_setup/) steps.

## How agents work

AI-Hub agents are **event-driven workflows** with three essential parts:

- **Steps**: Functions decorated with `@step()` that process events
- **Events**: Data objects flowing between steps
- **Configuration**: Typed settings that control agent behavior

## Create your first agent

Let's build a simple message processor that takes a user message, processes it in two steps, and returns a response.

### 1. Create a Custom Event (`MessageEvent.py`):

First, create an event to pass data between steps:

```python
from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class MyAgentEvent(ControlEvent):
    word_count: Annotated[int, Field(description="The word count of the processed content")]

```

### 2. Agent Configuration (`MyAgentConfig.py`):

```python
from typing import Annotated
from pydantic import Field
from aihub_lib.agents.AgentConfig import AgentConfig

class MyAgentConfig(AgentConfig):
    prefix: Annotated[str, Field(
        default="Processed:",
        description="Prefix to add to processed messages"
    )]
```

### 3. Agent Implementation (`MyAgent.py`):

```python
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step

from MyAgentEvent import MyAgentEvent
from MyAgentConfig import MyAgentConfig

class MyAgent(Agent):
    
    @step()
    async def process_message(self, event: UserMessageEvent) -> MyAgentEvent:
        """First step: Process the incoming message."""
        content = event.messages[-1].content
        word_count = len(content.split())
        print(f"[Step 1] Processing message: '{content}'")
        return MyAgentEvent(word_count=word_count)
    
    @step()
    async def create_response(
        self, 
        event: MyAgentEvent, 
        config: MyAgentConfig
    ) -> StopEvent:
        """Second step: Create final response with configuration."""
        response = f"{config.prefix} (Words: {event.word_count})"
        print(f"[Step 2] Creating response: '{response}'")
        return StopEvent()
```

### 4. Test Script (`trigger.py`):

```python
import asyncio
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from MyAgent import MyAgent
from MyAgentConfig import MyAgentConfig

# Enable detailed logging to see event flow
enable_logging()

async def main():
    # Configure the agent
    config = MyAgentConfig(
        agent_id="my_agent",
        name=LocaleString(en="My First Agent"),
        description=LocaleString(en="A simple message processing agent"),
        prefix="Processed:"
    )
    
    # Create test runner
    runner = AgentTestRunner(agent_type=MyAgent, default_agent_config=config)
    
    # Run the agent with a test message
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(
                    content="Hello world this is my first agent",
                    role=MessageRole.USER
                )],
                user=fake_user()
            )
        )
    
    print(f"Agent completed: {runner.has_stop_event}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Run and debug your agent

1. **Run the test script**:

```bash
python trigger.py
```

Expected output:

```
[Step 1] Processing message: 'Hello world this is my first agent' -> 'HELLO WORLD THIS IS MY FIRST AGENT'
[Step 2] Creating response: 'Processed: HELLO WORLD THIS IS MY FIRST AGENT (Words: 7)'
Agent completed: True
```

2. **Debug with Phoenix Tracing** - Open `http://localhost:6006` to see:

   - Step-by-step execution flow
   - Event data flowing between steps
   - Timing and performance metrics
   - Event payload details

3. **Check the logs** - The `enable_logging()` call shows real-time event flow and helps debug issues.

## Understanding the workflow

Your agent follows this event flow:

1. **UserMessageEvent** → `process_message()` → **MessageEvent**
2. **MessageEvent** → `create_response()` → **StopEvent**

Each step:

- Receives an event as input
- Processes the data
- Returns a new event
- The workflow engine routes events to the next step

## What you learned

- **Event-driven workflows**: Steps process events and produce new events
- **Custom events**: Creating typed data objects to pass between steps
- **Configuration**: Using typed settings to control agent behavior
- **Testing**: Use `AgentTestRunner` for isolated testing
- **Debugging**: Phoenix tracing and logging for observability

## Next steps

- [Your First Pipeline](/3_sdk/1_quick_start/4_your_first_pipeline/) -
- [Building Agents](/3_sdk/2_building_agents/) - Learn more advanced agent patterns
