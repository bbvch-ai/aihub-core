import copy

from jambo import SchemaConverter
from pydantic import BaseModel, ConfigDict, create_model
from swiss_ai_hub.core.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import AgentConfigSpecs, EventSpecs
from swiss_ai_hub.core.nats.events.discovery.process.ProcessConfigSpecs import ProcessConfigSpecs


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
    def create_agent_config_model(agent_config_specs: AgentConfigSpecs) -> type[BaseModel]:
        schema = copy.deepcopy(agent_config_specs.agent_config_schema)
        return SchemaConverter.build(schema)

    @staticmethod
    def create_process_config_model(process_config_specs: ProcessConfigSpecs) -> type[BaseModel]:
        schema = copy.deepcopy(process_config_specs.process_config_schema)
        return SchemaConverter.build(schema)

    @staticmethod
    def _create_model_from_event_specs(event_specs: EventSpecs) -> type[BaseModel]:
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
            __config__=ModelCreationService._model_config_dict,
        )

    @staticmethod
    def _create_model_from_class(event_class: type[BaseModel], excluded_fields: set, suffix: str) -> type[BaseModel]:
        model_name = f"{event_class.__name__}{suffix}"
        return ModelCreationService._create_filtered_model(
            model_name=model_name, source_model_class=event_class, excluded_fields=excluded_fields
        )
