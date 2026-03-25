from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber, LocaleInput
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class McpReactAgentConfig(AgentConfig):
    """Configuration for the MCP ReAct Agent — connects to an external MCP server and reasons over its tools."""

    mcp: Annotated[
        McpClientConfig,
        Field(description="MCP server connection configuration."),
    ]
    llm: Annotated[
        LLMConfig,
        Field(description="LLM used for reasoning and tool selection."),
    ]
    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt defining the agent's behavior when reasoning about tool use."),
    ] = None
    max_iterations: Annotated[
        int | InputNumber,
        Field(default=10, description="Maximum number of reasoning iterations before graceful termination."),
        Gt(0),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(default=128000, description="Maximum tokens allowed in input to manage context size or cost."),
        Gt(0),
    ]

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            mcp=McpClientConfig.as_form(),
            llm=LLMConfig.as_form(),
            system_prompt=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.system_prompt.label"),
                help=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.system_prompt.help"),
                input_type="textarea",
                rows=3,
            ),
            max_iterations=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.max_iterations.label"),
                help=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.max_iterations.help"),
                min=1,
                max=100,
                step=1,
            ),
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.config.number_of_input_tokens.help"),
                min=1000,
                max=200000,
                step=1000,
            ),
        )
