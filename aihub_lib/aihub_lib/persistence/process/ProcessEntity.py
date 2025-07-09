from datetime import datetime

from bson import ObjectId
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
)

from aihub_lib.persistence.agents.AgentEntity import EventSpec


class ProcessInSpec(EmbeddedDocument):
    route = StringField(required=True)
    method = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)

    @classmethod
    def from_dto(cls, process_in_dto) -> "ProcessInSpec":
        return cls(
            route=process_in_dto.route,
            method=process_in_dto.method,
            is_process_start=process_in_dto.is_process_start,
            event_specs=EventSpec.from_dto(process_in_dto.event_specs),
        )


class ProcessConfig(EmbeddedDocument):
    process_id = StringField(required=False)
    name = StringField(required=True)
    description = StringField(required=True)
    icon = StringField(default="meteor-icons:robot")


class ProcessEntity(Document):
    meta = {
        "collection": "processes",
        "strict": False,
        "indexes": [{"fields": ["process_class", "process_id"], "unique": True}],
    }
    process_class = StringField(required=True)
    process_id = StringField(required=True)
    process_config = EmbeddedDocumentField(ProcessConfig, required=True)
    human_inputs = ListField(EmbeddedDocumentField(ProcessInSpec))      # TODO: Make required
    program_inputs = ListField(EmbeddedDocumentField(ProcessInSpec))    # TODO: Make required
    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @classmethod
    def create_process(
        cls,
        process_class: str,
        process_id: str,
        process_config: ProcessConfig,
        human_inputs: list[ProcessInSpec],
        program_inputs: list[ProcessInSpec],
        process_entity_id: ObjectId | None = None,
    ) -> "ProcessEntity":
        process = cls(
            id=process_entity_id or ObjectId(),
            process_class=process_class,
            process_id=process_id,
            process_config=process_config,
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        process.save()
        return process

    @classmethod
    def create_or_update_from_dto(cls, process_dto) -> "ProcessEntity":
        existing_process = cls.objects(process_class=process_dto.process_class, process_id=process_dto.process_id).first()

        process_config = ProcessConfig(
            process_id=process_dto.process_config.process_id,
            name=process_dto.process_config.name,
            description=process_dto.process_config.description,
            icon=process_dto.process_config.icon,
        )

        # Create EventSpec objects, serializing the schema to avoid $ issues
        human_inputs = [ProcessInSpec.from_dto(process_in_dto) for process_in_dto in process_dto.human_inputs]
        program_inputs = [ProcessInSpec.from_dto(process_in_dto) for process_in_dto in process_dto.program_inputs]

        if existing_process:
            # Update existing process
            existing_process.process_config = process_config
            existing_process.human_inputs = human_inputs
            existing_process.program_inputs = program_inputs
            existing_process.last_discovered = datetime.now()
            existing_process.save()
            return existing_process
        else:
            # Create new process
            return cls.create_process(
                process_class=process_dto.process_class,
                process_id=process_dto.process_id,
                process_config=process_config,
                human_inputs=human_inputs,
                program_inputs=program_inputs,
            )

    @classmethod
    def get_processes(cls):
        return cls.objects()

    @classmethod
    def get_process_by_id(cls, process_entity_id: str) -> "ProcessEntity":
        return cls.objects().get(id=ObjectId(process_entity_id))

    @classmethod
    def get_process(cls, process_class: str, process_id: str) -> "ProcessEntity":
        return cls.objects().get(process_class=process_class, process_id=process_id)