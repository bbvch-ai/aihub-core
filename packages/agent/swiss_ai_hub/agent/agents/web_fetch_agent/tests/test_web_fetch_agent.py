"""The web fetch blueprint is the instructed assistant with reading required: its form has no switch that turns
reading off, a profile that tries to is refused, and every link in the message is asked for."""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import ConversationContextualizedEvent, FetchWebPagesEvent, UserMessageEvent
from swiss_ai_hub.core.form import Group
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.web_fetch_agent.web_fetch_agent import WebFetchAgent
from swiss_ai_hub.agent.agents.web_fetch_agent.web_fetch_agent_config import WebFetchAgentConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig

QUESTION = ChatMessage(role=MessageRole.USER, content="What does https://example.com/a say?")
CTX = ConversationContextualizedEvent(history=[QUESTION], query="What does https://example.com/a say?")
PROFILE = {
    "agent_id": "web-reader",
    "name": {"en": "Reader"},
    "description": {"en": "Reader"},
    "system_prompt": {"en": "Answer from the pages."},
    "llm": {"model_name": "text-generation/gemma-4-31B-it"},
}


def test_the_form_shows_the_limits_without_a_switch_to_turn_reading_off():
    [group] = [element for element in WebFetchAgentConfig.as_form().to_formkit_form() if element.name == "web_fetch"]

    assert isinstance(group, Group)
    assert not group.nullable
    assert [child.name for child in group.children] == ["max_urls", "timeout_seconds", "max_page_characters"]


def test_a_profile_saved_without_limits_reads_with_the_defaults():
    assert WebFetchAgentConfig.model_validate(PROFILE).web_fetch == WebFetchConfig()


def test_a_profile_cannot_switch_reading_off():
    with pytest.raises(ValidationError):
        WebFetchAgentConfig.model_validate({**PROFILE, "web_fetch": None})


@pytest.mark.asyncio
async def test_every_link_in_the_message_is_read():
    event = UserMessageEvent(user=fake_user(), messages=[QUESTION], web_references=["https://example.com/b"])
    config = WebFetchAgentConfig(
        agent_id="web-reader",
        name=LocaleString(en="Reader"),
        description=LocaleString(en="Reader"),
        system_prompt=LocaleString(en="Answer from the pages."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
    )

    requests = await WebFetchAgent().gather_context_step(CTX, event, config)

    [fetch] = [request for request in requests if isinstance(request, FetchWebPagesEvent)]
    assert fetch.urls == ["https://example.com/a", "https://example.com/b"]
    assert fetch.reading
