from typing import TYPE_CHECKING, Annotated, Self

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
    from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument


class AgentConfigDTO(BaseModel):
    """
    Encapsulates the data transfer object for an agent INSTANCE's configuration.

    Contains instance-level data (agent_id, name, description, icon) and the
    configuration form. Values come from both:
    - AgentClassEntity: class-level form schema
    - AgentConfigEntityDocument: instance-specific name, description, icon, agent_id

    NOTE: This represents config for an INSTANCE (with agent_id), not an agent CLASS.
    """

    model_config = {
        "use_enum_values": True,
        # Ensure nested models serialize by alias
        "populate_by_name": True,
    }

    agent_id: Annotated[str, Field(description="The id of the agent instance.")]
    name: Annotated[str, Field(description="The display name of the agent instance.")]
    description: Annotated[str, Field(description="The description of the agent instance.")]
    icon: Annotated[str, Field(description="The icon representing the agent instance.")] = "mage:robot"
    form: Annotated[
        list[ALL_FORM_OPTIONS] | None,
        Field(description="Dynamic form configuration for agent runtime settings."),
    ] = None

    @classmethod
    def from_class_and_config(
        cls,
        class_entity: "AgentClassEntity",
        config_entity: "AgentConfigEntityDocument",
        t: LocaleHandler,
    ) -> Self:
        """
        Create an AgentConfigDTO from an AgentClassEntity and AgentConfigEntityDocument.

        Class entity provides the form schema, config entity provides instance-specific
        metadata (agent_id, name, description, icon).
        """
        form = [form_element.in_locale(t) for form_element in class_entity.form_elements] if class_entity.form else None

        name = t.extract(config_entity.name.to_locale_string())
        description = t.extract(config_entity.description.to_locale_string())

        icon = config_entity.icon or class_entity.icon or "mage:robot"

        return cls(
            agent_id=config_entity.agent_id,
            name=name,
            description=description,
            icon=icon,
            form=form,
        )
