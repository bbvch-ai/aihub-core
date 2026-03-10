---
title: Human in the loop
---

# Human in the Loop

The **Human in the Loop (HITL)** pattern allows an agent to pause its execution at a critical point and request input,
approval, or guidance from a human user before continuing.

## How it works

The HITL pattern is orchestrated by a pair of events that manage the pause and resume logic:

1. **Request**: A step in your agent returns a `HumanInTheLoop.request` event. This is a special `ControlEvent` that
   also acts as a `DisplayEvent`, pausing the workflow and presenting a question to the user in the UI.
2. **Response**: The user's answer is sent back to the system as a `HumanInTheLoop.response` event.
3. **Resume**: Another step in your agent is configured to accept this response event. When the event arrives, the
   dispatcher routes it to the correct step, and the workflow resumes its execution.

The `HumanInTheLoop` helper class simplifies this process by providing a convenient `invoke` method to create the
request event with the correct routing information.

## Three HITL types

The framework provides three interaction types, each rendered differently in the UI:

| Type             | Class                        | UI behavior                                                     | Response type |
| ---------------- | ---------------------------- | --------------------------------------------------------------- | ------------- |
| **Input**        | `HumanInTheLoopInput`        | Popup dialog for free-form text entry                           | `str`         |
| **Confirmation** | `HumanInTheLoopConfirmation` | Yes/No button selection                                         | `bool`        |
| **Chat**         | `HumanInTheLoopChat`         | Message in chat stream (fallback for UIs without popup support) | `str`         |

```python
from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopInput,
    HumanInTheLoopConfirmation,
    HumanInTheLoopChat,
)

# Popup with text input field
HumanInTheLoopInput.invoke(question="What is your preferred language?")

# Yes/No buttons
HumanInTheLoopConfirmation.invoke(question="Approve this transaction?")

# Chat message (no special UI treatment)
HumanInTheLoopChat.invoke(question="Please provide additional context.")
```

### Type selection guide

| Use case                | Type                         | Example                                      |
| ----------------------- | ---------------------------- | -------------------------------------------- |
| Free-form user input    | `HumanInTheLoopInput`        | "Enter search query:", "Describe the issue:" |
| Binary decision         | `HumanInTheLoopConfirmation` | "Delete this file?", "Proceed with payment?" |
| Conversational fallback | `HumanInTheLoopChat`         | APIs or UIs without popup support            |

## Core pattern: single approval

This example shows a simple workflow where the agent asks for a single confirmation before proceeding.

**Reference**: `playground/minimal_workflow/human_in_the_loop_workflow/`

```python
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput

class ApprovalAgent(Agent):
    @step()
    async def request_approval(self, event: StartEvent) -> HumanInTheLoopInput.request:
        return HumanInTheLoopInput.invoke(question="Please enter your feedback:")

    @step()
    async def handle_response(self, event: HumanInTheLoopInput.response) -> StopEvent:
        user_response = event.response
        return StopEvent()
```

## Multi-step approval with custom event pairs

For workflows requiring multiple human interactions, create distinct subclasses. The dispatcher differentiates steps by
event type — using the same base type for multiple interactions causes ambiguity.

**Reference**: `playground/minimal_workflow/multistep_human_in_the_loop_workflow/`

### Step 1: Define custom HITL event pairs

Each HITL interaction point needs its own request/response event pair and a wrapper class:

::: code-group
```python [events/FirstStepHumanInTheLoop.py]
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class FirstStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class FirstStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class FirstStepHumanInTheLoop(HumanInTheLoopInput):
    request = FirstStepHumanInTheLoopRequestEvent
    response = FirstStepHumanInTheLoopResponseEvent
```

```python [events/SecondStepHumanInTheLoop.py]
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopInputRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopInputResponseEvent


class SecondStepHumanInTheLoopRequestEvent(HumanInTheLoopInputRequestEvent):
    pass


class SecondStepHumanInTheLoopResponseEvent(HumanInTheLoopInputResponseEvent):
    pass


class SecondStepHumanInTheLoop(HumanInTheLoopInput):
    request = SecondStepHumanInTheLoopRequestEvent
    response = SecondStepHumanInTheLoopResponseEvent
```
:::

### Step 2: Use distinct types in the workflow

```python
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step

from .events.FirstStepHumanInTheLoop import FirstStepHumanInTheLoop
from .events.SecondStepHumanInTheLoop import SecondStepHumanInTheLoop


class MultistepHumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def second_hitl(
        self, event: FirstStepHumanInTheLoop.response
    ) -> SecondStepHumanInTheLoop.request:
        print(f"First response: {event.response}")
        return SecondStepHumanInTheLoop.invoke(question="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print(f"Second response: {event.response}")
        return StopEvent()
```

