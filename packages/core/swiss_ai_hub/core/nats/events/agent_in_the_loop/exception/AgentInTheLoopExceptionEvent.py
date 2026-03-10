from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.control.exception.ExceptionEvent import ExceptionEvent
from swiss_ai_hub.core.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class AgentInTheLoopExceptionEvent(ControlAndDisplayEvent):
    """
    An error response from an agent when a delegated task fails.

    ### Why AgentInTheLoopExceptionEvent?
    When an agent encounters an error during a delegated task, this event:
    - Signals workflow disruption (since it's a `ControlEvent`), allowing error handling in the original agent
    - Is visible to the UI (since it's also a `DisplayEvent`), enabling monitoring and debugging of agent failures
    - Provides a dedicated error channel separate from successful responses
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.aitl_exception_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.aitl_exception_event.description"
    )

    exception_event: Annotated[
        ExceptionEvent,
        Field(description="The exception event from the delegated agent containing error details and failure context."),
    ]
