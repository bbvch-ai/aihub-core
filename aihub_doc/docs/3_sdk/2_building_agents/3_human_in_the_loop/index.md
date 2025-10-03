---
title: Human in the loop
index: 3
---

# Human in the loop

Agents can pause execution and request human input before continuing. This pattern works well for approval workflows, decision points, and maintaining human oversight.

## Core pattern

Two events connected by a helper class:

```python
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

class MyAgent(Agent):
    @step()
    async def request_approval(self, event: UserMessageEvent) -> HumanInTheLoop.request:
        return HumanInTheLoop.invoke(question="Should I proceed with this action?")

    @step()
    async def handle_response(self, event: HumanInTheLoop.response) -> StopEvent:
        if event.response.lower() == "yes":
            return StopEvent(final_message="Action approved and executed")
        return StopEvent(final_message="Action cancelled")
```

**Reference**: `playground/minimal_workflow/human_in_the_loop_workflow/`

The HumanInTheLoop class provides a convenient `invoke` method to create a `HumanInTheLoopRequestEvent`.


## When to use

::: details Use cases
- **High-risk operations** - Data deletion, financial transactions
- **Quality control** - Content review, output validation
- **Decision points** - Strategy selection, parameter configuration
- **Approval workflows** - Process gates, compliance checks
- **Ambiguous situations** - When AI confidence is low
:::

## Best practices

> [!TIP]
> Make questions specific and actionable. Include relevant context for decision-making.

- Use options to limit choices when possible
- Handle timeouts gracefully for time-sensitive operations
- Test different human responses in your test suite
- Provide enough context for humans to make informed decisions

The pattern maintains human control while leveraging agent automation.