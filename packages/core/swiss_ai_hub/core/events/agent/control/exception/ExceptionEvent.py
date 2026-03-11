from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.SemanticEvent import SemanticEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class ExceptionEvent(SemanticEvent):
    """
    An event signaling that an exception or error has occurred during a run.

    ### Why ExceptionEvent?
    In a complex, event-driven workflow, errors are inevitable. Some steps might fail due to
    invalid inputs, external service outages, or internal logic errors. The `ExceptionEvent`
    provides a unified way to:
    - Halt or adjust the workflow’s control flow as a `ControlEvent`.
    - Communicate the error details to end-users or logging systems as a `DisplayEvent`.

    By appearing as both a control and display event, `ExceptionEvent` ensures that the workflow
    can stop further processing while also making the error visible in UI dashboards, logs, or
    monitoring tools - giving operators and developers immediate insight into what went wrong.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.exception_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.exception_event.description")

    message: Annotated[str, Field(description="A human-readable description of the exception or error that occurred.")]
    http_status_code: Annotated[
        int,
        Field(
            description="HTTP status code associated with the exception. Defaults to 500 (Internal Server Error).",
        ),
    ] = 500

    def to_semantic_convention(self) -> dict[str, str]:
        return {
            "exception.type": self.http_status_code,
            "exception.message": self.message,
        }
