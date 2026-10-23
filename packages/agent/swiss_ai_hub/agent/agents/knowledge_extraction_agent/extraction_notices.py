from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import SELECT_KNOWLEDGE_DOCUMENTS_TOOL


class ExtractionNotices:
    """What the answer says about the discovery itself: why there is no table, or what the table may be missing."""

    @staticmethod
    def for_table(
        scope: KnowledgeDocumentRunScope, stopped_early: bool, t: LocaleHandler, by_location: bool = False
    ) -> list[str]:
        """`by_location`: the search stopped and the documents were selected by folder, so none are missing."""
        notices = []
        if by_location:
            notices.append(t("agent.knowledge_extraction_agent.messages.selected_by_location"))
        elif stopped_early:
            notices.append(t("agent.knowledge_extraction_agent.messages.stopped_early"))
        if scope.ignored:
            ignored = ", ".join(f"{reference.database}/{reference.namespace}" for reference in scope.ignored)
            notices.append(t("agent.knowledge_extraction_agent.messages.ignored_references", collections=ignored))
        return notices

    @staticmethod
    def without_selection(agent_config: KnowledgeExtractionAgentConfig, stopped_early: bool, t: LocaleHandler) -> str:
        if agent_config.tool_loop.is_disabled(SELECT_KNOWLEDGE_DOCUMENTS_TOOL):
            return t("agent.knowledge_extraction_agent.messages.select_disabled")
        if stopped_early:
            return t("agent.knowledge_extraction_agent.messages.stopped_before_selecting")
        return t("agent.knowledge_extraction_agent.messages.no_selection")
