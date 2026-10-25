from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import LocaleInput
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeExtractionAgentConfig(RecordExtractionFields, ToolLoopFields, AgentConfig):
    """
    Configuration for KnowledgeExtractionAgent: the collections and path glob it works on, the extraction model and
    limits, and the discovery loop's limits (published by the runner with the blueprint's tools as options).

    The profile is the hard boundary of what a request may touch, so the document tools are always on, `#` references
    only pick among the configured collections, and "every readable collection" is not offered.
    """

    instructions: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="Instructions for this profile, added after the agent's own on how to find documents."),
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
                label=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.config.instructions.label"),
                help=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.config.instructions.help"),
                input_type="textarea",
                rows=4,
            ),
            knowledge_tool=KnowledgeToolConfig(
                every_readable_collection=False, sources=[KnowledgeToolSource.as_form()]
            ),
            knowledge_documents=KnowledgeDocumentConfig(
                enabled=True,
                narrow_references=True,
                path_glob=KnowledgeDocumentConfig.path_glob_input(),
                semantic_search=KnowledgeDocumentConfig.semantic_search_input(),
            ),
            **cls.conversation_form_elements(),
            **cls.record_extraction_form_elements(),
        )
