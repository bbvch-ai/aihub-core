from swiss_ai_hub.core.events.agent import ExtractRecordsEvent
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_notices import ExtractionNotices
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop


class SelectedExtraction:
    """The extraction of the documents a discovery search settled on, with the notices its search left behind."""

    @staticmethod
    def of(
        selection: ExtractRecordsArguments,
        scope: KnowledgeDocumentRunScope,
        finished: ToolLoop.Finished,
        by_location: bool,
        t: LocaleHandler,
        calculation: str | None = None,
    ) -> ExtractRecordsEvent:
        return RecordExtraction.extract(
            selection.selection,
            selection.fields,
            scope.pairs(),
            selection.instructions,
            selection.row_terms,
            notices=[
                *ExtractionNotices.for_calculation(calculation, t),
                *ExtractionNotices.for_table(scope, finished.stopped_early, t, by_location),
            ],
            cut_short=finished.stopped_early and not by_location,
            document_terms=selection.document_terms,
        )
