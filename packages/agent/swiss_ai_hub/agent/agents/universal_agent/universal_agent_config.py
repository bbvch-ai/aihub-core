from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class UniversalAgentConfig(
    MemoryFields,
    AttachedFilesFields,
    KnowledgeToolFields,
    KnowledgeFields,
    ToolLoopFields,
    ConversationFields,
    AgentConfig,
):
    """
    Configuration for UniversalAgent: the capabilities it may use as tools, the loop's limits (published by the runner
    with the blueprint's tools as options), and instructions added to its own.
    """

    instructions: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="Instructions for this profile, added after the agent's own on how to use its tools."),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            instructions=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.universal_agent.config.instructions.label"),
                help=AgentLocaleString.from_i18n_path("agent.universal_agent.config.instructions.help"),
                input_type="textarea",
                rows=4,
            ),
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
            **cls.attached_files_form_elements(),
            **cls.knowledge_form_elements(),
            **cls.knowledge_tool_form_elements(),
        )
