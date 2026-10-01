"""Which chat features a blueprint supports, and whether one counts as requested for a run.

A blueprint never declares its features: it supports exactly those of the capabilities its steps call. A requested
feature it does not support never counts as requested, whoever sent it.
"""

from typing import Any, ClassVar
from unittest.mock import AsyncMock

import pytest
from swiss_ai_hub.core.events.agent import ChatFeature, ContextualizeConversationEvent, UserMessageEvent
from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.catalog import CapabilityCatalog
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.workflow.decorators.step import step


class SearchWebEvent(ControlEvent):
    pass


class WebSearchLikeCapability(Capability):
    calls: ClassVar[dict[type[ControlEvent], tuple[type[ControlEvent], ...]]] = {SearchWebEvent: ()}
    chat_feature: ClassVar[ChatFeature | None] = ChatFeature.WEB_SEARCH


class SearchingAgent(Agent):
    @step()
    async def open_step(self, event: UserMessageEvent) -> SearchWebEvent:
        return SearchWebEvent()


class PlainAgent(Agent):
    @step()
    async def open_step(self, event: UserMessageEvent) -> ContextualizeConversationEvent:
        return Conversation.contextualize(history=event.messages, message=event)


@pytest.fixture(autouse=True)
def _catalog_with_web_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stub capability is not one the SDK ships, so the catalog is taught about it for these tests."""
    monkeypatch.setattr(CapabilityCatalog, "all", staticmethod(lambda: [Conversation, Memory, WebSearchLikeCapability]))


def _run_context(requested: list[str] | None) -> Any:
    run_context = AsyncMock()
    run_context.get.return_value = requested
    return run_context


class TestSupportedFeatures:
    def test_blueprint_supports_the_features_of_the_capabilities_it_calls(self) -> None:
        assert SearchingAgent.supported_features() == {ChatFeature.WEB_SEARCH}

    def test_blueprint_without_feature_capabilities_supports_none(self) -> None:
        assert PlainAgent.supported_features() == set()

    @pytest.mark.parametrize("blueprint", [RAGAgent, LLMWrappingAgent])
    def test_existing_blueprints_support_no_feature_yet(self, blueprint: type[Agent]) -> None:
        """Until a capability serves a feature, no agent shows an OpenWebUI toggle."""
        assert blueprint.supported_features() == set()


class TestRequestedFeatures:
    @pytest.mark.asyncio
    async def test_supported_feature_requested_for_the_run(self) -> None:
        run_context = _run_context(["web_search"])

        assert await RequestedFeatures.contains(ChatFeature.WEB_SEARCH, run_context, SearchingAgent)
        run_context.get.assert_awaited_once_with(RequestedFeatures.RUN_CONTEXT_KEY)

    @pytest.mark.asyncio
    async def test_feature_not_requested(self) -> None:
        assert not await RequestedFeatures.contains(ChatFeature.WEB_SEARCH, _run_context([]), SearchingAgent)

    @pytest.mark.asyncio
    async def test_run_without_requested_features(self) -> None:
        """Programmatic starts such as a RAGStartEvent carry no features at all."""
        assert not await RequestedFeatures.contains(ChatFeature.WEB_SEARCH, _run_context(None), SearchingAgent)

    @pytest.mark.asyncio
    async def test_unsupported_feature_never_counts_as_requested(self) -> None:
        """An API caller can send any feature; the blueprint's support is the ceiling."""
        run_context = _run_context(["code_interpreter"])

        assert not await RequestedFeatures.contains(ChatFeature.CODE_INTERPRETER, run_context, SearchingAgent)
        run_context.get.assert_not_awaited()
