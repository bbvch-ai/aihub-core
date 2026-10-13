"""The budget a conversation fills: the admin's ceiling, capped by the model window less the tokenizer margin."""

from unittest.mock import patch

from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import WINDOW_SAFETY_FACTOR

MODULE = "swiss_ai_hub.agent.capabilities.conversation.conversation_fields"


def _config(number_of_input_tokens: int) -> LLMWrappingAgentConfig:
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
        assert _config(number_of_input_tokens=128_000).input_budget() == int(91_824 * WINDOW_SAFETY_FACTOR)


def test_a_cost_ceiling_below_the_window_is_kept_as_set():
    with patch(f"{MODULE}.usable_input_budget", return_value=91_824):
        assert _config(number_of_input_tokens=40_000).input_budget() == 40_000


def test_without_a_known_window_the_cost_ceiling_is_the_budget():
    with patch(f"{MODULE}.usable_input_budget", return_value=None):
        assert _config(number_of_input_tokens=128_000).input_budget() == 128_000
