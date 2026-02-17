from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpHostConfig import McpConnectionConfig, McpHostConfig
from aihub_lib.nats.events.form.elements.LocaleInput import LocaleInput
from pydantic import BaseModel, Field

from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class DelegatedAgentToolConfig(BaseModel):
    """Exposes another agent as a virtual tool the LLM can invoke."""

    agent_id: Annotated[str, Field(description="ID of the agent to delegate to.")]
    agent_class: Annotated[str, Field(description="Class name of the agent.")]
    tool_name: Annotated[str, Field(description="Function name the LLM sees for this agent.")]
    tool_description: Annotated[str, Field(description="Description of what the agent tool does.")]
    tool_parameters_schema: Annotated[
        dict,
        Field(description="JSON Schema for the tool parameters."),
    ] = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Query to send to the agent."}},
        "required": ["query"],
    }


class McpOrchestratorAgentConfig(AgentConfig):
    """Configuration for the MCP Orchestrator agent.

    system_prompt and llm are user-configurable (form elements in as_form).
    mcp and delegated_agents are deployment-specific (no form elements).
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt to guide the orchestrator's behavior.", title="System Prompt"),
    ] = None
    llm: Annotated[LLMConfig, Field(description="LLM for tool-calling decisions.")]
    mcp: Annotated[McpHostConfig, Field(description="MCP Host configuration.")]
    delegated_agents: Annotated[
        list[DelegatedAgentToolConfig],
        Field(default_factory=list, description="Agents exposed as virtual tools to the LLM."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode McpOrchestratorAgentConfig.

        Only system_prompt and llm are user-configurable. mcp and delegated_agents
        are deployment-specific and not rendered in the UI.
        """
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            agent_class=base.agent_class,
            system_prompt=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.config.system_prompt.label"),
                help=AgentLocaleString.from_i18n_path("agent.mcp_orchestrator_agent.config.system_prompt.help"),
                input_type="textarea",
            ),
            llm=LLMConfig.as_form(),
            mcp=McpHostConfig(
                connections=[McpConnectionConfig(name="default", url="http://localhost:12008/mcp")],
            ),
            delegated_agents=[],
        )
