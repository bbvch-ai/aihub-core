from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_chat import HumanInTheLoopChat
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_confirmation import HumanInTheLoopConfirmation
from swiss_ai_hub.core.events.agent.hitl.human_in_the_loop_input import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
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
