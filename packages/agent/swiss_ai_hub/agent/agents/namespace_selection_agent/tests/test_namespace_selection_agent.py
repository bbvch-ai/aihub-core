"""Tests for NamespaceSelectionAgent.

These tests verify the NamespaceSelectionAgent components work correctly.
Note: Full integration tests require Redis, NATS, and MongoDB infrastructure.
"""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import NamespaceSelectionAgentConfig
from swiss_ai_hub.agent.agents.namespace_selection_agent.events import (
    DetermineNamespacesEvent,
    FollowUpQuestionHitl,
    NamespaceApprovalHitl,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.events.follow_up_question_hitl import (
    FollowUpQuestionRequestEvent,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.llm.namespace_decision import NamespaceDecision
from swiss_ai_hub.agent.agents.namespace_selection_agent.llm.predict_namespace_decision import (
    MAX_DECISION_TOKENS,
    predict_namespace_decision,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import NamespaceSelectionAgent
from swiss_ai_hub.agent.agents.namespace_selection_agent.utils import (
    format_approval_question,
    format_available_namespaces,
    format_conversation_history,
)


def _truncated_json_error() -> ValidationError:
    """The real error a whitespace-padded, unterminated structured response produces."""
    try:
        NamespaceDecision.model_validate_json('{\n  "follow_up_question": "Which source?"\n  \n  \n')
    except ValidationError as error:
        return error
    raise AssertionError("expected NamespaceDecision to reject unterminated JSON")


class _RecordingLLM:
    """Stand-in that records ``model_copy`` updates and replays queued structured-predict outcomes."""

    def __init__(self, outcomes: list[Any]):
        self.outcomes = list(outcomes)
        self.updates: list[dict[str, Any]] = []
        self.call_count = 0

    def model_copy(self, update: dict[str, Any]) -> "_RecordingLLM":
        self.updates.append(update)
        return self

    async def astructured_predict(self, _output_cls, _prompt, **_prompt_args) -> NamespaceDecision:
        self.call_count += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class TestNamespaceDecision:
    """Tests for NamespaceDecision model."""

    def test_decision_with_enough_info(self):
        """Test creating a decision when enough info is available."""
        decision = NamespaceDecision(
            has_enough_information=True,
            selected_namespaces={"bucket1": "ns1"},
            reasoning="User clearly mentioned topic X",
        )
        assert decision.has_enough_information is True
        assert decision.selected_namespaces == {"bucket1": "ns1"}
        assert decision.follow_up_question is None

    def test_decision_needs_more_info(self):
        """Test creating a decision when more info is needed."""
        decision = NamespaceDecision(
            has_enough_information=False,
            follow_up_question="What topic are you interested in?",
            reasoning="User query is too vague",
        )
        assert decision.has_enough_information is False
        assert decision.selected_namespaces is None
        assert decision.follow_up_question == "What topic are you interested in?"


class TestFormatting:
    """Tests for formatting functions."""

    def test_format_available_namespaces(self):
        """Test formatting namespaces for LLM prompt."""
        available = {"bucket1": ["ns1", "ns2"], "bucket2": ["ns3"]}
        result = format_available_namespaces(available)
        assert "bucket1" in result
        assert "ns1" in result
        assert "ns2" in result
        assert "bucket2" in result
        assert "ns3" in result

    def test_format_conversation_history(self):
        """Test formatting conversation history for LLM prompt."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = format_conversation_history(history)
        assert "USER: Hello" in result
        assert "ASSISTANT: Hi there" in result

    def test_format_approval_question(self):
        """Test formatting approval question with namespaces."""
        selected = {"bucket1": "ns1", "bucket2": "ns2"}
        template = LocaleString(en="Approve these?\n{namespaces}")
        t = MagicMock()
        t.extract = lambda x: x.en if hasattr(x, "en") else x
        result = format_approval_question(selected, template, t)
        assert "bucket1" in result
        assert "ns1" in result
        assert "bucket2" in result
        assert "ns2" in result


class TestEvents:
    """Tests for event definitions."""

    def test_determine_namespaces_event_creation(self):
        """Test creating a DetermineNamespacesEvent."""
        event = DetermineNamespacesEvent()
        assert event is not None

    def test_follow_up_question_hitl_invoke(self):
        """Test creating a FollowUpQuestionHitl request via invoke."""
        request = FollowUpQuestionHitl.invoke(
            question="What topic are you interested in?",
        )
        assert request.question == "What topic are you interested in?"

    def test_namespace_approval_hitl_invoke(self):
        """Test creating a NamespaceApprovalHitl request via invoke."""
        request = NamespaceApprovalHitl.invoke(
            question="Approve these namespaces?",
        )
        assert request.question == "Approve these namespaces?"


class TestFieldDescriptions:
    """Strict structured outputs mark every property required, so no description may invite omission."""

    def test_optional_fields_ask_for_null_not_omission(self):
        """A model that skips a required key can never reach a closing brace — see issue #142."""
        for field_name in ("selected_namespaces", "follow_up_question"):
            description = NamespaceDecision.model_fields[field_name].description
            assert "Only set if" not in description, f"{field_name} invites omission"
            assert "null" in description, f"{field_name} must ask for an explicit null"


class TestPredictNamespaceDecision:
    """Tests for the hardened namespace determination call."""

    @pytest.mark.asyncio
    async def test_caps_output_tokens_on_the_strict_path(self):
        """The cap bounds a whitespace runaway; a real decision needs far fewer tokens."""
        decision = NamespaceDecision(has_enough_information=True, selected_namespaces={"b": "n"}, reasoning="clear")
        llm = _RecordingLLM([decision])

        result = await predict_namespace_decision(
            llm=llm, prompt=MagicMock(), available_namespaces="ns", conversation_history="history"
        )

        assert result is decision
        assert llm.call_count == 1
        assert llm.updates == [{"max_tokens": MAX_DECISION_TOKENS}]

    @pytest.mark.asyncio
    async def test_falls_back_to_function_calling_when_strict_json_is_malformed(self):
        """response_format and function calling fail on different models, so the second attempt switches."""
        decision = NamespaceDecision(has_enough_information=False, follow_up_question="Which?", reasoning="unclear")
        llm = _RecordingLLM([_truncated_json_error(), decision])

        result = await predict_namespace_decision(
            llm=llm, prompt=MagicMock(), available_namespaces="ns", conversation_history="history"
        )

        assert result is decision
        assert llm.call_count == 2
        assert llm.updates[1] == {"should_use_structured_outputs": False}

    @pytest.mark.asyncio
    async def test_raises_when_both_mechanisms_fail(self):
        """Degrading is the step's decision, not this helper's."""
        llm = _RecordingLLM([_truncated_json_error(), _truncated_json_error()])

        with pytest.raises(ValidationError):
            await predict_namespace_decision(
                llm=llm, prompt=MagicMock(), available_namespaces="ns", conversation_history="history"
            )

        assert llm.call_count == 2


class TestDetermineNamespacesStepDegradation:
    """A provider that cannot produce parseable JSON must not kill the run."""

    @pytest.mark.asyncio
    async def test_asks_for_clarification_when_no_decision_is_parseable(self, monkeypatch: pytest.MonkeyPatch):
        """The user gets the default follow-up question instead of a raw parser error."""

        async def failing_predict(**_kwargs):
            raise _truncated_json_error()

        monkeypatch.setattr(
            "swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent.predict_namespace_decision",
            failing_predict,
        )

        @asynccontextmanager
        async def cost_reporting_llm(_displayer):
            yield MagicMock()

        agent_config = MagicMock()
        agent_config.task_llm.cost_reporting_llm = cost_reporting_llm
        run_context = MagicMock()
        run_context.get = AsyncMock(return_value={})
        displayer = MagicMock()
        displayer.display_thought = AsyncMock()

        result = await NamespaceSelectionAgent().determine_namespaces_step(
            DetermineNamespacesEvent(),
            agent_config=agent_config,
            run_context=run_context,
            displayer=displayer,
            t=lambda key, **_kwargs: key,
        )

        assert isinstance(result, FollowUpQuestionRequestEvent)
        assert result.question == "agent.namespace_selection_agent.messages.default_follow_up"


class TestConfig:
    """Tests for configuration."""

    def test_config_creation_requires_llm(self):
        """Test that config requires LLM configuration."""
        # This test verifies the config structure - actual LLMConfig creation
        # requires LiteLLM proxy settings, so we just check the field exists
        assert hasattr(NamespaceSelectionAgentConfig, "model_fields")
        assert "llm" in NamespaceSelectionAgentConfig.model_fields
        assert "bucket_names" in NamespaceSelectionAgentConfig.model_fields
        assert "rag_delegation" in NamespaceSelectionAgentConfig.model_fields
