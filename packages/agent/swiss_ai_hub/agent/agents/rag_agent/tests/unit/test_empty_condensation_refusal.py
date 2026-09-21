"""A blank condensation refuses the turn with a localized message instead of leaking an exception.

`condense_standalone_question` raises `EmptyCondensationError` (#1753), and `stop_on_error` defaults to True,
so an uncaught raise reaches the dispatcher as an `ExceptionEvent` whose message the chat UI renders — the
raw English sentence from the error class. `do_condense_standalone_question` catches it and returns the same
`RAGFailureStopEvent` shape `_refuse_oversized_input` uses, so both "we cannot serve this turn" cases look
alike to the user.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import RAGFailureReason, RAGFailureStopEvent, StandaloneQuestionCondenserEvent
from swiss_ai_hub.core.generative_ai import EmptyCondensationError, LLMConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

# Load rag_agent first: it has a module-level circular dependency with rag.preconditions/step_functions that only
# resolves in the runtime (rag_agent-first) order; importing step_functions first would break.
import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.step_functions import do_condense_standalone_question

CONDENSE_PATH = "swiss_ai_hub.agent.rag.step_functions.condense_standalone_question"


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_chunk = AsyncMock()
    return displayer


async def _run(displayer: MagicMock, locale: str = "en"):
    llm_config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    with patch.object(LLMConfig, "cost_reporting_llm") as cost_reporting_llm:
        cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=False)
        return await do_condense_standalone_question(
            [ChatMessage(role=MessageRole.USER, content="Do we offer a discount?")],
            ChatMessage(role=MessageRole.USER, content="what about part-timers?"),
            llm_config,
            displayer,
            LocaleHandler(locale=locale),
            None,
        )


@pytest.mark.asyncio
async def test_a_blank_condensation_becomes_a_failure_stop_event():
    displayer = _displayer()

    with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
        result = await _run(displayer)

    assert isinstance(result, RAGFailureStopEvent)
    assert result.reason == RAGFailureReason.CONDENSATION_EMPTY


@pytest.mark.asyncio
async def test_the_refusal_is_rendered_to_the_user_and_carries_the_same_text():
    """The chunk is what the chat renders; `answer` carries it for non-streaming consumers."""
    displayer = _displayer()

    with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
        result = await _run(displayer)

    displayer.display_chunk.assert_awaited_once()
    assert displayer.display_chunk.await_args.args[0] == result.answer


@pytest.mark.asyncio
async def test_the_refusal_is_localized_not_the_exception_text():
    """The point of the catch: the user must never see `EmptyCondensationError`'s English message."""
    rendered = {}
    for locale in ("en", "de", "fr", "it"):
        displayer = _displayer()
        with patch(CONDENSE_PATH, side_effect=EmptyCondensationError("nothing came back")):
            result = await _run(displayer, locale=locale)
        rendered[locale] = result.answer

    assert "nothing came back" not in rendered.values()
    assert all(text for text in rendered.values())
    assert len(set(rendered.values())) == 4, f"locales must differ, got {rendered}"


@pytest.mark.asyncio
async def test_a_usable_condensation_still_returns_the_condenser_event():
    """The guard must not swallow the happy path."""
    displayer = _displayer()
    condensed = ChatMessage(role=MessageRole.USER, content="Do we offer a part-time discount?")

    with patch(CONDENSE_PATH, new=AsyncMock(return_value=condensed)):
        result = await _run(displayer)

    assert isinstance(result, StandaloneQuestionCondenserEvent)
    assert result.condensed_question == "Do we offer a part-time discount?"
    displayer.display_chunk.assert_not_awaited()
