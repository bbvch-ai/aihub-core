from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from aihub_lib.nats.events.form.base.FormkitElement import FormkitElement

if TYPE_CHECKING:
    from aihub_lib.agents.AgentConfig import AgentConfig


class AgentConfigSpecs(BaseModel):
    """
    Defines a specification for an agent's configuration.
    """

    name: Annotated[LocaleString, Field(description="The name of the process or agent.")]
    description: Annotated[LocaleString, Field(description="The description of the process or agent.")]
    icon: Annotated[str, Field(description="The icon representing the process or agent.")] = "meteor-icons:robot"

    agent_class: Annotated[str, Field(description="The class name of the agent, used for identification.")]
    agent_id: Annotated[str, Field(description="Uniquely identifies the agent instance.", pattern=r"^[a-z0-9_-]+$")]

    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="Formkit elements of the Agent Config.")] = []

    @classmethod
    def from_agent_config(
        cls, agent_config: "AgentConfig", form: list[FormkitElement] | None = None
    ) -> "AgentConfigSpecs":
        """
        Creates an AgentConfigSpecs from an AgentConfig instance.
        """
        return cls(
            name=agent_config.name,
            description=agent_config.description,
            icon=agent_config.icon,
            agent_class=agent_config.agent_class,
            agent_id=agent_config.agent_id,
            form=form if form is not None else agent_config.to_formkit_form(),
        )
