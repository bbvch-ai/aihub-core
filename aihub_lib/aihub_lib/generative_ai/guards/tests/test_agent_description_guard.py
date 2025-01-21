from unittest.mock import Mock, AsyncMock

import pytest
from llama_index.core import PromptTemplate
from pytest_bdd import scenarios, given, when, then, parsers
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.generative_ai.guards.agent_description_guard import (
    agent_description_guard,
    GuardResult,
)
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_lib.testing.asyncio_utils.bdd import async_test

scenarios("./features/agent_description_guard.feature")


@pytest.fixture
def llm_config():
    mock_llm = Mock(spec=ChatLLMConfig)
    mock_cost_reporting_llm = AsyncMock()
    mock_cost_reporting_llm.structured_predict.return_value = GuardResult(reasoning="Expected reasoning", success=True)
    mock_llm.cost_reporting_llm.return_value = mock_cost_reporting_llm
    return mock_llm


@pytest.fixture
def displayer():
    return Mock(spec=EventDisplayer)


@given(parsers.parse('a locale handler with locale "{locale}"'), target_fixture="locale_handler")
def _(locale):
    return LocaleHandler(locale=locale)


@given(parsers.parse('an agent description "{description}"'), target_fixture="agent_description")
def _(description):
    return description


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
async def _(agent_description, llm_config, displayer, locale_handler, user_query, messages):
    await agent_description_guard(
        agent_description=agent_description,
        llm_config=llm_config,
        displayer=displayer,
        t=locale_handler,
        user_query=user_query,
        messages=messages,
    )


@then("structured_predict should be called", target_fixture="call_args")
def _(llm_config):
    call_args = llm_config.cost_reporting_llm.return_value.__aenter__.return_value.structured_predict.call_args
    return call_args


@then("structured_predict should be called with prompt:")
def _(call_args, agent_description, locale_handler, user_query, docstring):
    prompt = PromptTemplate(locale_handler("lib.guards.agent_description_guard.prompt")).format(**call_args[1])
    assert prompt == docstring
