from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecsEntity import AgentConfigSpecsEntity
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS

if TYPE_CHECKING:
    from aihub_lib.persistence.agents.AgentConfigEntity import AgentConfigEntity


class AgentConfigDTO(BaseModel):
    model_config = {
        "use_enum_values": True,
        # Ensure nested models serialize by alias
        "populate_by_name": True,
    }

    agent_id: Annotated[str, Field(description="The id of the agent.")]
    name: Annotated[str, Field(description="The name of the agent.")]
    description: Annotated[str, Field(description="The description of the agent.")]
    icon: Annotated[str, Field(description="The icon representing the agent.")] = "meteor-icons:robot"
    form: Annotated[
        list[ALL_FORM_OPTIONS] | None,
        Field(description="Dynamic form configuration for agent runtime settings."),
    ] = None

    @classmethod
    def from_agent_config_specs(cls, agent_config_specs: AgentConfigSpecs, t: LocaleHandler) -> "AgentConfigDTO":
        form = [form.in_locale(t) for form in agent_config_specs.form]
        return cls(
            agent_id=agent_config_specs.agent_id,
            name=t.extract(agent_config_specs.name),
            description=t.extract(agent_config_specs.description),
            icon=agent_config_specs.icon,
            form=form,
        )

    @classmethod
    def from_agent_config_entity_specs(
        cls, agent_config_specs_entity: AgentConfigSpecsEntity | None, t: LocaleHandler
    ) -> "AgentConfigDTO | None":
        """
        Create an AgentConfigDTO from a persisted AgentConfigSpecsEntity.
        Returns None if agent_config_specs_entity is None (for backwards compatibility with
        agents that were stored before agent_config_specs was added to AgentEntity).
        """
        if agent_config_specs_entity is None:
            return None

        # Use form_elements property to deserialize dicts back to typed Pydantic models
        form_elements = agent_config_specs_entity.form_elements
        form = [form_element.in_locale(t) for form_element in form_elements]
        return cls(
            agent_id=agent_config_specs_entity.agent_id,
            name=t.extract(agent_config_specs_entity.to_locale_string_name()),
            description=t.extract(agent_config_specs_entity.to_locale_string_description()),
            icon=agent_config_specs_entity.icon,
            form=form,
        )

    @classmethod
    def from_default_agent_config_entity(
        cls, default_agent_config: "AgentConfigEntity", t: LocaleHandler
    ) -> "AgentConfigDTO":
        """
        Create an AgentConfigDTO from a default AgentConfigEntity (embedded document).
        Used as fallback for agents stored before agent_config_specs was added.
        Returns a minimal AgentConfigDTO with no form elements.
        """
        return cls(
            agent_id=default_agent_config.agent_id,
            name=t.extract(default_agent_config.name.to_locale_string()),
            description=t.extract(default_agent_config.description.to_locale_string()),
            icon=default_agent_config.icon,
            form=None,
        )
