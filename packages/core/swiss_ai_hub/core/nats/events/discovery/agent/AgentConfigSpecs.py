from typing import TYPE_CHECKING, Annotated, Any, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from swiss_ai_hub.core.agents.AgentConfig import AgentConfig


class AgentConfigSpecs(BaseModel):
    """
    Validation specification for agent configuration form submissions.

    Contains ONLY the agent class identifier and JSON schema for validation.
    Instance-level fields (name, description, icon, agent_id) are stored
    separately in AgentConfigEntityDocument and provided by the Agent class.

    The JSON schema is generated from the agent's configurable fields via
    to_configurable_submission_model() and is used to validate form submissions.
    """

    agent_class: Annotated[str, Field(description="The class name of the agent.")]
    agent_config_schema: Annotated[
        dict[str, Any],
        Field(
            description="JSON schema for validating form submissions. "
            "Generated from the agent's configurable fields via to_configurable_submission_model()."
        ),
    ] = {}

    @classmethod
    def from_agent_config(cls, agent_config: "AgentConfig", agent_class: str) -> Self:
        """
        Creates an AgentConfigSpecs from an AgentConfig instance.

        Extracts the JSON schema from the configurable submission model.
        Instance-level metadata (name, description, icon, agent_id) is NOT included -
        those come from the Agent class definition or AgentConfigEntityDocument.
        """
        submission_model = agent_config.to_configurable_submission_model()

        return cls(
            agent_class=agent_class,
            agent_config_schema=submission_model.model_json_schema(),
        )
