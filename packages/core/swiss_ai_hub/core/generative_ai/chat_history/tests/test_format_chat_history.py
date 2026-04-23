from llama_index.core.base.llms.types import ChatMessage
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.chat_history.format_chat_history import format_chat_history

scenarios("./features/format_chat_history.feature")


@given("an empty chat history", target_fixture="chat_history")
def _() -> list[ChatMessage]:
    return []


@given("a chat history:", target_fixture="chat_history")
def _(datatable) -> list[ChatMessage]:
    return [ChatMessage(role=row[0], content=row[1]) for row in datatable[1:]]


@when("the chat history is formatted", target_fixture="formatted")
def _(chat_history: list[ChatMessage]) -> str:
    return format_chat_history(chat_history)


@then(parsers.re(r'the result should equal "(?P<expected>.*)"'))
def _(formatted: str, expected: str) -> None:
    assert formatted == expected.replace("\\n", "\n")
