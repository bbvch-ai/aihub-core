from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber, LocaleInput
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class McpReactAgentConfig(MemoryFields, ConversationFields, AgentConfig):
    """Configuration for the MCP ReAct Agent: the capability mixins plus the MCP server and the loop bound."""

    mcp: Annotated[
        McpClientConfig,
        Field(description="MCP server connection configuration."),
    ]
    max_iterations: Annotated[
        int | InputNumber,
        Field(default=10, description="Maximum number of reasoning iterations before graceful termination."),
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
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
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
        )
