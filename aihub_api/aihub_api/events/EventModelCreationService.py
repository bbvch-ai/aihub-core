import copy
from typing import Type, TypeVar

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from jambo import SchemaConverter
from pydantic import BaseModel, ConfigDict, create_model

T = TypeVar("T", bound=BaseEvent)


class EventModelCreationService:
    _input_suffix = "Input"
    _output_suffix = "Output"
    _input_excluded_fields = {"event_id", "created_at", "user", "locale", "display_name", "display_description"}
    _output_excluded_fields = {"event_id", "created_at", "_event_name", "_parent_event_names"}
    _model_config_dict = ConfigDict(
        arbitrary_types_allowed=False,
        populate_by_name=True,
        use_enum_values=True,
    )

    @staticmethod
    def create_input_model(event_class: Type[T]) -> Type[BaseModel]:
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._input_excluded_fields, EventModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model(event_class: Type[T]) -> Type[BaseModel]:
        return EventModelCreationService._create_model_from_class(
            event_class, EventModelCreationService._output_excluded_fields, EventModelCreationService._output_suffix
        )

    @staticmethod
    def create_input_model_from_specs(event_specs: EventSpecs) -> Type[BaseModel]:
        return EventModelCreationService._create_model_from_specs(
            event_specs, EventModelCreationService._input_excluded_fields, EventModelCreationService._input_suffix
        )

    @staticmethod
    def create_output_model_from_specs(event_specs: EventSpecs) -> Type[BaseModel]:
        return EventModelCreationService._create_model_from_specs(
            event_specs, EventModelCreationService._output_excluded_fields, EventModelCreationService._output_suffix
        )

    @staticmethod
    def _create_filtered_model(
        model_name: str, source_model_class: Type[BaseModel], excluded_fields: set
    ) -> Type[BaseModel]:
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
    def _create_model_from_class(event_class: Type[T], excluded_fields: set, suffix: str) -> Type[BaseModel]:
        model_name = f"{event_class.event_name_from_class()}{suffix}"
        return EventModelCreationService._create_filtered_model(
            model_name=model_name, source_model_class=event_class, excluded_fields=excluded_fields
        )

    @staticmethod
    def _create_model_from_specs(event_specs: EventSpecs, excluded_fields: set, suffix: str) -> Type[BaseModel]:
        schema = copy.deepcopy(event_specs.event_schema)

        model_name = f"{event_specs.event_name}{suffix}"
        schema["title"] = model_name

        full_jambo_model = SchemaConverter.build(schema)

        return EventModelCreationService._create_filtered_model(
            model_name=model_name, source_model_class=full_jambo_model, excluded_fields=excluded_fields
        )
