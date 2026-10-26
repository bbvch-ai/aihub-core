from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, LLMStopEvent, Message, RecordsExtractedEvent

from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable

ANSWER_MODEL_NAME = "KnowledgeExtractionAgent"
# Streamed in parts so no single chunk event comes near the message broker's limit, however large the table: at most
# this many rows, and at most this many bytes as events serialize them (cells can hold whole clauses).
ROWS_PER_CHUNK = 50
CHUNK_BYTES = 100_000


class ExtractionAnswer:
    """Ends a run with the table, or with a notice when there is no table to show.

    The table is the answer, so it is streamed as written rather than through a model. Follow-up questions are grounded
    on the summary only: the whole table would crowd the task model's prompt and say nothing a summary does not.
    """

    @staticmethod
    async def table(
        extracted: RecordsExtractedEvent, query: str, displayer: EventDisplayer
    ) -> Conversation.CompleteRequest:
        parts = ExtractionAnswer._parts(extracted)
        for part in parts:
            await displayer.display_chunk(part, model_name=ANSWER_MODEL_NAME)
        return ExtractionAnswer._complete("".join(parts), extracted.summary, query)

    @staticmethod
    async def notice(text: str, query: str, displayer: EventDisplayer) -> Conversation.CompleteRequest:
        await displayer.display_chunk(text, model_name=ANSWER_MODEL_NAME)
        return ExtractionAnswer._complete(text, text, query)

    @staticmethod
    def _parts(extracted: RecordsExtractedEvent) -> list[str]:
        if not extracted.table:
            return [extracted.summary]
        parts: list[str] = []
        current: list[str] = []
        size = 0
        for line in extracted.table.split("\n"):
            line_bytes = ExtractionTable.serialized_bytes(line)
            if current and (len(current) >= ROWS_PER_CHUNK or size + line_bytes > CHUNK_BYTES):
                parts.append("\n".join(current) + "\n")
                current, size = [], 0
            current.append(line)
            size += line_bytes
        parts.append("\n".join(current) + "\n")
        return [*parts, f"\n{extracted.summary}"]

    @staticmethod
    def _complete(full: str, summary: str, query: str) -> Conversation.CompleteRequest:
        asked = [Message.from_string(role="user", content=query)]
        answer = LLMEvent(
            input_messages=asked,
            output_messages=[Message.from_string(role="assistant", content=summary, name=ANSWER_MODEL_NAME)],
        )
        stop = LLMStopEvent(
            input_messages=asked,
            output_messages=[Message.from_string(role="assistant", content=full, name=ANSWER_MODEL_NAME)],
        )
        return Conversation.complete(answer=answer, stop=stop)
