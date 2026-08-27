"""Tests for NamespaceSelectionAgent.

These tests verify the NamespaceSelectionAgent components work correctly.
Note: Full integration tests require Redis, NATS, and MongoDB infrastructure.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import get_args
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml
from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import StopEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

import swiss_ai_hub.agent
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import NamespaceSelectionAgentConfig
from swiss_ai_hub.agent.agents.namespace_selection_agent.events import (
    DetermineNamespacesEvent,
    FollowUpQuestionHitl,
    NamespaceApprovalHitl,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.llm.namespace_decision import NamespaceDecision
from swiss_ai_hub.agent.agents.namespace_selection_agent.namespace_selection_agent import (
    DETERMINATION_MAX_OUTPUT_TOKENS,
    NamespaceSelectionAgent,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.utils import (
    format_approval_question,
    format_available_namespaces,
    format_conversation_history,
)


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

    def test_nullable_fields_are_described_as_always_provided(self):
        """Strict structured output marks every property required, so a field that may be null must
        instruct the model to emit null rather than omit the key - a model that omits it cannot
        terminate the guided-decoding grammar and burns its whole token budget on whitespace."""
        for field_name, field_info in NamespaceDecision.model_fields.items():
            if type(None) not in get_args(field_info.annotation):
                continue
            description = field_info.description or ""
            assert "null" in description.lower(), (
                f"'{field_name}' accepts null and is therefore required by the strict schema, but its "
                f"description does not tell the model to provide null: {description!r}"
            )

    def test_strict_response_format_still_requires_every_property(self):
        """The canary for the assumption above: if OpenAI stopped forcing every property into
        `required`, the prompt contract this agent maintains would no longer be necessary. Asserts
        someone else's behaviour, so a moved private symbol must skip rather than fail the build."""
        try:
            from openai.resources.chat.completions.completions import _type_to_response_format
        except ImportError:
            pytest.skip("openai._type_to_response_format moved; strict-mode canary cannot run")

        json_schema = _type_to_response_format(NamespaceDecision)["json_schema"]

        assert json_schema["strict"] is True
        assert set(json_schema["schema"]["required"]) == set(json_schema["schema"]["properties"])


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


class _FakeLLM:
    """Stands in for the LLM yielded by ``cost_reporting_llm``, which is built fresh per call."""

    def __init__(self, *, result=None, error=None, max_tokens=8192):
        self.max_tokens = max_tokens
        self._result = result
        self._error = error
        self.call_count = 0

    async def astructured_predict(self, *_args, **_kwargs):
        self.call_count += 1
        if self._error is not None:
            raise self._error
        return self._result


class _FakeRunContext:
    def __init__(self, data: dict):
        self.data = data

    async def get(self, key, default=None):
        return self.data.get(key, default)

    async def set(self, key, value):
        self.data[key] = value


class _FakeLocaleHandler:
    """Returns the i18n key itself, so assertions can name the key the step is expected to use."""

    def __call__(self, key, **_kwargs):
        return key

    @staticmethod
    def extract(value):
        return value if isinstance(value, str) else "{namespaces}"


def _truncated_json_error() -> ValidationError:
    """The real error strict guided decoding produces when the model omits a property and pads whitespace."""
    try:
        NamespaceDecision.model_validate_json('{\n  "has_enough_information": true\n  \n  \n')
    except ValidationError as invalid_json:
        return invalid_json
    raise AssertionError("expected truncated JSON to fail validation")


DEFAULT_AVAILABLE = {"defaultknowledge": ["hr-policies", "it-support"], "sharedknowledge": ["product-specs"]}
_TRANSLATIONS_DIR = Path(swiss_ai_hub.agent.__file__).parent / "i18n" / "translations" / "agent"


async def _run_determination(llm: _FakeLLM, *, available=None, history=None):
    """Invoke the determination step with the collaborators the dispatcher would normally inject."""
    agent = NamespaceSelectionAgent.__new__(NamespaceSelectionAgent)
    cost_reporting_finished = []

    @asynccontextmanager
    async def cost_reporting_llm(_displayer, *, user=None):
        yield llm
        cost_reporting_finished.append(True)

    agent_config = MagicMock()
    agent_config.task_llm.cost_reporting_llm = cost_reporting_llm
    agent_config.max_conversation_history_entries = 20
    agent_config.approval_message_template = "Query these sources:\n{namespaces}\nApprove?"

    run_context = _FakeRunContext(
        {
            "available_namespaces": DEFAULT_AVAILABLE if available is None else available,
            "conversation_history": history if history is not None else [{"role": "user", "content": "leave policy?"}],
        }
    )
    displayer = AsyncMock()
    result = await NamespaceSelectionAgent.determine_namespaces_step(
        agent, DetermineNamespacesEvent(), agent_config, run_context, displayer, _FakeLocaleHandler(), fake_user()
    )
    return result, displayer, run_context, bool(cost_reporting_finished)


class TestDeterminationTokenCeiling:
    """AC2: a model that omits a property must not be able to burn the full output budget."""

    @pytest.mark.asyncio
    async def test_output_budget_is_capped_for_this_call(self):
        llm = _FakeLLM(
            result=NamespaceDecision(has_enough_information=False, follow_up_question="which?", reasoning="r")
        )
        await _run_determination(llm)
        assert llm.max_tokens == DETERMINATION_MAX_OUTPUT_TOKENS

    @pytest.mark.asyncio
    async def test_ceiling_below_the_cap_is_left_alone(self):
        """The cap is an upper bound, never a raise - a tighter configured budget stays tighter."""
        llm = _FakeLLM(
            result=NamespaceDecision(has_enough_information=False, follow_up_question="which?", reasoning="r"),
            max_tokens=256,
        )
        await _run_determination(llm)
        assert llm.max_tokens == 256


