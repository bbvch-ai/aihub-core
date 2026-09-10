from unittest.mock import AsyncMock, Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.agent_description_guard import agent_description_guard
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

scenarios("./features/agent_description_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        yield mock_llm.return_value


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('an agent description "{description}"'), target_fixture="agent_description")
def _(description, locale_handler):
    return LocaleString(**{locale_handler.locale: description})


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@given(parsers.parse('the guard model replies "{reply}"'))
def _(llm, reply):
    llm.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=reply)))


@when("the agent description guard is executed", target_fixture="guard_result")
@async_test
async def _(agent_description, llm, locale_handler, user_query):
    return await agent_description_guard(
        agent_description=agent_description,
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        messages=[],
    )


@then("the guard should accept the request")
def _(guard_result):
    assert guard_result.success is True


@then("the guard should reject the request")
def _(guard_result):
    assert guard_result.success is False


@then(parsers.parse('the reasoning should be "{expected_reasoning}"'))
def _(guard_result, expected_reasoning):
    assert guard_result.reasoning == expected_reasoning