## Dynamic HITL type selection

When the HITL type depends on runtime conditions, use union return types:

```python
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopChat,
    HumanInTheLoopConfirmation,
    HumanInTheLoopInput,
)

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class HitlDemoAgent(Agent):
    @step()
    async def select_hitl_type(
        self, event: UserMessageEvent
    ) -> HumanInTheLoopInput.request | HumanInTheLoopConfirmation.request | HumanInTheLoopChat.request:
        choice = event.user_query.lower()

        if "confirmation" in choice:
            return HumanInTheLoopConfirmation.invoke("Do you confirm this action?")
        elif "chat" in choice:
            return HumanInTheLoopChat.invoke("This is a chat-style question. What is your response?")
        else:
            return HumanInTheLoopInput.invoke("Please enter your text input:")

    @step()
    async def handle_response(
        self,
        event: HumanInTheLoopInput.response | HumanInTheLoopConfirmation.response | HumanInTheLoopChat.response,
    ) -> StopEvent:
        if isinstance(event, HumanInTheLoopConfirmation.response):
            result = f"Confirmation: {'Yes' if event.response else 'No'}"
        else:
            result = f"Response: {event.response}"
        return StopEvent()
```

## Bot-in-the-Loop (Teams/Slack integration)

Bot-in-the-Loop (BITL) enables workflows to interact with external messaging platforms via the Azure Bot Framework.
Unlike HITL (which prompts users within the agent UI), BITL sends messages to Microsoft Teams channels or Slack channels
and awaits responses from users on those platforms.

### Channel configuration

BITL requires platform-specific configuration:

::: code-group
```python [Microsoft Teams]
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig

teams_config = TeamsConfig(
    channel_id="19:abc123@thread.tacv2",  # Teams channel ID
    tenant_id="12345678-1234-1234-1234-123456789abc",  # Azure AD tenant ID
    bot_id="87654321-4321-4321-4321-cba987654321",  # Bot UUID
)
```

```python [Slack]
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig

slack_config = SlackConfig(
    channel_id="C0123456789",  # Slack channel ID (starts with 'C')
    service_url="https://slack.botframework.com",
)
```
:::

### Basic usage

```python
from aihub_lib.nats.events import StopEvent
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class BotInTheLoopAgent(Agent):
    @step()
    async def request_approval(
        self, start_event: MyStartEvent
    ) -> BotInTheLoop.request:
        return BotInTheLoop.invoke(
            user=start_event.user,
            question="Should the agent proceed with the deployment?",
            channel_config=start_event.channel_config,  # TeamsConfig or SlackConfig
        )

    @step()
    async def handle_response(self, event: BotInTheLoop.response) -> StopEvent:
        answer = event.response

        if event.responder:
            print(f"Answered by: {event.responder.user_name} ({event.responder.user_id})")
            if event.responder.aad_object_id:  # Teams-specific
                print(f"AAD Object ID: {event.responder.aad_object_id}")

        return StopEvent()
```

### Iterative conversations

BITL supports multi-turn conversations by returning another `BotInTheLoop.request`:

```python
@step()
async def handle_response(
    self, event: BotInTheLoop.response
) -> BotInTheLoop.request | StopEvent:
    if event.response.lower() == "yes":
        return StopEvent()
    else:
        return BotInTheLoop.invoke(
            user=event.request_event.user,
            question="What about now? Ready to proceed?",
            channel_config=event.request_event.channel_config,
        )
```

### Response event structure

The `BotInTheLoop.response` event provides:

| Field           | Type                        | Description                    |
| --------------- | --------------------------- | ------------------------------ |
| `response`      | `str`                       | The user's message text        |
| `request_event` | `BotInTheLoopRequestEvent`  | Original request (for context) |
| `responder`     | `BotInTheLoopResponderInfo` | Who responded                  |

**Responder information:**

| Field             | Type           | Description                     |
| ----------------- | -------------- | ------------------------------- |
| `user_id`         | `str`          | Platform user ID (Slack/Teams)  |
| `user_name`       | `str`          | Display name                    |
| `additional_info` | `dict \| None` | Platform-specific metadata      |
| `aad_object_id`   | `str \| None`  | Azure AD object ID (Teams only) |

### BITL vs HITL

| Aspect                | HumanInTheLoop            | BotInTheLoop                                   |
| --------------------- | ------------------------- | ---------------------------------------------- |
| **Platform**          | Agent UI (web/mobile)     | Teams / Slack                                  |
| **User context**      | Same session user         | External channel users                         |
| **UI options**        | Input, Confirmation, Chat | Text message only                              |
| **Response tracking** | Implicit (same user)      | Explicit (`responder` field)                   |
| **Use case**          | In-app approvals          | Cross-platform notifications, team escalations |
