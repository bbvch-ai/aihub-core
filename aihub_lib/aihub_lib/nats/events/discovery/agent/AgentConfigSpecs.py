from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS

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
    def from_agent_config(cls, agent_config: "AgentConfig") -> "AgentConfigSpecs":
        """
        Creates an AgentConfigSpecs from an AgentConfig instance.

        Extracts the form elements by calling to_formkit_form() on the config instance,
        along with the metadata fields (name, description, icon, agent_class, agent_id).
        """
        return cls(
            name=agent_config.name,
            description=agent_config.description,
            icon=agent_config.icon,
            agent_class=agent_config.agent_class,
            agent_id=agent_config.agent_id,
            form=agent_config.to_formkit_form(),
        )

    @classmethod
    def from_agent_config_class(cls, agent_config_type: type["AgentConfig"]) -> "AgentConfigSpecs":
        """
        Creates an AgentConfigSpecs from an AgentConfig class type.

        This method is deprecated. Use from_agent_config() with an instance instead.
        This exists for backward compatibility with tests that pass a class type.

        Note: This will only work if the AgentConfig class has default values for all required fields,
        which is typically not the case for custom agent configs.
        """
        # For backward compatibility, try to create an instance with minimal required fields
        # This is a fallback for tests - in production, use from_agent_config() with the default_agent_config
        try:
            dummy_instance = agent_config_type(
                name=LocaleString(en="", de="", fr="", it=""),
                description=LocaleString(en="", de="", fr="", it=""),
                agent_class="",
                agent_id="placeholder",
            )
            return cls.from_agent_config(dummy_instance)
        except Exception:
            # If we can't create an instance, return empty specs
            return cls(
                name=LocaleString(en="", de="", fr="", it=""),
                description=LocaleString(en="", de="", fr="", it=""),
                agent_class="",
                agent_id="placeholder",
                form=[],
            )
