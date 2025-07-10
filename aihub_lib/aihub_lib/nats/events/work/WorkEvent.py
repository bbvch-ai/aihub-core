from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class WorkEvent(ProcessEvent):
    """
    A work event signals that a piece of work was successfully completed by some entity involved in the process.
    You should generally never inherit from this class directly but use a more specific child class such as
    AgentWorkEvent, HumanWorkEvent, ... etc. instead.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.process_steps.work_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.process_steps.work_event.description"
    )

    display_name: Annotated[LocaleString | None, Field(description="Display name for the process step")] = None
    display_description: Annotated[
        LocaleString | None, Field(description="Display description for the process step")
    ] = None
