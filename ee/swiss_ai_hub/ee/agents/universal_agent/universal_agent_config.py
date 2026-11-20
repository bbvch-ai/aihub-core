from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.agent.capabilities import (
    AttachedFilesFields,
    ConversationFields,
    KnowledgeFields,
    KnowledgeToolFields,
    MemoryFields,
    RecordExtractionFields,
    ToolLoopFields,
    WebFetchFields,
)
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.ee.i18n.enterprise_locale_string import EnterpriseLocaleString


class UniversalAgentConfig(
    MemoryFields,
    AttachedFilesFields,
    RecordExtractionFields,
    KnowledgeToolFields,
    KnowledgeFields,
    WebFetchFields,
    ToolLoopFields,
    ConversationFields,
    AgentConfig,
):
    """
    Configuration for UniversalAgent: the capabilities it may use as tools, the loop's limits (published by the runner
    with the blueprint's tools as options), and instructions added to its own. The document tools and table
    extraction stay off until a profile switches them on, so a profile saved before they existed keeps its tools.
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
                label=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.config.instructions.label"),
                help=EnterpriseLocaleString.from_i18n_path("agent.universal_agent.config.instructions.help"),
                input_type="textarea",
                rows=4,
            ),
            **cls.conversation_form_elements(),
            **cls.memory_form_elements(),
            **cls.attached_files_form_elements(),
            **cls.knowledge_form_elements(),
            **cls.knowledge_tool_form_elements(),
            **cls.web_fetch_form_elements(),
            **cls.knowledge_document_form_elements(),
            **cls.record_extraction_form_elements(),
        )
