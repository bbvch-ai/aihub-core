from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class LLMWrappingAgentConfig(MemoryFields, AttachedFilesFields, ConversationFields, AgentConfig):
    """
    Configuration for LLMWrappingAgent: the capability mixins plus a mandatory system prompt.

    Supports duality pattern for form rendering and data validation.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput,
        Field(description="System prompt that sets the agent's behaviour for the wrapped LLM."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode LLMWrappingAgentConfig."""
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            system_prompt=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.config.system_prompt.label"),
                help=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.config.system_prompt.help"),
                input_type="textarea",
                rows=3,
            ),
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
            **cls.attached_files_form_elements(),
        )
