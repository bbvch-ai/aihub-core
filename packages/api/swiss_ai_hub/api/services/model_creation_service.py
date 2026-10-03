import copy
import types
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, create_model
from pydantic.fields import FieldInfo
from swiss_ai_hub.core.events import EventSpecs
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.jambo import SchemaConverter


class ModelCreationService:
    _input_suffix = "Input"
    _output_suffix = "Output"
    _input_excluded_fields = {
        "event_id",
        "created_at",
        "user",
        "locale",
        "display_name",
        "display_description",
        "agent_config",
    }
    _output_excluded_fields = {"event_id", "created_at", "_event_name", "_parent_event_names"}
    _model_config_dict = ConfigDict(
        arbitrary_types_allowed=False,
        populate_by_name=True,
        use_enum_values=True,
    )
    _json_schema_scalar_types: dict[str, type] = {
        "boolean": bool,
        "string": str,
        "integer": int,
        "number": float,
    }

    @staticmethod
    def create_input_model_from_event_class(event_class: type[BaseModel]) -> type[BaseModel]:
        return ModelCreationService._create_model_from_class(
            event_class, ModelCreationService._input_excluded_fields, ModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model_from_event_class(event_class: type[BaseModel]) -> type[BaseModel]:
        return ModelCreationService._create_model_from_class(
            event_class, ModelCreationService._output_excluded_fields, ModelCreationService._output_suffix
        )

    @staticmethod
    def create_input_model_from_event_specs(event_specs: EventSpecs) -> type[BaseModel]:
        event_class = ModelCreationService._create_model_from_event_specs(event_specs)
        return ModelCreationService._create_model_from_class(
            event_class, ModelCreationService._input_excluded_fields, ModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model_from_event_specs(event_specs: EventSpecs) -> type[BaseModel]:
        event_class = ModelCreationService._create_model_from_event_specs(event_specs)
        return ModelCreationService._create_model_from_class(
            event_class, ModelCreationService._output_excluded_fields, ModelCreationService._output_suffix
        )

    @staticmethod
    def create_config_model(config_specs: ConfigSpecs) -> type[BaseModel]:
        schema = copy.deepcopy(config_specs.config_schema)
        return SchemaConverter.build(schema)

    @staticmethod
    def _create_model_from_event_specs(event_specs: EventSpecs) -> type[BaseModel]:
        """Reconstructs the event's Pydantic model from its JSON Schema.

        jambo's ``SchemaConverter`` only ever reads a node's ``properties`` — it has no concept of
        ``additionalProperties`` — so a free-form map field (``dict[str, bool]``, say) has no named
        properties and jambo silently rebuilds it as an empty model. Any data submitted under that field
        then vanishes on validation (Pydantic's default ``extra="ignore"``), with no error to signal it.
        Map fields are pulled out of the schema before jambo ever sees them and reattached afterwards
        with their real type, so they survive the round-trip like every fixed-shape field already does.
        """
        schema = copy.deepcopy(event_specs.event_schema)
        schema["title"] = event_specs.event_name
        original = copy.deepcopy(schema)

        map_fields = ModelCreationService._extract_free_form_map_fields(schema)
        event_class = SchemaConverter.build(schema)
        if map_fields:
            event_class = ModelCreationService._reattach_map_fields(event_class, map_fields)
        return ModelCreationService._restore_nested_maps(event_class, original, original.get("$defs", {}))

    @staticmethod
    def _restore_nested_maps(
        model: type[BaseModel], node: dict[str, Any], definitions: dict[str, Any]
    ) -> type[BaseModel]:
        """The same repair for maps inside nested models, such as the call arguments a tool approval response
        carries on its request event, which jambo builds from the schema's definitions."""
        properties = node.get("properties", {})
        replaced: dict[str, tuple[Any, FieldInfo]] = {}
        for name, field_info in model.model_fields.items():
            nested = ModelCreationService._nested_model(field_info.annotation)
            nested_node = ModelCreationService._resolve(properties.get(name, {}), definitions)
            if nested is None or not nested_node.get("properties"):
                continue
            nested_maps = {
                key: ModelCreationService._map_field(key, value, nested_node.get("required", []))
                for key, value in nested_node["properties"].items()
                if ModelCreationService._is_free_form_map(value)
            }
            restored = ModelCreationService._restore_nested_maps(nested, nested_node, definitions)
            if nested_maps:
                restored = ModelCreationService._reattach_map_fields(restored, nested_maps)
            if restored is not nested:
                annotation = restored | None if type(None) in get_args(field_info.annotation) else restored
                replaced[name] = (annotation, field_info)
        if not replaced:
            return model
        fields = {name: (info.annotation, info) for name, info in model.model_fields.items()}
        fields.update(replaced)
        return create_model(model.__name__, **fields, __config__=ModelCreationService._model_config_dict)

    @staticmethod
    def _map_field(name: str, property_schema: dict[str, Any], required: list[str]) -> tuple[type, FieldInfo]:
        value_type = ModelCreationService._resolve_map_value_type(property_schema.get("additionalProperties"))
        default = ... if name in required and "default" not in property_schema else property_schema.get("default", {})
        return dict[str, value_type], Field(
            default=default, title=property_schema.get("title"), description=property_schema.get("description")
        )

    @staticmethod
    def _nested_model(annotation: Any) -> type[BaseModel] | None:
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation
        if get_origin(annotation) in (Union, types.UnionType):
            models = [arg for arg in get_args(annotation) if isinstance(arg, type) and issubclass(arg, BaseModel)]
            return models[0] if len(models) == 1 else None
        return None

    @staticmethod
    def _resolve(property_schema: dict[str, Any], definitions: dict[str, Any]) -> dict[str, Any]:
        reference = property_schema.get("$ref") or next(
            (member["$ref"] for member in property_schema.get("anyOf", []) if "$ref" in member), None
        )
        if reference:
            return definitions.get(reference.rsplit("/", 1)[-1], {})
        return property_schema

    @staticmethod
    def _extract_free_form_map_fields(schema: dict[str, Any]) -> dict[str, tuple[type, FieldInfo]]:
        properties: dict[str, Any] = schema.get("properties", {})
        required: list[str] = schema.get("required", [])
        map_fields: dict[str, tuple[type, FieldInfo]] = {}

        for name in list(properties):
            property_schema = properties[name]
            if not ModelCreationService._is_free_form_map(property_schema):
                continue

            is_required = name in required
            value_type = ModelCreationService._resolve_map_value_type(property_schema.get("additionalProperties"))
            default = ... if is_required and "default" not in property_schema else property_schema.get("default", {})

            map_fields[name] = (
                dict[str, value_type],
                Field(
                    default=default,
                    title=property_schema.get("title"),
                    description=property_schema.get("description"),
                ),
            )
            del properties[name]
            if is_required:
                required.remove(name)

        return map_fields

    @staticmethod
    def _is_free_form_map(property_schema: dict[str, Any]) -> bool:
        additional_properties = property_schema.get("additionalProperties")
        return additional_properties not in (None, False) and not property_schema.get("properties")

    @staticmethod
    def _resolve_map_value_type(additional_properties: Any) -> type:
        if isinstance(additional_properties, dict):
            return ModelCreationService._json_schema_scalar_types.get(additional_properties.get("type"), Any)
        return Any

    @staticmethod
    def _reattach_map_fields(
        event_class: type[BaseModel], map_fields: dict[str, tuple[type, FieldInfo]]
    ) -> type[BaseModel]:
        fields = {name: (field_info.annotation, field_info) for name, field_info in event_class.model_fields.items()}
        fields.update(map_fields)
        return create_model(
            event_class.__name__,
            **fields,
            __config__=ModelCreationService._model_config_dict,
        )

    @staticmethod
    def _create_filtered_model(
        model_name: str, source_model_class: type[BaseModel], excluded_fields: set
    ) -> type[BaseModel]:
        fields = {}
        for name, field_info in source_model_class.model_fields.items():
            if name not in excluded_fields:
                fields[name] = (field_info.annotation, field_info)

        return create_model(
            model_name,
            **fields,
            __config__=ModelCreationService._model_config_dict,
        )

    @staticmethod
    def _create_model_from_class(event_class: type[BaseModel], excluded_fields: set, suffix: str) -> type[BaseModel]:
        model_name = f"{event_class.__name__}{suffix}"
        return ModelCreationService._create_filtered_model(
            model_name=model_name, source_model_class=event_class, excluded_fields=excluded_fields
        )
