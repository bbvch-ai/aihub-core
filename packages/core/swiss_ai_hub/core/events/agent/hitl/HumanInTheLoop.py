from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopChat import HumanInTheLoopChat
from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopConfirmation import HumanInTheLoopConfirmation
from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopResponseEvent,
)


class HumanInTheLoop:
    """
    A helper for triggering human-in-the-loop (HITL) steps within a workflow.

    Use the specific helpers for type-safe interactions:
    - `HumanInTheLoop.input` for free-form text input (popup dialog)
    - `HumanInTheLoop.confirmation` for yes/no confirmation (popup dialog)
    - `HumanInTheLoop.chat` for chat-style input (appears as regular message)

    Or use the base classes directly via `request` and `response` attributes.
    """

    request = HumanInTheLoopRequestEvent
    response = HumanInTheLoopResponseEvent

    # Typed helpers
    input = HumanInTheLoopInput
    confirmation = HumanInTheLoopConfirmation
    chat = HumanInTheLoopChat
