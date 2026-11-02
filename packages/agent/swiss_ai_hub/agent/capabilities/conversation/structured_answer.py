import json
import logging
from typing import Any

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMEvent, LLMStopEvent, Message, ResponseSchema, ResponseSchemaViolation
from swiss_ai_hub.core.generative_ai import ReasoningFreeChat
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields

logger = logging.getLogger(__name__)


class StructuredAnswer:
    """
    The run's answer as the JSON the caller asked for, set on the stop event.

    The answering step already asked its model for the shape (`display_llm_stream(..., response_schema=...)`), so
    this mostly parses and validates. When the answer does not match, because the model lacks structured outputs,
    ignored them, or the blueprint never passed the schema, the model is asked once more with the schema and the
    validation error, from the same prompt. A second miss fails the run: a caller who asked for a shape must never
    receive prose in its place.
    """

    @staticmethod
    async def stop_for(
        answer: LLMEvent,
        schema: ResponseSchema,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> LLMStopEvent:
        """The stop event carrying the answer, its text replaced by the validated JSON."""
        try:
            structured = schema.validated(StructuredAnswer._text_of(answer))
        except ResponseSchemaViolation as violation:
            logger.info("Answer did not match the requested schema %s, correcting it once: %s", schema.name, violation)
            await displayer.display_thought(t("agent.thought.correcting_structured_answer"))
            structured = await StructuredAnswer._corrected(answer, schema, violation, conversation, displayer, t, user)
        return StructuredAnswer._stop_with(answer, structured)

    @staticmethod
    async def _corrected(
        answer: LLMEvent,
        schema: ResponseSchema,
        violation: ResponseSchemaViolation,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> dict[str, Any]:
        """Thinking is off for the call, as reasoning providers break JSON with it on."""
        messages = [
            *answer.chat_messages,
            ChatMessage(role=MessageRole.USER, content=StructuredAnswer._instruction(schema, violation, t)),
        ]
        async with conversation.llm.cost_reporting_llm(displayer, user=user) as llm:
            kwargs = {"response_format": schema.response_format()} if llm.should_use_structured_outputs else {}
            response = await ReasoningFreeChat.achat(llm, messages, **kwargs)
        return schema.validated(response.message.content or "")

    @staticmethod
    def _instruction(schema: ResponseSchema, violation: ResponseSchemaViolation, t: LocaleHandler) -> str:
        instruction = t("agent.conversation.prompt.correct_structured_answer", violation=str(violation))
        if schema.json_schema is None:
            return instruction
        shape = t("agent.conversation.prompt.structured_answer_schema", schema=json.dumps(schema.json_schema))
        return f"{instruction}\n{shape}"

    @staticmethod
    def _text_of(answer: LLMEvent) -> str:
        return answer.output_messages[-1].content if answer.output_messages else ""

    @staticmethod
    def _stop_with(answer: LLMEvent, structured: dict[str, Any]) -> LLMStopEvent:
        stop = LLMStopEvent.model_validate(answer.model_dump(exclude={"event_id", "created_at"}))
        stop.output_messages = [
            Message.from_llama_index(
                ChatMessage(role=MessageRole.ASSISTANT, content=json.dumps(structured, ensure_ascii=False))
            )
        ]
        stop.structured_output = structured
        return stop
