from typing import Any, Dict, Type, TypeVar, Union

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from pydantic import BaseModel, ConfigDict, Field, create_model

T = TypeVar("T", bound=BaseEvent)


def create_input_model(event_class: Type[T]) -> Type[BaseModel]:
    """
    Creates an input model for an event class by removing fields with generated values.
    """
    # Get all fields from the original model
    fields = {}
    for name, field_info in event_class.model_fields.items():
        # Skip fields with generated values
        if name not in ["event_id", "created_at", "user", "locale", "display_name", "display_description"]:
            fields[name] = (field_info.annotation, field_info)

    # Create a new model with the filtered fields
    return create_model(
        f"{event_class.event_name_from_class()}Input",
        **fields,
        __config__=ConfigDict(
            arbitrary_types_allowed=False,
            populate_by_name=True,
            use_enum_values=True,
        ),
    )


def create_input_model_from_specs(event_specs: EventSpecs) -> Type[BaseModel]:
    """
    Creates an input model from EventSpecs by removing fields with generated values.
    """
    schema = event_specs.event_schema
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    # Fields to exclude (same as original function)
    excluded_fields = {"event_id", "created_at", "user", "locale", "display_name", "display_description"}

    fields = {}
    for field_name, field_schema in properties.items():
        if field_name not in excluded_fields:
            # Convert JSON schema field to Pydantic field
            field_type = _json_schema_to_python_type(field_schema)
            field_info = _create_field_info(field_schema, field_name in required)
            fields[field_name] = (field_type, field_info)

    # Create the model
    return create_model(
        f"{event_specs.event_name}Input",
        **fields,
        __config__=ConfigDict(
            arbitrary_types_allowed=False,
            populate_by_name=True,
            use_enum_values=True,
        ),
    )


def _json_schema_to_python_type(field_schema: Dict[str, Any]) -> Type:
    """Convert JSON schema type to Python type."""
    schema_type = field_schema.get("type")

    if schema_type == "string":
        return str
    elif schema_type == "integer":
        return int
    elif schema_type == "number":
        return float
    elif schema_type == "boolean":
        return bool
    elif schema_type == "array":
        return list
    elif schema_type == "object":
        return dict
    else:
        return Any


def _create_field_info(field_schema: Dict[str, Any], is_required: bool):
    """Create Pydantic Field info from JSON schema."""
    kwargs = {}

    # Handle description
    if "description" in field_schema:
        kwargs["description"] = field_schema["description"]

    # Handle default value
    if "default" in field_schema:
        kwargs["default"] = field_schema["default"]
    elif not is_required:
        kwargs["default"] = None

    return Field(**kwargs)
