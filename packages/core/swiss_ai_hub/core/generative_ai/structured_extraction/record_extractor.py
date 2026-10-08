import logging
from typing import Annotated, Any

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.structured_extraction.document_extraction_result import DocumentExtractionResult
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import RecordValue
from swiss_ai_hub.core.generative_ai.structured_extraction.record_merger import RecordMerger
from swiss_ai_hub.core.generative_ai.structured_extraction.record_provenance import RecordProvenance
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.generative_ai.structured_extraction.text_windows import TextWindows
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)

# The tokenizer behind `LLMConfig.token_counter` is tiktoken, not the served model's. Same factor and reasoning as
# `BUDGET_SAFETY_FACTOR` in the agent package's `imap/token_budget`.
INPUT_BUDGET_SAFETY_FACTOR = 0.85

# Records come back as JSON, which repeats every field name per record: a dense invoice table measures up to about
# twice its own text. A window larger than half the output budget could make the model run out mid-list, which
# strict mode turns into unterminated JSON rather than a shorter answer.
OUTPUT_TOKENS_PER_WINDOW_TOKEN = 2

# Wide enough to hold any single table row or paragraph whole, so a record cut at one boundary is complete in the
# neighbouring window.
WINDOW_OVERLAP_RATIO = 0.1

# Room for a header (invoice number, supplier, contract parties) that every later window is shown, so a value stated
# once at the top still reaches records far below it.
DOCUMENT_OPENING_TOKENS = 512

MIN_WINDOW_TOKENS = 256

MAX_FAILURE_REASON_CHARACTERS = 300


class RecordExtractor:
    """Extracts every record matching a schema from one document, however long the document is."""

    @staticmethod
    @trace_fn
    async def extract(
        schema: Annotated[RecordSchema, "Fields every record has"],
        document: Annotated[KnowledgeDocument, "The whole document, as `KnowledgeDocumentReader` loads it"],
        llm: Annotated[LLM, "Model that extracts; costs are counted by its own callback manager"],
        llm_config: Annotated[LLMConfig, "Config of `llm`, for its context window, output limit and tokenizer"],
        t: LocaleHandler,
        instructions: Annotated[str | None, "Which records to keep, e.g. 'only hardware positions'"] = None,
    ) -> DocumentExtractionResult:
        """Malformed model output becomes a failed result for this document instead of a raise.

        A deliberate departure from fail-fast: a caller extracts from many documents, and one document a model
        cannot handle must not cost the records of the others. A document fails as a whole, never with the records of
        the windows that worked, because a partial list would read as complete. Infrastructure errors still raise.
        """
        RecordExtractor._require_whole(document)
        provenance = RecordProvenance.from_summary(document.summary)
        prompt = RichPromptTemplate(t("lib.prompt.structured_extraction.extraction_prompt"))
        prompt_args = RecordExtractor._prompt_args(schema, document, instructions)
        window_tokens = RecordExtractor._window_tokens(prompt, prompt_args, llm_config)
        windows = TextWindows.split(
            document.text, window_tokens, int(window_tokens * WINDOW_OVERLAP_RATIO), llm_config.token_counter
        )
        opening = RecordExtractor._opening(document.text, window_tokens, llm_config) if len(windows) > 1 else ""
        records_model = schema.to_records_model()

        per_window = []
        for position, window in enumerate(windows, start=1):
            window_args = {
                **prompt_args,
                "text": window,
                "position": position,
                "total": len(windows),
                "opening": opening if position > 1 else "",
            }
            try:
                per_window.append(await RecordExtractor._extract_window(llm, records_model, prompt, window_args))
            except ValueError as malformed_output:
                logger.warning("[extract] %s: excerpt %d of %d failed", provenance.path, position, len(windows))
                reason = f"Excerpt {position} of {len(windows)}: {type(malformed_output).__name__}: {malformed_output}"
                return DocumentExtractionResult.failed_with(
                    provenance, reason[:MAX_FAILURE_REASON_CHARACTERS], len(windows)
                )

        return DocumentExtractionResult.succeeded(provenance, RecordMerger.merge(per_window), len(windows))

    @staticmethod
    async def _extract_window(
        llm: LLM, records_model: type[BaseModel], prompt: RichPromptTemplate, window_args: dict[str, Any]
    ) -> list[dict[str, RecordValue]]:
        """Records of one window, without the all-null ones strict mode lets a model emit for "nothing here"."""
        result = await llm.astructured_predict(records_model, prompt, **window_args)
        records = [record.model_dump() for record in result.records]
        return [record for record in records if any(value is not None for value in record.values())]

    @staticmethod
    def _prompt_args(schema: RecordSchema, document: KnowledgeDocument, instructions: str | None) -> dict[str, Any]:
        return {
            "fields": schema.fields,
            "field_names": ", ".join(schema.field_names),
            "instructions": instructions or "",
            "title": document.summary.title,
        }

    @staticmethod
    def _window_tokens(prompt: RichPromptTemplate, prompt_args: dict[str, Any], llm_config: LLMConfig) -> int:
        """The largest window that leaves room for the prompt around it and for the records it can yield.

        Raises when the model is too small to extract with at all, which is a configuration error, not a document's.
        """
        model_info = llm_config.get_model_info()["model_info"]
        rendered = prompt.format(**prompt_args, text="", position=1, total=1, opening="")
        prompt_tokens = len(llm_config.token_counter(rendered))
        input_room = (
            int(model_info["max_input_tokens"] * INPUT_BUDGET_SAFETY_FACTOR) - prompt_tokens - DOCUMENT_OPENING_TOKENS
        )
        output_room = model_info["max_output_tokens"] // OUTPUT_TOKENS_PER_WINDOW_TOKEN
        window_tokens = min(input_room, output_room)
        if window_tokens < MIN_WINDOW_TOKENS:
            raise ValueError(
                f"{llm_config.model_name} leaves {window_tokens} tokens per document window, fewer than the "
                f"{MIN_WINDOW_TOKENS} extraction needs. Choose a model with a larger context window or output limit."
            )
        return window_tokens

    @staticmethod
    def _opening(text: str, window_tokens: int, llm_config: LLMConfig) -> str:
        """The start of the document, for values every record shares but only the first window states.

        Capped at half a window so it ends well before the second window begins: a record inside it is then extracted
        from the first window only, and the opening never yields a copy the merger would have to catch.
        """
        opening_tokens = min(DOCUMENT_OPENING_TOKENS, window_tokens // 2)
        return TextWindows.split(text, opening_tokens, 0, llm_config.token_counter)[0]

    @staticmethod
    def _require_whole(document: KnowledgeDocument) -> None:
        """A character range would be extracted as if it were the document, silently losing every record outside it."""
        if document.start != 0 or document.end != document.text_length:
            raise ValueError(
                f"{document.summary.path} was loaded as characters {document.start}-{document.end} of "
                f"{document.text_length}; extraction needs the whole document."
            )
