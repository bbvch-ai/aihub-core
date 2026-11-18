import asyncio
from contextlib import nullcontext
from typing import Any

from llama_index.core.llms import LLM
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel

from swiss_ai_hub.core.generative_ai.structured_extraction.document_match import DocumentMatch
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
        judged_model: type[BaseModel] | None = None,
    ) -> None:
        self.llm = llm
        self.records_model = records_model
        self.prompt = prompt
        self.prompt_args = prompt_args
        self.windows = windows
        self.opening = opening
        self.limiter = limiter
        self.judged_model = judged_model

    async def records(self, position: int) -> list[dict[str, RecordValue]] | ValueError:
        """Records of one window, without the all-null ones strict mode lets a model emit for "nothing here"."""
        result = await self._predict(self.records_model, self._window_args(position, judging=False))
        if isinstance(result, ValueError):
            return result
        return self._kept(result.records)

    async def judged(self) -> tuple[DocumentMatch, list[dict[str, RecordValue]]] | ValueError:
        """The first window's verdict on the document condition, with its records.

        Only the first window is judged: the start of a document is where its supplier, parties and date stand.
        """
        if self.judged_model is None:
            raise ValueError("A window can only be judged with a model that carries a document match.")
        result = await self._predict(self.judged_model, self._window_args(0, judging=True))
        if isinstance(result, ValueError):
            return result
        return result.document_match, self._kept(result.records)

    async def _predict(self, model: type[BaseModel], window_args: dict[str, Any]) -> Any | ValueError:
        async with self.limiter or nullcontext():
            try:
                return await self.llm.astructured_predict(model, self.prompt, **window_args)
            except ValueError as malformed_output:
                return malformed_output

    def _window_args(self, position: int, judging: bool) -> dict[str, Any]:
        """Only a judged call sees the document condition, so the other windows extract exactly as without one."""
        return {
            **self.prompt_args,
            "document_condition": self.prompt_args.get("document_condition", "") if judging else "",
            "text": self.windows[position],
            "position": position + 1,
            "total": len(self.windows),
            "opening": self.opening if position > 0 else "",
        }

    @staticmethod
    def _kept(records: list[BaseModel]) -> list[dict[str, RecordValue]]:
        dumped = [record.model_dump() for record in records]
        return [
            record
            for record in dumped
            if any(value is not None for name, value in record.items() if name != RecordSchema.MATCH_FIELD)
        ]
