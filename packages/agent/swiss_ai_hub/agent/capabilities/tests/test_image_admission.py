"""The images a turn may send the main model: held to the profile's toggle and the model's curated `max_images`."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock
from swiss_ai_hub.core.events.agent import (
    ConversationContextualizedEvent,
    NotAMetaQuestionEvent,
    RefusalReason,
    RefusalStopEvent,
)
from swiss_ai_hub.core.generative_ai import ImageBudget, LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation


def _config(accept_images: bool = True) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="image-test",
        name=LocaleString(en="Images"),
        description=LocaleString(en="Image fixture"),
        system_prompt=LocaleString(en="You are helpful."),
        llm=LLMConfig(model_name="text-generation/vision", default_parameter=LLMParameter(accept_images=accept_images)),
    )


def _turn(text: str, images: int = 0) -> ChatMessage:
    blocks = [TextBlock(text=text), *(ImageBlock(url=f"https://example.test/{text}-{i}.png") for i in range(images))]
    return ChatMessage(role=MessageRole.USER, blocks=blocks)


def _model(**model_info: object):
    return patch.object(LLMConfig, "get_model_info", return_value={"model_info": model_info})


async def _derive(history: list[ChatMessage], config: LLMWrappingAgentConfig):
    return await Conversation.derive_query_step(
        LLMWrappingAgent(),
        request=Conversation.contextualize(history=history),
        _cleared=NotAMetaQuestionEvent(reasoning=""),
        conversation=config,
        displayer=AsyncMock(),
        t=MagicMock(side_effect=lambda key, **_: key),
    )


@pytest.mark.asyncio
async def test_a_turn_without_images_never_asks_for_the_model():
    with patch.object(LLMConfig, "get_model_info") as get_model_info:
        events = await _derive([_turn("hello")], _config())

    assert isinstance(events[0], ConversationContextualizedEvent)
    get_model_info.assert_not_called()


@pytest.mark.asyncio
async def test_more_images_than_the_model_takes_are_refused():
    with _model(supports_vision=True, max_images=2):
        stop = await _derive([_turn("look", images=3)], _config())

    assert isinstance(stop, RefusalStopEvent)
    assert stop.reason == RefusalReason.TOO_MANY_IMAGES


@pytest.mark.asyncio
async def test_earlier_images_give_way_to_the_limit_without_a_refusal():
    with _model(supports_vision=True, max_images=2):
        events = await _derive([_turn("before", images=2), _turn("now", images=2)], _config())

    contextualized = events[0]
    assert isinstance(contextualized, ConversationContextualizedEvent)
    assert ImageBudget.count(contextualized.history) == 2
    assert ImageBudget.count(contextualized.history[-1:]) == 2


@pytest.mark.asyncio
async def test_images_are_refused_when_the_profile_does_not_accept_them():
    with _model(supports_vision=True):
        stop = await _derive([_turn("look", images=1)], _config(accept_images=False))

    assert isinstance(stop, RefusalStopEvent)
    assert stop.reason == RefusalReason.IMAGES_NOT_ACCEPTED


@pytest.mark.asyncio
async def test_images_are_refused_for_a_model_that_declares_no_vision():
    with _model(supports_vision=False):
        stop = await _derive([_turn("look", images=1)], _config())

    assert stop.reason == RefusalReason.IMAGES_NOT_ACCEPTED


@pytest.mark.asyncio
async def test_earlier_images_are_dropped_silently_when_images_are_not_accepted():
    with _model(supports_vision=False):
        events = await _derive([_turn("before", images=1), _turn("now")], _config())

    assert ImageBudget.count(events[0].history) == 0
    assert events[0].history[-1].content == "now"


@pytest.mark.asyncio
async def test_a_model_without_a_curated_limit_receives_every_image():
    with _model():
        events = await _derive([_turn("look", images=12)], _config())

    assert ImageBudget.count(events[0].history) == 12
