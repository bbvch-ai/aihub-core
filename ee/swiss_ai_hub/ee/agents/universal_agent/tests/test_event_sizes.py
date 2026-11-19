"""The Universal Agent's turn ends in events the broker accepts, even when an attached form is long in characters.

The fixture and the measurements are the LLM Wrapping Agent's, so both blueprints are held to the same limit.
"""

from unittest.mock import MagicMock

import pytest
from swiss_ai_hub.agent.agents.llm_wrapping_agent.tests.test_event_sizes import (
    EVENT_LIMIT_BYTES,
    QUESTION,
    _answer_to,
    _prompt,
    _size,
    _stop_after,
)
from swiss_ai_hub.core.events.agent import ConversationContextualizedEvent, ToolLoopFinishedEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

from swiss_ai_hub.ee.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.ee.agents.universal_agent.universal_agent_config import UniversalAgentConfig


@pytest.mark.asyncio
async def test_the_universal_turn_ends_in_events_the_broker_accepts():
    config = UniversalAgentConfig(
        agent_id="event-sizes",
        name=LocaleString(en="Universal"),
        description=LocaleString(en="Universal fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
    )
    ctx = ConversationContextualizedEvent(history=_prompt(), query=QUESTION)

    events = await UniversalAgent().complete_step(
        ToolLoopFinishedEvent(answer=_answer_to(_prompt())),
        ctx,
        agent_config=config,
        topic=MagicMock(),
        t=LocaleHandler(locale="en"),
        user=None,
    )
    stop = await _stop_after(events[-1])

    for event in [*events, stop]:
        assert _size(event) < EVENT_LIMIT_BYTES, type(event).__name__
