"""A refusal has to be about what the user asked, not about a document from earlier in the thread.

The history handed to the reject path still carries the user's words verbatim — "summarise this file" — so a
model asked to explain the refusal from that alone resolves the reference the only way it can, against the
earlier turns. The condenser already resolved it against the attachment; this pins that the result reaches
the refusal.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import FewShotRejectEvent
from swiss_ai_hub.core.i18n import LocaleHandler

import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.step_functions import do_respond_with_llm

_ASKED_ABOUT = "test_upload_file.pdf"
_FROM_THE_HISTORY = "Spesenreglement_bbv.pdf"


def _displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()
    displayer.display_llm_stream = AsyncMock(return_value=MagicMock())
    return displayer


def _llm_config() -> MagicMock:
    llm_config = MagicMock()
    llm_config.cost_reporting_llm.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
    llm_config.cost_reporting_llm.return_value.__aexit__ = AsyncMock(return_value=False)
    return llm_config


async def _reject(condensed: ChatMessage | None, locale: str = "en") -> str:
    displayer = _displayer()
    history = [
        ChatMessage(role=MessageRole.USER, content=f"summarise {_FROM_THE_HISTORY}"),
        ChatMessage(role=MessageRole.USER, content="summarise this file"),
    ]
    event = FewShotRejectEvent(reason="Summarising a file is outside this agent's scope.")

    with patch("swiss_ai_hub.agent.rag.step_functions.merge_consecutive_messages", side_effect=lambda m: m):
        await do_respond_with_llm(
            event,
            history,
            None,
            None,
            _llm_config(),
            displayer,
            LocaleHandler(locale=locale),
            None,
            condensed_question=condensed,
        )

    messages = displayer.display_llm_stream.call_args[0][2]
    return messages[0].content


@pytest.mark.asyncio
async def test_the_refusal_is_told_what_was_actually_asked():
    instruction = await _reject(ChatMessage(role=MessageRole.USER, content=f"Summarise {_ASKED_ABOUT}."))

    assert _ASKED_ABOUT in instruction
    assert "outside this agent's scope" in instruction


@pytest.mark.asyncio
async def test_a_refusal_without_a_condensed_question_still_renders():
    """Every placeholder in the template must resolve, or the refusal raises instead of being delivered."""
    instruction = await _reject(None)

    assert "{" not in instruction
    assert "outside this agent's scope" in instruction


@pytest.mark.parametrize("locale", ["de", "en", "fr", "it"])
@pytest.mark.asyncio
async def test_every_locale_renders_the_reject_prompt(locale):
    """One template, four languages, and a missing placeholder only fails at runtime in that language."""
    instruction = await _reject(ChatMessage(role=MessageRole.USER, content=f"Summarise {_ASKED_ABOUT}."), locale)

    assert _ASKED_ABOUT in instruction
    assert "{" not in instruction
