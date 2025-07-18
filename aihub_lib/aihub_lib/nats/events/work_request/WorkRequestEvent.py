from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class WorkRequestEvent(ProcessEvent):
    """
    A work request event signals that a process steps wants to delegate a piece of work to some entity involved in the
    process.
    You should generally never inherit from this class directly but use a more specific child class such as
    AgentWorkRequestEvent, HumanWorkRequestEvent, ... etc. instead.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.process_steps.work_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.process_steps.work_request_event.description"
    )

    display_name: Annotated[LocaleString | None, Field(description="Display name for the process step")] = None
    display_description: Annotated[LocaleString | None, Field(description="Display description for the event")] = None
