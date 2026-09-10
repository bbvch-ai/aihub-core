from unittest.mock import AsyncMock, Mock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.few_shot_guard import few_shot_guard
from swiss_ai_hub.core.generative_ai.prompting.few_shot.few_shot_guard_example import FewShotGuardExample
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

scenarios("./features/few_shot_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        yield mock_llm.return_value


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse("the following few-shot examples:"), target_fixture="examples")
def _(datatable, locale_handler):
    examples = []
    for row in datatable[1:]:
        user_message = LocaleString(**{locale_handler.locale: row[0]})
        success = row[1] == "True"
        reason = LocaleString(**{locale_handler.locale: row[2]})
        examples.append(FewShotGuardExample(user=user_message, success=success, reason=reason))
    return examples


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@given(parsers.parse('the guard model replies "{reply}"'))
def _(llm, reply):
    llm.achat = AsyncMock(return_value=ChatResponse(message=ChatMessage(role=MessageRole.ASSISTANT, content=reply)))


@when("the few-shot guard is executed", target_fixture="guard_result")
@async_test
async def _(examples, llm, locale_handler, user_query):
    return await few_shot_guard(examples=examples, llm=llm, t=locale_handler, user_query=user_query)


@then("the guard should accept the request")
def _(guard_result):
    assert guard_result.success is True


@then("the guard should reject the request")
def _(guard_result):
    assert guard_result.success is False


@then(parsers.parse('the reasoning should be "{expected_reasoning}"'))
def _(guard_result, expected_reasoning):
    assert guard_result.reasoning == expected_reasoning