class TestDeterminationUnparseableOutput:
    """AC3: unparseable structured output must reach the user as a sentence, never as a Pydantic dump."""

    @pytest.mark.asyncio
    async def test_validation_error_stops_the_run_with_a_readable_message(self):
        result, displayer, _, _ = await _run_determination(_FakeLLM(error=_truncated_json_error()))

        assert isinstance(result, StopEvent)
        displayer.display_chunk.assert_awaited_once()
        assert (
            displayer.display_chunk.await_args.args[0]
            == "agent.namespace_selection_agent.messages.determination_failed"
        )

    @pytest.mark.asyncio
    async def test_value_error_is_handled_the_same_way(self):
        """``ResilientOpenAILike`` treats ValueError as malformed output too, so this step must agree."""
        result, displayer, _, _ = await _run_determination(_FakeLLM(error=ValueError("no content")))

        assert isinstance(result, StopEvent)
        displayer.display_chunk.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_infrastructure_errors_still_propagate(self):
        """A gateway failure is not a malformed answer - masking it as "please rephrase" would hide outages."""
        with pytest.raises(TimeoutError):
            await _run_determination(_FakeLLM(error=TimeoutError("gateway timed out")))

    @pytest.mark.asyncio
    async def test_costs_are_still_reported_when_output_is_unparseable(self):
        """Returning from inside the cost-reporting context is a normal exit, so usage must still be recorded."""
        _, _, _, cost_reported = await _run_determination(_FakeLLM(error=_truncated_json_error()))
        assert cost_reported is True


class TestDeterminationDecisionRouting:
    """The three decision outcomes must keep working; the guarded call must not change them."""

    @pytest.mark.asyncio
    async def test_clarification_decision_asks_the_model_s_question(self):
        llm = _FakeLLM(
            result=NamespaceDecision(
                has_enough_information=False,
                follow_up_question="Did you mean hr-policies or it-support?",
                reasoning="ambiguous",
            )
        )
        result, _, _, _ = await _run_determination(llm)

        assert isinstance(result, FollowUpQuestionHitl.request)
        assert result.question == "Did you mean hr-policies or it-support?"

    @pytest.mark.asyncio
    async def test_valid_selection_requests_approval_and_stores_the_proposal(self):
        """The happy path: a usable decision proposes namespaces and waits for the user to approve."""
        selected = {"defaultknowledge": "hr-policies", "sharedknowledge": "product-specs"}
        llm = _FakeLLM(
            result=NamespaceDecision(has_enough_information=True, selected_namespaces=selected, reasoning="clear")
        )
        result, _, run_context, _ = await _run_determination(llm)

        assert isinstance(result, NamespaceApprovalHitl.request)
        assert "hr-policies" in result.question
        assert run_context.data["proposed_namespaces"] == selected

    @pytest.mark.asyncio
    async def test_hallucinated_namespace_loops_back_for_another_attempt(self):
        """An invented namespace is fed back as a correction rather than proposed to the user."""
        llm = _FakeLLM(
            result=NamespaceDecision(
                has_enough_information=True,
                selected_namespaces={"defaultknowledge": "does-not-exist"},
                reasoning="hallucinated",
            )
        )
        result, _, run_context, _ = await _run_determination(llm)

        assert isinstance(result, DetermineNamespacesEvent)
        assert "proposed_namespaces" not in run_context.data
        assert run_context.data["conversation_history"][-1]["role"] == "system"


class TestDeterminationPromptContract:
    """The strict schema requires every property, so schema and prompt must both demand all of them."""

    def test_every_locale_instructs_the_model_to_send_all_fields(self):
        """A prompt edit that misses a locale would silently reintroduce the bug for those users."""
        for locale in ("en", "de", "fr", "it"):
            path = _TRANSLATIONS_DIR / f"namespace_selection_agent.{locale}.yml"
            translations = yaml.safe_load(path.read_text(encoding="utf-8"))
            prompt = translations["prompts"]["determination"]
            missing = [field for field in NamespaceDecision.model_fields if field not in prompt]
            assert not missing, f"{locale} determination prompt never names {missing}"
            assert translations["messages"]["determination_failed"], f"{locale} is missing determination_failed"


class TestAdvertisedStartEvents:
    """The RAG-delegation picker in the Admin UI lists agent classes by their advertised start events.

    `NamespaceSelectionAgent` must not advertise `RAGStartEvent`: it cannot be started by one, and
    advertising it put this agent in its own delegation picker, where selecting it made a profile
    delegate to itself and the run hung forever with nothing logged.
    """

    def test_rag_start_event_is_not_advertised(self):
        start_event_names = {event.__name__ for event in NamespaceSelectionAgent.get_start_events()}
        assert "RAGStartEvent" not in start_event_names

    def test_chat_message_is_still_the_entry_point(self):
        start_event_names = {event.__name__ for event in NamespaceSelectionAgent.get_start_events()}
        assert start_event_names == {"UserMessageEvent"}
