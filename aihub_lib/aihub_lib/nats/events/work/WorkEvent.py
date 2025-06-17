from typing import Annotated, ClassVar, Optional

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.process.ProcessEvent import ProcessEvent


class WorkEvent(ProcessEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.process_steps.work_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.process_steps.work_event.description"
    )

    display_name: Annotated[Optional[LocaleString], Field(description="Display name for the process step")] = None
    display_description: Annotated[
        Optional[LocaleString], Field(description="Display description for the process step")
    ] = None
