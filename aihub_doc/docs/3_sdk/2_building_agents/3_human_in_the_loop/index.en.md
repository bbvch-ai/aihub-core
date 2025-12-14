---
title: Human in the loop
---

# Human in the Loop

The **Human in the Loop (HITL)** pattern allows an agent to pause its execution at a critical point and request input,
approval, or guidance from a human user before continuing.

## How It Works

The HITL pattern is orchestrated by a pair of events that manage the pause and resume logic:

1. **Request**: A step in your agent returns a `HumanInTheLoop.request` event. This is a special `ControlEvent` that
   also acts as a `DisplayEvent`, pausing the workflow and presenting a question to the user in the UI.
2. **Response**: The user's answer is sent back to the system as a `HumanInTheLoop.response` event.
3. **Resume**: Another step in your agent is configured to accept this response event. When the event arrives, the
   dispatcher routes it to the correct step, and the workflow resumes its execution.

The `HumanInTheLoop` helper class simplifies this process by providing a convenient `invoke` method to create the
request event with the correct routing information.

## Core Pattern: Single Approval

This example shows a simple workflow where the agent asks for a single confirmation before proceeding.

**Reference**: `playground/minimal_workflow/human_in_the_loop_workflow/`

```python
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

class ApprovalAgent(Agent):
    @step()
    async def request_approval(self, event: StartEvent) -> HumanInTheLoop.request:
        # 1. Pause the workflow and ask a question.
        return HumanInTheLoop.invoke(message="Should I proceed with this action?")

    @step()
    async def handle_response(self, event: HumanInTheLoop.response) -> StopEvent:
        # 2. Resume the workflow based on the human's response.
        if event.response.lower() == "yes":
            return StopEvent(final_message="Action approved and executed.")
        return StopEvent(final_message="Action cancelled by user.")
```

## Advanced Pattern: Multi-Step Approval

You can chain multiple HITL steps together to create more complex, multi-stage approval or data-gathering workflows.

**Reference**: `playground/minimal_workflow/multistep_human_in_the_loop_workflow/`

```python
class MultistepApprovalAgent(Agent):
    @step()
    async def request_initial_approval(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        # First checkpoint
        return FirstStepHumanInTheLoop.invoke(message="Shall I continue?")

    @step()
    async def request_final_confirmation(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
        # Second checkpoint, only reached after the first is approved
        if event.response.lower() == "yes":
            return SecondStepHumanInTheLoop.invoke(message="Are you absolutely sure?")
        return StopEvent(final_message="Process cancelled at first step.")

    @step()
    async def execute_action(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        # Final step, only reached after the second confirmation
        if event.response.lower() == "yes":
            return StopEvent(final_message="Action confirmed and executed.")
        return StopEvent(final_message="Process cancelled at final confirmation.")
```
