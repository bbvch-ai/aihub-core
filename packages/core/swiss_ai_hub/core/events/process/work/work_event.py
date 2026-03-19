from typing import Annotated, ClassVar, Self

from pydantic import Field, model_validator

from swiss_ai_hub.core.events.process.process_event import ProcessEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class WorkEvent(ProcessEvent):
    """
    A work event signals that a piece of work was successfully completed by some entity involved in the process.
    You should generally never inherit from this class directly but use a more specific child class such as
    AgentWorkEvent, HumanWorkEvent, ... etc. instead.
    Work events are the driving forces of an agentic process: By submitting a work event, an entity signals
    that it has completed a step in the workflow and the process dispatcher will drive the process
    to the appropriate next step(s).
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.process_steps.work_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.process_steps.work_event.description"
    )

    display_name: Annotated[LocaleString | None, Field(description="Display name for the process step")] = None
    display_description: Annotated[
        LocaleString | None, Field(description="Display description for the process step")
    ] = None

    in_response_to: Annotated[
        str | None, Field(description="The ID of the work event that this event is in response to")
    ] = None

    @model_validator(mode="after")
    def set_default_values(self) -> Self:
        """Set default values from class if instance values are None."""
        if not self.display_name:
            self.display_name = self.__class__._display_name
        if not self.display_description:
            self.display_description = self.__class__._display_description
        return self

    @classmethod
    def display_name_from_class(cls) -> LocaleString:
        return cls._display_name

    @classmethod
    def display_description_from_class(cls) -> LocaleString:
        return cls._display_description
