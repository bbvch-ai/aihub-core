"""The LLM wrapping agent reads the pages a message links next to its other context: the request always goes out, so
the prompt waits for it, and the pages take room from attached files only while the profile reads them."""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AttachedFilesReadEvent,
    ConversationContextualizedEvent,
    FetchWebPagesEvent,
    KnowledgeSearchedEvent,
    MemoryRecalledEvent,
    ReadAttachedFilesEvent,
    UserMessageEvent,
    WebPagesFetchedEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig

QUESTION = ChatMessage(role=MessageRole.USER, content="What does https://example.com/a say?")
CTX = ConversationContextualizedEvent(history=[QUESTION], query="What does https://example.com/a say?")


def _config(web_fetch: WebFetchConfig | None) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="web-fetch-wrapper",
        name=LocaleString(en="Wrapper"),
        description=LocaleString(en="Wrapper"),
        system_prompt=LocaleString(en="Respond briefly."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        web_fetch=web_fetch,
    )


async def _gather(web_fetch: WebFetchConfig | None) -> tuple[FetchWebPagesEvent, ReadAttachedFilesEvent]:
    event = UserMessageEvent(user=fake_user(), messages=[QUESTION], web_references=["https://example.com/b"])
    requests = await LLMWrappingAgent().gather_context_step(CTX, event, _config(web_fetch))
    [fetch] = [request for request in requests if isinstance(request, FetchWebPagesEvent)]
    [read] = [request for request in requests if isinstance(request, ReadAttachedFilesEvent)]
    return fetch, read


@pytest.mark.asyncio
async def test_the_linked_pages_are_requested_and_get_room_while_fetching_is_on():
    fetch, read = await _gather(WebFetchConfig(max_page_characters=4_000))

    assert fetch.urls == ["https://example.com/a", "https://example.com/b"]
    assert fetch.reading
    assert read.reserve_tokens == 2 * 4_000 // 4


@pytest.mark.asyncio
async def test_with_fetching_off_the_request_still_goes_out_but_takes_no_room():
    """The step answers, telling the model it cannot open the links, and the chat shows no reading progress."""
    fetch, read = await _gather(None)

    assert fetch.urls == ["https://example.com/a", "https://example.com/b"]
    assert not fetch.reading
    assert read.reserve_tokens == 0


@pytest.mark.asyncio
async def test_the_pages_join_the_prompt_ahead_of_the_attached_files():
    page = [ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT>The page says Z.")]
    attached = [ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT>The file says Y.")]

    request = await LLMWrappingAgent().assemble_prompt_step(
        CTX,
        MemoryRecalledEvent(),
        AttachedFilesReadEvent(block=attached),
        KnowledgeSearchedEvent(),
        WebPagesFetchedEvent(block=page),
    )

    assert request.blocks[-2:] == [page, attached]
