import json
from typing import Annotated, Any, Self, override

from pydantic import BaseModel, Discriminator, Field, Tag
from swiss_ai_hub.core.events.process import ProcessEvent
from swiss_ai_hub.core.events.process import WorkEvent
from swiss_ai_hub.core.events.process import WorkRequestEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.messaging.entities.persisted_process_event_entity import PersistedProcessEventEntity

# Import all events here that the frontend should be able to display
ProcessEvents = (
    Annotated[ProcessEvent, Tag("ProcessEvent")]
    | Annotated[WorkRequestEvent, Tag("WorkRequestEvent")]
    | Annotated[WorkEvent, Tag("WorkEvent")]
)


def event_discriminator(event: ProcessEvent) -> str:
    valid_tags = [arg.__metadata__[0].tag for arg in ProcessEvents.__args__]

    # Return "DisplayEvent" if _event_name is missing or not in valid_tags
    if not hasattr(event, "_event_name"):
        return "ProcessEvent"

    if event._event_name in valid_tags:
        return event._event_name

    for event_name in event._parent_event_names:
        if event_name in valid_tags:
            return event_name

    return "ProcessEvent"


class ContextualizedProcessEvent(BaseModel):
    """
    Wraps an process event with context information like the processes class, ID, and thread ID.
    This is necessary as the event payload itself is independent of the topic context through
    which the event was published.
    This class ensures that both the information from the topic context and the event itself is bundled
    together.
    """

    locale: Annotated[
        str,
        Field(
            description="The locale in which event name and description is returned.",
        ),
    ] = LocaleHandler.DEFAULT_LOCALE
    event_display_name: Annotated[str, Field(description="Display name for the event")]
    event_display_description: Annotated[str, Field(description="Display description for the event")]

    process_class: Annotated[str, Field(description="The process class responsible for this event.")]
    process_id: Annotated[str, Field(description="Unique identifier of the process instance that produced the event.")]
    process_walkthrough_id: Annotated[str, Field(description="Unique identifier assigned to this walkthrough.")]
    event_type: Annotated[str, Field(description="Type of the event.")]
    event_name: Annotated[str, Field(description="Name of the event, indicating its subtype or category.")]
    event_id: Annotated[str, Field(description="Unique identifier of this event instance.")]
    event: Annotated[
        ProcessEvent,
        Field(
            description="Data of the event itself.",
            discriminator=Discriminator(event_discriminator),
        ),
    ]

    @classmethod
    def from_persisted_event(cls, persisted_event: PersistedProcessEventEntity, locale: str | None = None) -> Self:
        """
        Construct a ContextualizedProcessEvent from a PersistedProcessEventEntity, converting persisted event data
        into a client-ready format.
        """
        locale_handler = LocaleHandler(locale=locale)
        process_event = ProcessEvent.deserialize_event(persisted_event.event_data)
        return cls(
            locale=locale or locale_handler.DEFAULT_LOCALE,
            process_class=persisted_event.process_class,
            process_id=persisted_event.process_id,
            process_walkthrough_id=persisted_event.process_walkthrough_id,
            event_type=persisted_event.event_type,
            event_name=persisted_event.event_name,
            event_id=persisted_event.event_id,
            event=process_event,
            event_display_name=locale_handler.extract(process_event.display_name),
            event_display_description=locale_handler.extract(process_event.display_description),
        )

    @override
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Serializes the event into a dictionary. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        data = super().model_dump(**kwargs)
        return {**data, "event": self.event.model_dump(**kwargs)}

    @override
    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Serializes the event into a JSON string. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        return json.dumps(self.model_dump(**kwargs), default=str)
