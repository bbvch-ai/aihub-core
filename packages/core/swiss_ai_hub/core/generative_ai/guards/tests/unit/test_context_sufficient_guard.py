from unittest.mock import AsyncMock, Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole, TextBlock
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

scenarios("./features/context_sufficient_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        yield mock_llm.return_value


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@given(parsers.parse('the following context "{context}"'), target_fixture="context_message")
def _(context):
    return ChatMessage(role="user", blocks=[TextBlock(text=context)])


@given("the following previous queries:", target_fixture="prev_queries")
def _(datatable):
    return [row[0] for row in datatable[1:]]


@given("no previous queries", target_fixture="prev_queries")
def _():
    return []


@given("more hops are available", target_fixture="more_hops_available")
def _():
    return True


@given("no more hops are available", target_fixture="more_hops_available")
def _():
    return False


@given("the following chat history:", target_fixture="chat_history")
def _(datatable):
    return [ChatMessage(role=row[0], content=row[1]) for row in datatable[1:]]


@given(parsers.parse('the guard model replies "{reply}"'))
def _(llm, reply):
    llm.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=reply)))


@when("the context sufficient guard is executed", target_fixture="guard_result")
@async_test
async def _(llm, locale_handler, user_query, context_message, prev_queries, more_hops_available):
    return await context_sufficient_guard(
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        context_message=context_message,
        prev_queries=prev_queries,
        more_hops_available=more_hops_available,
        chat_history=[],
    )


@when("the context sufficient guard is executed with chat history", target_fixture="guard_result")
@async_test
async def _(llm, locale_handler, user_query, context_message, prev_queries, more_hops_available, chat_history):
    return await context_sufficient_guard(
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        context_message=context_message,
        prev_queries=prev_queries,
        more_hops_available=more_hops_available,
        chat_history=chat_history,
    )


@then("the guard should accept the request")
def _(guard_result):
    assert guard_result.success is True, f"Expected accept, got reject: {guard_result.reasoning}"


@then("the guard should reject the request")
def _(guard_result):
    assert guard_result.success is False, f"Expected reject, got accept: {guard_result.reasoning}"


@then(parsers.parse('the reasoning should be "{expected_reasoning}"'))
def _(guard_result, expected_reasoning):
    assert guard_result.reasoning == expected_reasoning, f"got: {guard_result.reasoning}"


@then("no new query should be generated")
def _(guard_result):
    assert guard_result.new_query is None, f"unexpected new query: {guard_result.new_query}"


@then(parsers.parse('a new query "{expected_query}" should be generated'))
def _(guard_result, expected_query):
    assert guard_result.new_query == expected_query, f"got: {guard_result.new_query}"


@then("the prompt should include the chat history")
def _(llm, chat_history):
    sent_messages = llm.achat.call_args.args[0]
    rendered = " ".join(
        block.text for message in sent_messages for block in message.blocks if isinstance(block, TextBlock)
    )
    for message in chat_history:
        assert message.content in rendered, f"chat-history content missing from prompt: {message.content!r}"
