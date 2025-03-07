from typing import Type, TypeVar

from aihub_lib.nats.events import BaseEvent
from pydantic import BaseModel, ConfigDict, create_model

T = TypeVar("T", bound=BaseEvent)


def create_input_model(event_class: Type[T]) -> Type[BaseModel]:
    """
    Creates an input model for an event class by removing the event_id and created_at fields.
    """
    # Get all fields from the original model
    fields = {}
    for name, field_info in event_class.model_fields.items():
        # Skip event_id and created_at fields
        if name not in ["event_id", "created_at", "user", "locale"]:
            fields[name] = (field_info.annotation, field_info)

    # Create a new model with the filtered fields
    return create_model(
        f"{event_class.__name__}Input",
        __base__=BaseModel,
        **fields,
        model_config=ConfigDict(
            arbitrary_types_allowed=False,
            populate_by_name=True,
            use_enum_values=True,
        ),
    )
