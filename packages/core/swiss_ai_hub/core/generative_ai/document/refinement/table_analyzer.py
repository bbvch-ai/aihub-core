import logging
from typing import TYPE_CHECKING

from llama_index.core import PromptTemplate

from swiss_ai_hub.core.generative_ai.document.refinement.models import (
    HeaderAnalysis,
    TableBoundary,
    TableSplitAnalysis,
)
from swiss_ai_hub.core.generative_ai.document.refinement.prompts import (
    HEADER_DETECTION_PROMPT,
    SPLIT_DETECTION_PROMPT,
)

if TYPE_CHECKING:
    from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class TableAnalyzer:
    def __init__(self, llm_config: "LLMConfig") -> None:
        self.llm, _ = llm_config.to_llama_index()

    def detect_splits(self, table_text: str) -> TableSplitAnalysis:
        prompt = PromptTemplate(SPLIT_DETECTION_PROMPT)
        analysis = self.llm.structured_predict(TableSplitAnalysis, prompt, table_text=table_text)

        logger.debug(f"Split analysis raw response: {analysis.tables}, reasoning={analysis.reasoning}")

        # Validate: sort by start_row and ensure the first starts at 0
        validated = sorted(
            [TableBoundary(start_row=max(0, t.start_row)) for t in analysis.tables],
            key=lambda t: t.start_row,
        )
        if not validated or validated[0].start_row != 0:
            validated = [TableBoundary(start_row=0)] + [t for t in validated if t.start_row > 0]

        return TableSplitAnalysis(tables=validated, reasoning=analysis.reasoning)

    def detect_headers(self, table_text: str) -> HeaderAnalysis:
        prompt = PromptTemplate(HEADER_DETECTION_PROMPT)
        analysis = self.llm.structured_predict(HeaderAnalysis, prompt, table_text=table_text)

        logger.debug(f"Header analysis raw response: {analysis.num_header_rows}, reasoning={analysis.reasoning}")

        # Validate: clamp to 1-4
        validated_num = max(1, min(4, analysis.num_header_rows))
        return HeaderAnalysis(num_header_rows=validated_num, reasoning=analysis.reasoning)
