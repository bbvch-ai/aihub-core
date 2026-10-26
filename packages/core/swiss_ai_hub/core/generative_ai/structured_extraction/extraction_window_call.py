import asyncio
from contextlib import nullcontext
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel

from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import RecordValue
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema


class ExtractionWindowCall:
    """One document's windows, each extracted by one model call, so the windows can run side by side.

    Each window is sent with the document's opening rather than with what earlier windows yielded, so the calls are
    independent and their order does not change the records. A malformed answer comes back as the `ValueError` it
    raised, for the extractor to fail the document with; infrastructure errors raise.
    """

    def __init__(
        self,
        llm: LLM,
        records_model: type[BaseModel],
        prompt: RichPromptTemplate,
        prompt_args: dict[str, Any],
        windows: list[str],
        opening: str,
        limiter: asyncio.Semaphore | None,
    ) -> None:
        self.llm = llm
        self.records_model = records_model
        self.prompt = prompt
        self.prompt_args = prompt_args
        self.windows = windows
        self.opening = opening
        self.limiter = limiter

    async def records(self, position: int) -> list[dict[str, RecordValue]] | ValueError:
        """Records of one window, without the all-null ones strict mode lets a model emit for "nothing here"."""
        window_args = {
            **self.prompt_args,
            "text": self.windows[position],
            "position": position + 1,
            "total": len(self.windows),
            "opening": self.opening if position > 0 else "",
        }
        async with self.limiter or nullcontext():
            try:
                result = await self.llm.astructured_predict(self.records_model, self.prompt, **window_args)
            except ValueError as malformed_output:
                return malformed_output
        records = [record.model_dump() for record in result.records]
        return [
            record
            for record in records
            if any(value is not None for name, value in record.items() if name != RecordSchema.MATCH_FIELD)
        ]
