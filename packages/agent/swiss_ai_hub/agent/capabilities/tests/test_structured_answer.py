import json
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ContextualizeConversationEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    NotAMetaQuestionEvent,
    RefusalReason,
    RefusalStopEvent,
    ResponseSchema,
    ResponseSchemaViolation,
)
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent import FewShotAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.mcp_react_agent.mcp_react_agent import McpReactAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.conversation.structured_answer import StructuredAnswer
from swiss_ai_hub.agent.capabilities.requested_response_schema import RequestedResponseSchema
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

CONVERSATION_MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation"
T = AgentLocaleHandler("en")
THINKING_OFF = {"extra_body": {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}}

INVOICE = ResponseSchema(
    name="invoice",
    json_schema={
        "type": "object",
        "properties": {"issuer": {"type": "string"}, "total": {"type": ["number", "null"]}},
        "required": ["issuer", "total"],
        "additionalProperties": False,
    },
    strict=True,
)


class _RunContext:
    def __init__(self, values: dict | None = None) -> None:
        self.values = dict(values or {})

    async def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)


def _requesting(schema: ResponseSchema | None) -> _RunContext:
    """The run context as the dispatcher fills it from the start event."""
    message = UserMessageEvent(user=fake_user(), messages=[], response_schema=schema)
    return _RunContext(message.to_context_dict())


def _answer(text: str) -> LLMEvent:
    return LLMEvent(
        input_messages=[Message.from_string(role="user", content="Read the invoice.")],
        output_messages=[Message.from_string(role="assistant", content=text)],
        chat_model_name="text-generation/test",
    )


def _conversation(*replies: str, structured_outputs: bool = True) -> MagicMock:
    achat = AsyncMock(
        side_effect=[MagicMock(message=ChatMessage(role=MessageRole.ASSISTANT, content=reply)) for reply in replies]
    )

    @asynccontextmanager
    async def cost_reporting_llm(*_args: Any, **_kwargs: Any):
        yield MagicMock(achat=achat, should_use_structured_outputs=structured_outputs)

    conversation = MagicMock()
    conversation.llm.cost_reporting_llm = cost_reporting_llm
    conversation.achat = achat
    return conversation


def _displayer() -> MagicMock:
    return MagicMock(display_thought=AsyncMock())


async def _stop_for(answer: LLMEvent, conversation: MagicMock) -> LLMStopEvent:
    return await StructuredAnswer.stop_for(answer, INVOICE, conversation, _displayer(), T, user=None)


class TestStructuredAnswer:
    @pytest.mark.asyncio
    async def test_a_matching_answer_ends_the_run_with_its_parsed_json(self):
        conversation = _conversation()

        stop = await _stop_for(_answer('{"issuer": "ACME AG", "total": 120.5}'), conversation)

        assert stop.structured_output == {"issuer": "ACME AG", "total": 120.5}
        assert json.loads(stop.output_messages[-1].content) == stop.structured_output
        assert stop.input_messages[0].content == "Read the invoice."
        conversation.achat.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_prose_answer_is_corrected_once_from_the_same_prompt_with_the_schema(self):
        conversation = _conversation('{"issuer": "ACME AG", "total": null}')

        stop = await _stop_for(_answer("The invoice is from ACME AG."), conversation)

        assert stop.structured_output == {"issuer": "ACME AG", "total": None}
        sent = conversation.achat.await_args.args[0]
        assert [message.content for message in sent[:2]] == ["Read the invoice.", "The invoice is from ACME AG."]
        assert '"required": ["issuer", "total"]' in sent[-1].content
        assert conversation.achat.await_args.kwargs == {**THINKING_OFF, "response_format": INVOICE.response_format()}

    @pytest.mark.asyncio
    async def test_a_model_without_structured_outputs_is_corrected_from_the_prompt_alone(self):
        conversation = _conversation('{"issuer": "ACME AG", "total": 3}', structured_outputs=False)

        await _stop_for(_answer("ACME AG, 3 francs"), conversation)

        assert conversation.achat.await_args.kwargs == THINKING_OFF

    @pytest.mark.asyncio
    async def test_a_second_miss_fails_the_run_instead_of_returning_prose(self):
        conversation = _conversation('{"issuer": "ACME AG"}')

        with pytest.raises(ResponseSchemaViolation, match="'total' is a required property"):
            await _stop_for(_answer("ACME AG"), conversation)


