import copy

from jambo import SchemaConverter
from pydantic import BaseModel, ConfigDict, create_model
from swiss_ai_hub.core.events.discovery.EventSpecs import EventSpecs


class EventModelCreationService:
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

    @staticmethod
    def create_input_model(event_class: type[BaseModel]) -> type[BaseModel]:
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._input_excluded_fields, EventModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model(event_class: type[BaseModel]) -> type[BaseModel]:
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._output_excluded_fields, EventModelCreationService._output_suffix
        )

    @staticmethod
    def create_input_model_from_specs(event_specs: EventSpecs) -> type[BaseModel]:
        event_class = EventModelCreationService._create_model_from_specs(event_specs)
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._input_excluded_fields, EventModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model_from_specs(event_specs: EventSpecs) -> type[BaseModel]:
        event_class = EventModelCreationService._create_model_from_specs(event_specs)
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._output_excluded_fields, EventModelCreationService._output_suffix
        )

    @staticmethod
    def _create_model_from_specs(event_specs: EventSpecs) -> type[BaseModel]:
        schema = copy.deepcopy(event_specs.event_schema)
        schema["title"] = event_specs.event_name
        return SchemaConverter.build(schema)

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
            __config__=EventModelCreationService._model_config_dict,
        )

    @staticmethod
    def _create_model_from_class(event_class: type[BaseModel], excluded_fields: set, suffix: str) -> type[BaseModel]:
        model_name = f"{event_class.__name__}{suffix}"
        return EventModelCreationService._create_filtered_model(
            model_name=model_name, source_model_class=event_class, excluded_fields=excluded_fields
        )
