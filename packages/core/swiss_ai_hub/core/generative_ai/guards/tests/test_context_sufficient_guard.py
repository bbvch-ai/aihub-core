from unittest.mock import Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.context_sufficient_guard import ContextGuardResult, context_sufficient_guard
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

scenarios("./features/context_sufficient_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        mock_llm_instance = mock_llm.return_value
        yield mock_llm_instance


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@given(parsers.parse('the following context "{context}"'), target_fixture="context")
def _(context):
    return context


@given("the following previous queries:", target_fixture="prev_queries")
def _(datatable):
    queries = []
    for row in datatable[1:]:
        queries.append(row[0])
    return queries


@given("no previous queries", target_fixture="prev_queries")
def _():
    return []


@given("more hops are available", target_fixture="more_hops_available")
def _():
    return True


@given("no more hops are available", target_fixture="more_hops_available")
def _():
    return False


@given(parsers.parse('the LLM returns success={success:w} with reasoning="{reasoning}"'), target_fixture="llm_result")
def _(llm, success, reasoning):
    success_bool = success == "True"
    result = ContextGuardResult(reasoning=reasoning, success=success_bool, new_query=None)
    llm.structured_predict.return_value = result
    return result


@given(
    parsers.parse('the LLM returns success={success:w} with reasoning="{reasoning}" and new_query="{new_query}"'),
    target_fixture="llm_result",
)
def _(llm, success, reasoning, new_query):
    success_bool = success == "True"
    result = ContextGuardResult(reasoning=reasoning, success=success_bool, new_query=new_query)
    llm.structured_predict.return_value = result
    return result


@given("the following chat history:", target_fixture="chat_history")
def _(datatable):
    return [ChatMessage(role=row[0], content=row[1]) for row in datatable[1:]]


@when("the context sufficient guard is executed", target_fixture="guard_result")
@async_test
async def _(llm, locale_handler, user_query, context, prev_queries, more_hops_available):
    result = await context_sufficient_guard(
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        context=context,
        prev_queries=prev_queries,
        more_hops_available=more_hops_available,
    )
    return result


@when("the context sufficient guard is executed with chat history", target_fixture="guard_result")
@async_test
async def _(llm, locale_handler, user_query, context, prev_queries, more_hops_available, chat_history):
    result = await context_sufficient_guard(
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        context=context,
        prev_queries=prev_queries,
        more_hops_available=more_hops_available,
        chat_history=chat_history,
    )
    return result


@then("the LLM prompt should include the chat history")
def _(llm, chat_history):
    call_kwargs = llm.structured_predict.call_args.kwargs
    rendered = call_kwargs["chat_history"]
    for message in chat_history:
        assert message.role.value in rendered
        assert message.content in rendered


@then("the LLM prompt should render chat history as an empty string")
def _(llm):
    assert llm.structured_predict.call_args.kwargs["chat_history"] == ""


@then("the guard should accept the request")
def _(guard_result):
    assert guard_result.success is True, f"Expected guard to accept, but it rejected with: {guard_result.reasoning}"


@then("the guard should reject the request")
def _(guard_result):
    assert guard_result.success is False, f"Expected guard to reject, but it accepted with: {guard_result.reasoning}"


@then(parsers.parse('the reasoning should be "{expected_reasoning}"'))
def _(guard_result, expected_reasoning):
    assert guard_result.reasoning == expected_reasoning, (
        f"Expected reasoning: {expected_reasoning}, got: {guard_result.reasoning}"
    )


@then("no new query should be generated")
def _(guard_result):
    assert guard_result.new_query is None, f"Expected no new query, but got: {guard_result.new_query}"


@then(parsers.parse('a new query "{expected_query}" should be generated'))
def _(guard_result, expected_query):
    assert guard_result.new_query == expected_query, (
        f"Expected new query: {expected_query}, got: {guard_result.new_query}"
    )