class TestConversationWithASchema:
    @pytest.mark.asyncio
    async def test_completion_validates_instead_of_generating_follow_ups(self):
        with patch(f"{CONVERSATION_MODULE}.generate_follow_up_questions", new=AsyncMock()) as follow_ups:
            stop = await Conversation.complete_conversation_step(
                LLMWrappingAgent(),
                request=CompleteConversationEvent(answer=_answer('{"issuer": "ACME AG", "total": 1}')),
                conversation=_conversation(),
                run_context=_requesting(INVOICE),
                displayer=_displayer(),
                t=T,
            )

        follow_ups.assert_not_awaited()
        assert stop.structured_output == {"issuer": "ACME AG", "total": 1}

    @pytest.mark.asyncio
    async def test_a_refusal_handed_to_the_completion_ends_the_run_as_a_refusal(self):
        refusal = RefusalStopEvent(reason=RefusalReason.INPUT_TOO_LARGE)

        with patch(f"{CONVERSATION_MODULE}.generate_follow_up_questions", new=AsyncMock()):
            stop = await Conversation.complete_conversation_step(
                LLMWrappingAgent(),
                request=Conversation.complete(answer=_answer("Too long."), stop=refusal),
                conversation=_conversation(),
                run_context=_requesting(INVOICE),
                displayer=_displayer(),
                t=T,
            )

        assert stop is refusal

    @pytest.mark.asyncio
    async def test_a_supplied_stop_is_the_answer_validated_not_the_summary_beside_it(self):
        conversation = _conversation('{"issuer": "ACME AG", "total": 12}')
        summary = _answer("One invoice found.")
        table = LLMStopEvent(
            input_messages=summary.input_messages,
            output_messages=[Message.from_string(role="assistant", content="| issuer | total |\n| ACME AG | 12 |")],
        )

        with patch(f"{CONVERSATION_MODULE}.generate_follow_up_questions", new=AsyncMock()) as follow_ups:
            stop = await Conversation.complete_conversation_step(
                LLMWrappingAgent(),
                request=Conversation.complete(answer=summary, stop=table),
                conversation=conversation,
                run_context=_requesting(INVOICE),
                displayer=_displayer(),
                t=T,
            )

        follow_ups.assert_not_awaited()
        assert stop.structured_output == {"issuer": "ACME AG", "total": 12}
        assert "| ACME AG | 12 |" in conversation.achat.await_args.args[0][1].content

    @pytest.mark.asyncio
    async def test_a_message_asking_for_a_shape_is_not_inspected_for_a_meta_question(self):
        with patch(f"{CONVERSATION_MODULE}.do_detect_meta_question", new=AsyncMock()) as detect:
            cleared = await Conversation.inspect_message_step(
                LLMWrappingAgent(),
                request=ContextualizeConversationEvent(history=[], user_query="Who are you? Answer as JSON."),
                conversation=MagicMock(),
                run_context=_requesting(INVOICE),
                displayer=_displayer(),
                t=T,
            )

        detect.assert_not_awaited()
        assert isinstance(cleared, NotAMetaQuestionEvent)


class TestSupport:
    @pytest.mark.parametrize("blueprint", [LLMWrappingAgent, FewShotAgent, McpReactAgent, UniversalAgent])
    def test_blueprints_completing_on_an_llm_stop_support_a_response_schema(self, blueprint):
        assert blueprint.supports_response_schema()

    def test_rag_ending_on_its_own_stop_events_does_not(self):
        assert not RAGAgent.supports_response_schema()

    @pytest.mark.asyncio
    async def test_a_blueprint_without_support_never_sees_the_request(self):
        assert await RequestedResponseSchema.of(_requesting(INVOICE), RAGAgent) is None
        assert await RequestedResponseSchema.of(_requesting(INVOICE), LLMWrappingAgent) == INVOICE
        assert await RequestedResponseSchema.of(_requesting(None), LLMWrappingAgent) is None


class TestPrompts:
    @pytest.mark.parametrize("locale", ["de", "fr", "it"])
    def test_every_locale_translates_the_correction(self, locale):
        for key in ("correct_structured_answer", "structured_answer_schema"):
            path = f"agent.conversation.prompt.{key}"
            translated = AgentLocaleHandler(locale)(path, violation="v", schema="s")
            assert translated != T(path, violation="v", schema="s")
