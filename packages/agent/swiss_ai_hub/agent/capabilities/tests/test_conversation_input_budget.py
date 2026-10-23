"""The budget a conversation fills: the model window less the tokenizer margin, held to the admin's own limit."""

from unittest.mock import patch

from swiss_ai_hub.core.form import ModelBoundInputNumber
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import (
    FALLBACK_INPUT_TOKENS,
    WINDOW_SAFETY_FACTOR,
)

MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation_fields"


def _config(number_of_input_tokens: int | None) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig.model_construct(
        agent_id="chat",
        name=LocaleString(en="Chat"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        task_llm=None,
        number_of_input_tokens=number_of_input_tokens,
    )


def test_a_window_is_filled_only_up_to_the_safety_margin():
    """Issue #2077: tiktoken undercounts Ministral by 6%, so a prompt fitted exactly to the window overflowed it."""
    with patch(f"{MODULE}.usable_input_budget", return_value=91_824):
        assert _config(number_of_input_tokens=128_000).input_budget == int(91_824 * WINDOW_SAFETY_FACTOR)


def test_a_cost_ceiling_below_the_window_is_kept_as_set():
    with patch(f"{MODULE}.usable_input_budget", return_value=91_824):
        assert _config(number_of_input_tokens=40_000).input_budget == 40_000


def test_without_a_known_window_the_cost_ceiling_is_the_budget():
    with patch(f"{MODULE}.usable_input_budget", return_value=None):
        assert _config(number_of_input_tokens=128_000).input_budget == 128_000


def test_the_budget_field_is_bounded_by_the_main_model_window_instead_of_a_static_range():
    element = LLMWrappingAgentConfig.conversation_form_elements()["number_of_input_tokens"]

    assert isinstance(element, ModelBoundInputNumber)
    assert element.model_ref == "llm.model_name"
    assert element.max_from == "max_input_tokens"
    assert element.max is None


def test_the_budget_field_tells_the_form_how_much_of_the_window_is_filled():
    """The bound stays the model's real limit; the form says what a value up to it amounts to at run time."""
    element = LLMWrappingAgentConfig.conversation_form_elements()["number_of_input_tokens"]

    assert element.fill_factor == WINDOW_SAFETY_FACTOR
    assert element.model_dump(by_alias=True)["fillFactor"] == WINDOW_SAFETY_FACTOR


def test_an_unset_limit_fills_the_window_less_the_margin():
    with patch(f"{MODULE}.usable_input_budget", return_value=155_648):
        assert _config(number_of_input_tokens=None).input_budget == int(155_648 * WINDOW_SAFETY_FACTOR)


def test_an_unset_limit_without_a_known_window_falls_back_to_the_previous_default():
    with patch(f"{MODULE}.usable_input_budget", return_value=None):
        assert _config(number_of_input_tokens=None).input_budget == FALLBACK_INPUT_TOKENS


def test_only_a_limit_of_the_admins_own_holds_back_what_the_window_allows():
    assert _config(number_of_input_tokens=None).held_to_ceiling(150_000) == 150_000
    assert _config(number_of_input_tokens=40_000).held_to_ceiling(150_000) == 40_000


def test_a_new_profile_leaves_the_limit_to_the_model():
    """A pre-filled number was above the window of every smaller model, so a fresh profile on one could not be saved."""
    assert LLMWrappingAgentConfig.model_fields["number_of_input_tokens"].default is None


def test_the_budget_field_offers_its_own_override_showing_what_applies_while_unset():
    element = LLMWrappingAgentConfig.conversation_form_elements()["number_of_input_tokens"]

    assert element.override_label is not None
    assert element.default_from is None
    assert element.fallback_default == FALLBACK_INPUT_TOKENS
