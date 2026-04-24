from llama_index.core.base.llms.types import ChatMessage
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.chat_history.format_chat_history import format_chat_history

scenarios("./features/format_chat_history.feature")

_MULTILINE_SYSTEM_CONTENT = """
<organizational_context>

## Organizational Memory Context

    The following information represents facts about the organization.

    **Organizational Facts:**
    - Vacation policy: 25 days per year
    - Sick leave: 10 days per year

</organizational_context>
"""


@given("an empty chat history", target_fixture="chat_history")
def _() -> list[ChatMessage]:
    return []


@given("a chat history:", target_fixture="chat_history")
def _(datatable) -> list[ChatMessage]:
    return [ChatMessage(role=row[0], content=row[1]) for row in datatable[1:]]


@given(
    "a chat history with a multi-line system message containing blank lines",
    target_fixture="chat_history",
)
def _() -> list[ChatMessage]:
    return [ChatMessage(role="system", content=_MULTILINE_SYSTEM_CONTENT)]


@when("the chat history is formatted", target_fixture="formatted")
def _(chat_history: list[ChatMessage]) -> str:
    return format_chat_history(chat_history)


@then(parsers.re(r'the result should equal "(?P<expected>.*)"'))
def _(formatted: str, expected: str) -> None:
    assert formatted == expected.replace("\\n", "\n")


@then("every non-empty content line from the input appears in the output")
def _(formatted: str) -> None:
    expected_lines = [line.strip() for line in _MULTILINE_SYSTEM_CONTENT.splitlines() if line.strip()]
    for line in expected_lines:
        assert line in formatted, f"Missing expected line: {line!r}"


@then("the content appears verbatim after the role header")
def _(formatted: str) -> None:
    assert formatted == f"system:\n{_MULTILINE_SYSTEM_CONTENT}"
