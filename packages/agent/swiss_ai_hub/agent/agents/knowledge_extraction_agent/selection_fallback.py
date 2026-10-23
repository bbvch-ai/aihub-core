import json
import logging

from llama_index.core.prompts.rich import RichPromptTemplate
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ToolCallApprovedEvent, ToolResultEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_answer import SelectionFallbackAnswer
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments

logger = logging.getLogger(__name__)

# A selection is a handful of short entries; the cap bounds what a strict-mode stall can cost.
SELECTION_MAX_TOKENS = 1024
RESULT_CHARACTERS = 600


class SelectionFallback:
    """The selection a discovery loop's own searches point to, when the model ended without stating it.

    Some models answer in text instead of making the closing call to `select_knowledge_documents`, and a gathering
    loop drops that text, so the run would end without a table although the searches found the documents. Asking the
    same model once more, with structured output over what it searched and found, turns that work into a selection.
    """

    @staticmethod
    async def ask(
        query: str,
        calls: list[ToolCallApprovedEvent],
        results: list[ToolResultEvent],
        scope: KnowledgeDocumentRunScope,
        llm_config: LLMConfig,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
        stopped_early: bool = False,
    ) -> ExtractRecordsArguments | None:
        """The selection the searches point to. After a search stopped at its limit, only by folder and path: its hits
        are incomplete, and a condition on the rows is checked in every document by the extraction instead."""
        if not calls:
            return None
        prompt = RichPromptTemplate(t("agent.knowledge_extraction_agent.prompt.select_now"))
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
            deterministic = llm.model_copy(update={"temperature": 0.0, "max_tokens": SELECTION_MAX_TOKENS})
            try:
                answer = await deterministic.astructured_predict(
                    SelectionFallbackAnswer,
                    prompt,
                    request=query,
                    scope=scope.describe(),
                    transcript=SelectionFallback._transcript(calls, results),
                    stopped=stopped_early,
                )
            except ValueError:
                logger.warning("[knowledge-extraction] the model stated no usable selection")
                return None
        if answer.nothing_matches:
            return None
        return answer.as_arguments(by_location=stopped_early)

    @staticmethod
    def _transcript(calls: list[ToolCallApprovedEvent], results: list[ToolResultEvent]) -> str:
        by_call = {result.tool_call_id: result.content for result in results}
        unique = {call.tool_call_id: call for call in calls}.values()
        return "\n\n".join(
            f"{call.name}({json.dumps(call.arguments, ensure_ascii=False)}):\n"
            f"{by_call.get(call.tool_call_id, '')[:RESULT_CHARACTERS]}"
            for call in unique
        )
