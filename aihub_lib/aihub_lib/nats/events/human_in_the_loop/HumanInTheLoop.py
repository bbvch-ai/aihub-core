from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoopChat import HumanInTheLoopChat
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoopConfirmation import HumanInTheLoopConfirmation
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoopInput import HumanInTheLoopInput
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopRequestEvent
from aihub_lib.nats.events.human_in_the_loop.response import HumanInTheLoopResponseEvent


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
