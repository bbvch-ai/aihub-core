from unittest.mock import Mock, patch

import pytest
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.guards.agent_description_guard import GuardResult, agent_description_guard
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


scenarios("./features/agent_description_guard.feature")


@pytest.fixture
def llm():
    with patch("llama_index.core.llms.llm.LLM", new_callable=Mock) as mock_llm:
        mock_llm_instance = mock_llm.return_value
        mock_llm_instance.structured_predict.return_value = GuardResult(reasoning="Expected reasoning", success=True)
        yield mock_llm_instance


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('an agent description "{description}"'), target_fixture="agent_description")
def _(description, locale_handler):
    return LocaleString(**{locale_handler.locale: description})


@given(parsers.parse('a user query "{query}"'), target_fixture="user_query")
def _(query):
    return query


@given("the following messages:", target_fixture="messages")
def _(datatable):
    messages = []
    for row in datatable[1:]:
        role = MessageRole[row[0]]
        content = row[1]
        messages.append(ChatMessage(role=role, content=content))
    return messages


@when("the agent description guard is executed")
@async_test
async def _(agent_description, llm, locale_handler, user_query, messages):
    await agent_description_guard(
        agent_description=agent_description,
        llm=llm,
        t=locale_handler,
        user_query=user_query,
        messages=messages,
    )


@then("structured_predict should be called", target_fixture="call_args")
def _(llm):
    llm.structured_predict.assert_called()
    call_args = llm.structured_predict.call_args
    return call_args


@then("structured_predict should be called with prompt:")
def _(call_args, locale_handler, docstring):
    prompt = PromptTemplate(locale_handler("lib.guards.agent_description_guard.prompt")).format(**call_args[1])
    assert prompt.strip() == docstring.strip()
