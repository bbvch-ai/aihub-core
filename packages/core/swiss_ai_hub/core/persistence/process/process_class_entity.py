import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Self

from bson import ObjectId
from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    StringField,
)
from pydantic import TypeAdapter

from swiss_ai_hub.core.events.process.discovery.agent_in.agent_in_specs import AgentInSpecs
from swiss_ai_hub.core.events.process.discovery.human_in.human_in_specs import HumanInSpecs
from swiss_ai_hub.core.events.process.discovery.program_in.program_in_specs import ProgramInSpecs
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.agents.agent_class_entity import EventSpec
from swiss_ai_hub.core.persistence.form.config_specs_entity import ConfigSpecsEntity
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.base.formkit_element import FormkitElement

logger = logging.getLogger(__name__)


class ProgramInSpecsEntity(EmbeddedDocument):
    """Stores program input specification in the database."""

    route = StringField(required=True)
    method = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)

    @classmethod
    def from_specs(cls, specs: ProgramInSpecs) -> Self:
        return cls(
            route=specs.route,
            method=specs.method,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
        )

    def to_specs(self) -> ProgramInSpecs:
        """Convert this entity back to a ProgramInSpecs Pydantic model."""
        return ProgramInSpecs(
            route=self.route,
            method=self.method,
            is_process_start=self.is_process_start,
            event_specs=self.event_specs.to_specs(),
        )


class HumanInSpecsEntity(EmbeddedDocument):
    """Stores human input specification in the database."""

    name = EmbeddedDocumentField(LocaleStringEntity, required=True)
    description = EmbeddedDocumentField(LocaleStringEntity, required=True)
    route = StringField(required=True)
    method = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)
    form = ListField(DictField(), default=list)

    @classmethod
    def from_specs(cls, specs: HumanInSpecs) -> Self:
        return cls(
            name=LocaleStringEntity.from_locale_string(specs.name),
            description=LocaleStringEntity.from_locale_string(specs.description),
            route=specs.route,
            method=specs.method,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
            form=[form_element.model_dump() for form_element in specs.form],
        )

    def to_specs(self) -> HumanInSpecs:
        """Convert this entity back to a HumanInSpecs Pydantic model."""
        adapter = TypeAdapter(list[ALL_FORM_OPTIONS])
        form_elements = adapter.validate_python(self.form) if self.form else []
        return HumanInSpecs(
            name=self.name.to_locale_string(),
            description=self.description.to_locale_string(),
            route=self.route,
            method=self.method,
            is_process_start=self.is_process_start,
            event_specs=self.event_specs.to_specs(),
            form=form_elements,
        )


class AgentInSpecsEntity(EmbeddedDocument):
    """Stores agent input specification in the database."""

    agent_class = StringField(required=True)
    agent_id = StringField(required=True)
    is_process_start = BooleanField(required=True)
    event_specs = EmbeddedDocumentField(EventSpec, required=True)

    @classmethod
    def from_specs(cls, specs: AgentInSpecs) -> Self:
        return cls(
            agent_class=specs.agent_class,
            agent_id=specs.agent_id,
            is_process_start=specs.is_process_start,
            event_specs=EventSpec.from_specs(specs.event_specs),
        )

    def to_specs(self) -> AgentInSpecs:
        """Convert this entity back to an AgentInSpecs Pydantic model."""
        return AgentInSpecs(
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            is_process_start=self.is_process_start,
            event_specs=self.event_specs.to_specs(),
        )


