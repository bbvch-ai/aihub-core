import logging
from datetime import datetime

from bson import ObjectId
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    ReferenceField,
    StringField,
)

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events.discovery.process.agent_in.AgentInSpecs import AgentInSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.persistence.agents.AgentEntity import EventSpec
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.persistence.process.ProcessConfigEntityEmbeddedDocument import ProcessConfigEntityEmbeddedDocument

logger = logging.getLogger(__name__)


class ProgramInSpecsEntity(EmbeddedDocument):
    route = StringField(required=True)
    method = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)

    @classmethod
    def from_specs(cls, specs: ProgramInSpecs) -> "ProgramInSpecsEntity":
        return cls(
            route=specs.route,
            method=specs.method,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
        )


class HumanInSpecsEntity(EmbeddedDocument):
    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    route = StringField(required=True)
    method = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)
    form = ListField(DictField(), default=list)

    @classmethod
    def from_specs(cls, specs: HumanInSpecs) -> "HumanInSpecsEntity":
        return cls(
            name=LocaleStringEntity.from_locale_string(specs.name),
            description=LocaleStringEntity.from_locale_string(specs.description),
            route=specs.route,
            method=specs.method,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
            form=[form_element.model_dump() for form_element in specs.form],
        )


class AgentInSpecsEntity(EmbeddedDocument):
    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)

    @classmethod
    def from_specs(cls, specs: AgentInSpecs) -> "AgentInSpecsEntity":
        return cls(
            agent_class=specs.agent_class,
            agent_id=specs.agent_id,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
        )


class ProcessConfig(EmbeddedDocument):
    process_id = StringField(required=False)
    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    icon = StringField(default="meteor-icons:robot")


class ProcessEntity(Document):
    meta = {
        "collection": "processes",
        "strict": False,
        "indexes": [
            {"fields": ["process_class", "process_id"], "unique": True},
            {"fields": ["process_class"]},
        ],
    }
    process_class = StringField(required=True)
    process_id = StringField(required=True)
    process_config = ReferenceField(ProcessConfigEntityDocument, required=False)
    default_process_config = EmbeddedDocumentField(ProcessConfigEntityEmbeddedDocument, required=True)
    human_inputs = ListField(EmbeddedDocumentField(HumanInSpecsEntity), default=list)
    program_inputs = ListField(EmbeddedDocumentField(ProgramInSpecsEntity), default=list)
    agent_inputs = ListField(EmbeddedDocumentField(AgentInSpecsEntity), default=list)
    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @classmethod
    @trace_fn
    def create_process(
        cls,
        process_class: str,
        process_id: str,
        process_config: ProcessConfigEntityDocument | None,
        default_process_config: ProcessConfigEntityEmbeddedDocument,
        human_inputs: list[HumanInSpecsEntity],
        program_inputs: list[ProgramInSpecsEntity],
        agent_inputs: list[AgentInSpecsEntity],
        process_entity_id: ObjectId | None = None,
    ) -> "ProcessEntity":
        process = cls(
            id=process_entity_id or ObjectId(),
            process_class=process_class,
            process_id=process_id,
            process_config=process_config,
            default_process_config=default_process_config,
            human_inputs=human_inputs,
            agent_inputs=agent_inputs,
            program_inputs=program_inputs,
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        process.save()
        return process

    @classmethod
    @trace_fn
    def create_or_update(
        cls,
        process_id: str,
        process_class: str,
        default_process_config: ProcessConfig,
        human_inputs: list[HumanInSpecs],
        program_inputs: list[ProgramInSpecs],
        agent_inputs: list[AgentInSpecs],
    ) -> "ProcessEntity":
        existing_process = cls.objects(process_class=process_class, process_id=process_id).first()

        process_config_entity = ProcessConfigEntityDocument.find_for_class_and_id(
            process_class=process_class, process_id=process_id
        )
        if not process_config_entity:
            logger.debug(f"No process config found for class {process_class} and ID {process_id}.")

        default_process_config_entity = ProcessConfigEntityEmbeddedDocument.from_process_config(default_process_config)

        # Create EventSpec objects, serializing the schema to avoid $ issues
        human_inputs = [HumanInSpecsEntity.from_specs(human_in_dto) for human_in_dto in human_inputs]
        program_inputs = [ProgramInSpecsEntity.from_specs(program_in_dto) for program_in_dto in program_inputs]
        agent_inputs = [AgentInSpecsEntity.from_specs(agent_in_dto) for agent_in_dto in agent_inputs]

        if existing_process:
            # Update existing process
            existing_process.default_process_config = default_process_config_entity
            existing_process.process_config = process_config_entity
            existing_process.human_inputs = human_inputs
            existing_process.program_inputs = program_inputs
            existing_process.agent_inputs = agent_inputs
            existing_process.last_discovered = datetime.now()
            existing_process.save()
            return existing_process
        else:
            # Create new process
            return cls.create_process(
                process_class=process_class,
                process_id=process_id,
                process_config=process_config_entity,
                default_process_config=default_process_config_entity,
                human_inputs=human_inputs,
                program_inputs=program_inputs,
                agent_inputs=agent_inputs,
            )

    @classmethod
    @trace_fn
    def get_processes(cls):
        return cls.objects()

    @classmethod
    @trace_fn
    def get_process_by_id(cls, process_entity_id: str) -> "ProcessEntity":
        return cls.objects().get(id=ObjectId(process_entity_id))

    @classmethod
    @trace_fn
    def get_process(cls, process_class: str, process_id: str) -> "ProcessEntity":
        return cls.objects(process_class=process_class, process_id=process_id).first()
