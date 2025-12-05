from mongoengine import DictField, EmbeddedDocument, EmbeddedDocumentField, ListField, StringField
from pydantic import TypeAdapter

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class AgentConfigSpecsEntity(EmbeddedDocument):
    agent_class = StringField(required=True)
    agent_id = StringField(required=True, description="Unique, URL-safe ID for the agent instance (e.g., 'agent_123').")
    name = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Name of the agent, used for display in the UI."
    )
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Description of the agent's purpose or functionality."
    )
    icon = StringField(required=True, description="Icon representing the agent, e.g., 'meteor-icons:robot'.")

    form = ListField(DictField(), default=list)

    @classmethod
    def from_specs(cls, specs: AgentConfigSpecs) -> "AgentConfigSpecsEntity":
        return cls(
            agent_class=specs.agent_class,
            agent_id=specs.agent_id,
            name=LocaleStringEntity.from_locale_string(specs.name),
            description=LocaleStringEntity.from_locale_string(specs.description),
            icon=specs.icon,
            form=[form_element.model_dump() for form_element in specs.form],
        )

    @property
    def form_elements(self) -> list[ALL_FORM_OPTIONS]:
        """
        Deserialize the stored form dicts back to typed form element Pydantic models.
        Uses TypeAdapter for proper discriminated union validation.
        """
        if not self.form:
            return []
        adapter = TypeAdapter(list[ALL_FORM_OPTIONS])
        return adapter.validate_python(self.form)

    def to_locale_string_name(self) -> LocaleString:
        """Convert the name LocaleStringEntity to a LocaleString."""
        return self.name.to_locale_string()

    def to_locale_string_description(self) -> LocaleString:
        """Convert the description LocaleStringEntity to a LocaleString."""
        return self.description.to_locale_string()