class ProcessClassEntity(Document):
    """
    Represents a registered process CLASS in the system.

    Stores the class-level metadata (name, description, icon), form schema for
    creating process instances, and the validation specs.
    Online status is determined by the last_discovered timestamp.

    NOTE: This entity stores CLASS information only (one record per process_class).
    Instance/configuration data is stored in ProcessConfigEntityDocument.
    """

    ONLINE_THRESHOLD = timedelta(minutes=5)

    meta = {
        "collection": "process_classes",
        "strict": False,
        "indexes": [{"fields": ["process_class"], "unique": True}],
    }
    process_class = StringField(required=True, unique=True)

    # Class-level metadata
    name = EmbeddedDocumentField(LocaleStringEntity, required=False, description="Display name for this process class.")
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=False, description="Description of this process class."
    )
    icon = StringField(required=True, default="mage:broadcast", description="Icon for this process class.")

    form = ListField(DictField(), default=list, description="FormKit elements defining the process configuration form.")
    process_config_specs = EmbeddedDocumentField(ConfigSpecsEntity, required=False)

    # Process-specific metadata
    human_inputs = ListField(EmbeddedDocumentField(HumanInSpecsEntity), default=list)
    program_inputs = ListField(EmbeddedDocumentField(ProgramInSpecsEntity), default=list)
    agent_inputs = ListField(EmbeddedDocumentField(AgentInSpecsEntity), default=list)
    templates = ListField(DictField(), default=list)

    first_discovered = DateTimeField(required=True, default=datetime.now)
    last_discovered = DateTimeField(required=True, default=datetime.now)

    @property
    def is_online(self) -> bool:
        """Process is online if it responded to discovery within the threshold."""
        if self.last_discovered is None:
            return False
        return datetime.now() - self.last_discovered < self.ONLINE_THRESHOLD

    @property
    def form_elements(self) -> list["FormkitElement"]:
        """Deserialize the stored form dicts back to typed form element Pydantic models."""
        if not self.form:
            return []
        adapter = TypeAdapter(list[ALL_FORM_OPTIONS])
        return adapter.validate_python(self.form)

    @classmethod
    @trace_fn
    def create_process_class(
        cls,
        process_class: str,
        name: LocaleStringEntity | None,
        description: LocaleStringEntity | None,
        icon: str,
        form: list[dict],
        process_config_specs: ConfigSpecsEntity | None,
        human_inputs: list[HumanInSpecsEntity],
        program_inputs: list[ProgramInSpecsEntity],
        agent_inputs: list[AgentInSpecsEntity],
        templates: list[dict] | None = None,
        process_class_entity_id: ObjectId | None = None,
    ) -> Self:
        process = cls(
            id=process_class_entity_id or ObjectId(),
            process_class=process_class,
            name=name,
            description=description,
            icon=icon,
            form=form,
            process_config_specs=process_config_specs,
            human_inputs=human_inputs,
            program_inputs=program_inputs,
            agent_inputs=agent_inputs,
            templates=templates or [],
            first_discovered=datetime.now(),
            last_discovered=datetime.now(),
        )
        process.save()
        return process

    @classmethod
    @trace_fn
    def create_or_update(
        cls,
        process_class: str,
        name: LocaleString,
        description: LocaleString,
        icon: str,
        form: list[ALL_FORM_OPTIONS],
        process_config_specs: ConfigSpecs,
        human_inputs: list[HumanInSpecs],
        program_inputs: list[ProgramInSpecs],
        agent_inputs: list[AgentInSpecs],
        templates: list[dict] | None = None,
    ) -> Self:
        """
        Creates a new ProcessClassEntity or updates an existing one if a process
        with the same process_class already exists.
        """
        existing_process = cls.objects(process_class=process_class).first()

        name_entity = LocaleStringEntity.from_locale_string(name)
        description_entity = LocaleStringEntity.from_locale_string(description)

        # Store WITHOUT aliases - MongoDB doesn't allow keys starting with '$'
        form_dicts = [element.model_dump() for element in form]
        process_config_specs_entity = ConfigSpecsEntity.from_specs(process_config_specs)

        human_inputs_entities = [HumanInSpecsEntity.from_specs(h) for h in human_inputs]
        program_inputs_entities = [ProgramInSpecsEntity.from_specs(p) for p in program_inputs]
        agent_inputs_entities = [AgentInSpecsEntity.from_specs(a) for a in agent_inputs]

        if existing_process:
            existing_process.name = name_entity
            existing_process.description = description_entity
            existing_process.icon = icon
            existing_process.form = form_dicts
            existing_process.process_config_specs = process_config_specs_entity
            existing_process.human_inputs = human_inputs_entities
            existing_process.program_inputs = program_inputs_entities
            existing_process.agent_inputs = agent_inputs_entities
            existing_process.templates = templates or []
            existing_process.last_discovered = datetime.now()
            existing_process.save()
            return existing_process
        else:
            return cls.create_process_class(
                process_class=process_class,
                name=name_entity,
                description=description_entity,
                icon=icon,
                form=form_dicts,
                process_config_specs=process_config_specs_entity,
                human_inputs=human_inputs_entities,
                program_inputs=program_inputs_entities,
                agent_inputs=agent_inputs_entities,
                templates=templates,
            )

    @classmethod
    @trace_fn
    def get_all(cls) -> list["ProcessClassEntity"]:
        """Get all registered process classes."""
        return list(cls.objects())

    @classmethod
    @trace_fn
    def get_by_process_class(cls, process_class: str) -> "ProcessClassEntity | None":
        """Get a process class by its class name."""
        return cls.objects(process_class=process_class).first()

    @classmethod
    @trace_fn
    def get_by_id(cls, process_class_entity_id: str) -> Self:
        """Get a process class by its MongoDB document ID."""
        return cls.objects().get(id=ObjectId(process_class_entity_id))
