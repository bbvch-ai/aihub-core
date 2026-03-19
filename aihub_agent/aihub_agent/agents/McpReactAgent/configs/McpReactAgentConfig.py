from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events.form import InputNumber, LocaleInput
from aihub_lib.nats.events.form.constraints import Gt
from pydantic import Field

from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


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
                label=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.help"),
                min=1000,
                max=200000,
                step=1000,
            ),
        )
