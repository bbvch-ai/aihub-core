from typing import Annotated, ClassVar, Self

from pydantic import Field, model_validator

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.BaseEvent import BaseEvent


class DisplayEvent(BaseEvent):
    """
    Represents a user-facing event that can be shown to end-users, UIs, or monitoring dashboards.
    Display events are purely informational and never affect the control flow or execution order
    of workflows.

    ### Why DisplayEvent?
    While `ControlEvent` influences the system’s decision-making and progression, `DisplayEvent`
    focuses on communicating results, status updates, and other information intended for human
    consumption or passive observation. This separation ensures that even if a display event fails
    to reach a UI, it doesn’t alter the underlying workflow logic or state transitions.

    By subclassing `BaseEvent`, `DisplayEvent` remains fully compatible with the automatic
    registration, serialization, and deserialization mechanisms, making it simple to integrate
    into a user interface or logging pipeline.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.display_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.display_event.description")

    display_name: Annotated[LocaleString | None, Field(description="Display name for the event")] = None
    display_description: Annotated[LocaleString | None, Field(description="Display description for the event")] = None

    @model_validator(mode="after")
    def set_default_values(self) -> Self:
        """Set default values from class if instance values are None."""
        if not self.display_name:
            self.display_name = self.__class__._display_name
        if not self.display_description:
            self.display_description = self.__class__._display_description
        return self

    @classmethod
    def display_name_from_class(cls):
        return cls._display_name

    @classmethod
    def display_description_from_class(cls):
        return cls._display_description
