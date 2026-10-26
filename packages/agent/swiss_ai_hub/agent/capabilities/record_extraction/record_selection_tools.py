from typing import Annotated

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.generative_ai import (
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelector,
    KnowledgeDocumentSummary,
)

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_sample import SAMPLE_ABOVE_DOCUMENTS
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

SELECT_KNOWLEDGE_DOCUMENTS_TOOL = "select_knowledge_documents"
_SAMPLE_PATHS = 10


class RecordSelectionTools(BaseToolSpec):
    """Lets the model settle which documents a table is extracted from, and see how many that is, before anything
    is extracted.

    Stateless: a call resolves the selection and reports it. A blueprint that extracts once the loop is done re-resolves
    the last call's arguments itself; in a loop that offers the extraction as a tool, the call is the preview the model
    checks before it extracts, so the user approves an extraction whose size the model already knows.
    """

    spec_functions = [SELECT_KNOWLEDGE_DOCUMENTS_TOOL]

    def __init__(self, context: ToolContext) -> None:
        self.context = context
        config = context.agent_config
        if not isinstance(config, RecordExtractionFields) or not config.knowledge_documents.enabled:
            self.spec_functions = []

    @ToolOptions.of(
        label=AgentLocaleString.from_i18n_path("agent.record_extraction.tools.select.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.record_extraction.tools.select.approval"),
    )
    async def select_knowledge_documents(
        self,
        any_of: Annotated[list[KnowledgeDocumentCriteria], ExtractRecordsArguments.model_fields["any_of"].description],
        fields: Annotated[str, ExtractRecordsArguments.model_fields["fields"].description],
        instructions: Annotated[str | None, ExtractRecordsArguments.model_fields["instructions"].description] = None,
        row_terms: Annotated[str | None, ExtractRecordsArguments.model_fields["row_terms"].description] = None,
        document_terms: Annotated[
            str | None, ExtractRecordsArguments.model_fields["document_terms"].description
        ] = None,
    ) -> str:
        """Settles which knowledge documents a table is extracted from, and which columns and rows it holds, and
        reports how many documents that is with example paths. Call it once you know the documents, and again with
        narrower or broader conditions when the count or the examples are wrong. A condition on the rows (an amount,
        a cap, a percentage) goes into instructions: the extraction applies it to every row, so select every
        document that may hold such rows instead of checking the condition yourself."""
        config = self.context.agent_config
        if not isinstance(config, RecordExtractionFields):
            raise TypeError(f"{type(config).__name__} lacks RecordExtractionFields")
        arguments = ExtractRecordsArguments.model_validate(
            {
                "any_of": any_of,
                "fields": fields,
                "instructions": instructions,
                "row_terms": row_terms,
                "document_terms": document_terms,
            }
        )
        scope = await KnowledgeDocumentScope.for_tool(self.context)
        settings = config.record_extraction
        selected = await KnowledgeDocumentSelector.resolve(
            scope.pairs(), arguments.selection, settings.max_documents_total, scope.restricting_glob
        )
        return self._report(selected.documents, selected.truncated, settings, arguments)

    @staticmethod
    def _report(
        documents: list[KnowledgeDocumentSummary],
        truncated: bool,
        settings: RecordExtractionConfig,
        arguments: ExtractRecordsArguments,
    ) -> str:
        if not documents:
            return (
                "No document meets these conditions, so nothing would be extracted. Check the listing and search "
                "results and select again with broader conditions, or tell the user nothing matches."
            )
        examples = "\n".join(f"- {document.path}" for document in documents[:_SAMPLE_PATHS])
        rows = f" Rows: {arguments.instructions}." if arguments.instructions else ""
        return (
            f"Selected documents: {RecordSelectionTools._count(documents, truncated, settings)} Columns: "
            f"{arguments.fields}.{rows} Examples:\n{examples}\n"
            "If these are the documents the user asked about, you are done selecting: do not call "
            "select_knowledge_documents again with the same conditions, and do not narrow them only to make the "
            "selection smaller; the user decides that. Select again only with different conditions, when these "
            "documents are wrong."
        )

    @staticmethod
    def _count(documents: list[KnowledgeDocumentSummary], truncated: bool, settings: RecordExtractionConfig) -> str:
        if truncated:
            return (
                f"more than {len(documents)}, more than this profile extracts; the user will be shown a sample and "
                "asked to narrow the request."
            )
        minutes = ExtractionEstimate.minutes(documents, settings.max_parallel_extractions)
        if len(documents) <= SAMPLE_ABOVE_DOCUMENTS:
            return f"{len(documents)}, extracted in one answer (about {minutes} minutes)."
        return (
            f"{len(documents)} (about {minutes} minutes). Do not ask the user yourself: the extraction shows a "
            "sample first and asks whether to extract them all or to narrow the request. When you have the "
            "extract_records tool, call it now."
        )
