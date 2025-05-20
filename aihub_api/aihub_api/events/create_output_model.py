from typing import Type, TypeVar

from aihub_lib.nats.events import BaseEvent
from pydantic import BaseModel, ConfigDict, create_model

T = TypeVar("T", bound=BaseEvent)


def create_output_model(event_class: Type[T]) -> Type[BaseModel]:
    """
    Creates an output model for an event class by removing fields with secret values.
    """
    # Get all fields from the original model
    fields = {}
    for name, field_info in event_class.model_fields.items():
        # Skip fields with generated values
        if name not in ["event_id", "created_at", "_event_name", "_parent_event_names"]:
            fields[name] = (field_info.annotation, field_info)

    # Create a new model with the filtered fields
    return create_model(
        f"{event_class.event_name_from_class()}Output",
        **fields,
        __config__=ConfigDict(
            arbitrary_types_allowed=False,
            populate_by_name=True,
            use_enum_values=True,
        ),
    )
