import pytest
from llama_index.core.base.llms.types import ChatMessage
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.chat_history.limit_chat_history import limit_chat_history
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


scenarios("./features/limit_chat_history.feature")


@pytest.fixture
def chat_message_factory():
    def _create_message(content: str):
        return ChatMessage(role="user", content=content, token_count=len(content.split()))

    return _create_message


@given(parsers.parse("a chat history with {count:d} messages"), target_fixture="chat_history")
def _(count, chat_message_factory):
    return [chat_message_factory(f"Message {i}") for i in range(count)]


@given(parsers.parse("a token limit configuration of {token_limit:d} tokens"), target_fixture="config")
def _(token_limit):
    return {
        "number_of_input_tokens": token_limit,
    }


@when("the limit chat history step is executed", target_fixture="limited_history")
def _(config, chat_history):
    return limit_chat_history(
        number_of_input_tokens=config["number_of_input_tokens"],
        chat_history=chat_history,
    )


@then(parsers.parse("the limited chat history should contain {expected_count:d} messages"))
def _(expected_count, limited_history):
    assert len(limited_history) == expected_count


@then("the limited chat history should contain all messages")
def _(limited_history, chat_history):
    assert len(limited_history) == len(chat_history)


@then("the limited chat history should contain fewer messages")
def _(limited_history, chat_history):
    assert len(limited_history) < len(chat_history)
