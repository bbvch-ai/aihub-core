from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from pydantic import BaseModel, ConfigDict, Field, create_model

T = TypeVar("T", bound=BaseEvent)

# Fields with generated values that should be excluded from input models
EXCLUDED_FIELDS = {"event_id", "created_at", "user", "locale", "display_name", "display_description"}


def create_input_model(event_class: Type[T]) -> Type[BaseModel]:
    """
    Creates an input model for an event class by removing fields with generated values.
    """
    # Get all fields from the original model
    fields = {}
    for name, field_info in event_class.model_fields.items():
        # Skip fields with generated values
        if name not in EXCLUDED_FIELDS:
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
    definitions = schema.get("$defs", {})

    fields = {}
    for field_name, field_schema in properties.items():
        if field_name not in EXCLUDED_FIELDS:
            # Convert JSON schema field to Pydantic field
            field_type = _json_schema_to_python_type(field_schema, definitions)
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


def _json_schema_to_python_type(field_schema: Dict[str, Any], definitions: Dict[str, Any] = None) -> Type:
    """Convert JSON schema type to Python type."""
    if definitions is None:
        definitions = {}

    # Handle $ref references
    if "$ref" in field_schema:
        ref_path = field_schema["$ref"]
        if ref_path.startswith("#/$defs/"):
            def_name = ref_path.replace("#/$defs/", "")
            if def_name in definitions:
                return _create_nested_model_from_schema(definitions[def_name], definitions)
        return dict

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
        items_schema = field_schema.get("items", {})
        if items_schema:
            item_type = _json_schema_to_python_type(items_schema, definitions)
            return List[item_type]
        return list
    elif schema_type == "object":
        # For objects with properties, create a dynamic model
        properties = field_schema.get("properties")
        if properties:
            return _create_nested_model_from_schema(field_schema, definitions)
        return dict
    elif "anyOf" in field_schema:
        # Handle Union types (e.g., Optional fields)
        return _handle_union_type(field_schema["anyOf"], definitions)
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


def _create_nested_model_from_schema(
    object_schema: Dict[str, Any], definitions: Dict[str, Any] = None
) -> Type[BaseModel]:
    """Create a dynamic Pydantic model from a JSON object schema."""
    if definitions is None:
        definitions = {}

    properties = object_schema.get("properties", {})
    required = set(object_schema.get("required", []))

    fields = {}
    for field_name, field_schema in properties.items():
        field_type = _json_schema_to_python_type(field_schema, definitions)
        field_info = _create_field_info(field_schema, field_name in required)
        fields[field_name] = (field_type, field_info)

    # Create a dynamic model name
    model_name = object_schema.get("title", "DynamicNestedModel")

    return create_model(
        model_name,
        **fields,
        __config__=ConfigDict(
            arbitrary_types_allowed=False,
            populate_by_name=True,
            use_enum_values=True,
        ),
    )


def _handle_union_type(any_of_schemas: List[Dict[str, Any]], definitions: Dict[str, Any] = None) -> Type:
    """Handle anyOf/Union types from JSON schema."""
    if definitions is None:
        definitions = {}

    types = []
    has_null = False

    for schema in any_of_schemas:
        if schema.get("type") == "null":
            has_null = True
        else:
            types.append(_json_schema_to_python_type(schema, definitions))

    if len(types) == 1 and has_null:
        return Optional[types[0]]
    elif len(types) > 1:
        if has_null:
            return Optional[Union[tuple(types)]]
        else:
            return Union[tuple(types)]
    else:
        return Any
