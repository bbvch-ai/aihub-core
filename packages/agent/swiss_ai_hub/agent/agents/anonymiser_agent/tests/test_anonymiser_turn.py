import re
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from pydantic import SecretStr
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, MemoryStorageRequestedEvent
from swiss_ai_hub.core.infrastructure import AnalyzerSpan, PresidioAnalyzerClient, PresidioAnalyzerSettings

from swiss_ai_hub.agent.agents.anonymiser_agent.anonymiser_agent import AnonymiserAgent
from swiss_ai_hub.agent.agents.anonymiser_agent.anonymiser_turn import AnonymiserTurn
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

KNOWN_VALUES = {
    "Anna Muster": "PERSON",
    "Peter Meier": "PERSON",
    "anna.muster@example.ch": "EMAIL_ADDRESS",
    "Bahnhofstrasse 1, 8001 Zürich": "CH_ADDRESS",
}
LETTER = "Liebe Anna Muster, bitte bestätigen Sie Ihre Adresse Bahnhofstrasse 1, 8001 Zürich an anna.muster@example.ch."


class FakeAnalyzer:
    """Finds the known values, the way the analyzer would, and counts how often it was asked."""

    def __init__(self) -> None:
        self.calls = 0

    async def analyze(
        self, text: str, entities: list[str], allow_list_pattern: str | None = None
    ) -> list[AnalyzerSpan]:
        self.calls += 1
        return [
            AnalyzerSpan(entity_type=entity_type, start=match.start(), end=match.end())
            for value, entity_type in KNOWN_VALUES.items()
            for match in re.finditer(re.escape(value), text)
        ]


class FakeThreadContext:
    def __init__(self) -> None:
        self.store: dict = {}

    async def get(self, key, default=None):
        return self.store.get(key, default)

    async def set(self, key, value):
        self.store[key] = value


@pytest.fixture
def displayer() -> MagicMock:
    displayer = MagicMock()
    displayer.display_chunk = AsyncMock()
    displayer.display_thought = AsyncMock()
    displayer.display_event = AsyncMock()
    return displayer


@pytest.fixture
def t() -> AgentLocaleHandler:
    return AgentLocaleHandler("en")


def code_block_of(reply: str) -> str:
    return re.search(r"```text\n(.*)\n```", reply, re.DOTALL).group(1)


async def send(text: str, chat: FakeThreadContext, displayer: MagicMock, t: AgentLocaleHandler, analyzer=None) -> str:
    stop = await AnonymiserTurn.answer(text, analyzer or FakeAnalyzer(), displayer, chat, t)
    return stop.output_messages[0].content


@pytest.mark.asyncio
async def test_should_replace_every_detected_entity_with_a_placeholder(displayer, t) -> None:
    reply = await send(LETTER, FakeThreadContext(), displayer, t)

    assert code_block_of(reply) == (
        "Liebe <PERSON_1>, bitte bestätigen Sie Ihre Adresse <CH_ADDRESS_2> an <EMAIL_ADDRESS_3>."
    )
    assert not any(value in reply for value in KNOWN_VALUES)


@pytest.mark.asyncio
async def test_should_show_the_answer_it_returns(displayer, t) -> None:
    reply = await send(LETTER, FakeThreadContext(), displayer, t)

    displayer.display_chunk.assert_awaited_once_with(reply, model_name=AnonymiserTurn.SOURCE_NAME)


@pytest.mark.asyncio
async def test_should_restore_an_answer_with_a_placeholder_repeated_several_times(displayer, t) -> None:
    chat = FakeThreadContext()
    await send(LETTER, chat, displayer, t)
    analyzer = FakeAnalyzer()

    reply = await send(
        "Dear <PERSON_1>, we wrote to <EMAIL_ADDRESS_3>. <PERSON_1> lives at <CH_ADDRESS_2>. Thanks, <PERSON_1>!",
        chat,
        displayer,
        t,
        analyzer,
    )

    assert reply == (
        f"{t('agent.anonymiser_agent.messages.restored')}\n\n"
        "Dear Anna Muster, we wrote to anna.muster@example.ch. Anna Muster lives at Bahnhofstrasse 1, 8001 Zürich. "
        "Thanks, Anna Muster!"
    )
    assert analyzer.calls == 0


@pytest.mark.asyncio
async def test_should_keep_a_separator_a_separator_when_the_pasted_answer_lost_its_blank_lines(displayer, t) -> None:
    chat = FakeThreadContext()
    await send(LETTER, chat, displayer, t)

    reply = await send("Variante 1 für <PERSON_1>\r\n---\r\nVariante 2\r\n===\r\nEnde", chat, displayer, t)

    assert reply.split("\n\n", 1)[1] == "Variante 1 für Anna Muster\n\n---\nVariante 2\n\n===\nEnde"


@pytest.mark.asyncio
async def test_should_give_the_same_person_the_same_placeholder_in_later_messages(displayer, t) -> None:
    chat = FakeThreadContext()
    await send(LETTER, chat, displayer, t)

    reply = await send("Peter Meier trifft Anna Muster.", chat, displayer, t)

    assert code_block_of(reply) == "<PERSON_4> trifft <PERSON_1>."


@pytest.mark.asyncio
async def test_should_not_restore_another_chats_placeholders(displayer, t) -> None:
    await send(LETTER, FakeThreadContext(), displayer, t)

    reply = await send("Bitte <PERSON_1> zurückrufen.", FakeThreadContext(), displayer, t)

    assert "Anna Muster" not in reply
    assert "`<PERSON_1>`" in reply.split("\n\n")[-1]


@pytest.mark.asyncio
async def test_should_point_out_placeholders_this_chat_never_issued(displayer, t) -> None:
    chat = FakeThreadContext()
    await send(LETTER, chat, displayer, t)

    reply = await send("<PERSON_1> und <PERSON_9>", chat, displayer, t)

    assert reply.split("\n\n")[1] == "Anna Muster und <PERSON_9>"
    assert reply.endswith(t("agent.anonymiser_agent.messages.unknown_placeholders", placeholders="`<PERSON_9>`"))


@pytest.mark.asyncio
async def test_should_keep_a_text_without_personal_data_unchanged(displayer, t) -> None:
    chat = FakeThreadContext()

    reply = await send("Das Meeting ist am Montag.", chat, displayer, t)

    assert reply == t("agent.anonymiser_agent.messages.nothing_found")


@pytest.mark.asyncio
async def test_should_name_the_chat_once_without_its_content(displayer, t) -> None:
    chat = FakeThreadContext()
    await send(LETTER, chat, displayer, t)
    await send("<PERSON_1>", chat, displayer, t)

    events = [call.args[0] for call in displayer.display_event.await_args_list]
    assert [(type(event), event.title) for event in events] == [
        (ConversationTitleEvent, t("agent.anonymiser_agent.title"))
    ]


@pytest.mark.asyncio
async def test_should_fence_the_text_beyond_its_own_backticks(displayer, t) -> None:
    reply = await send("Anna Muster schickt:\n```\ncode\n```", FakeThreadContext(), displayer, t)

    assert "````text\n<PERSON_1> schickt:\n```\ncode\n```\n````" in reply


@pytest.mark.asyncio
async def test_should_ask_for_a_text_when_the_message_is_empty(displayer, t) -> None:
    reply = await send("  ", FakeThreadContext(), displayer, t)

    assert reply == t("agent.anonymiser_agent.messages.empty")


@pytest.mark.asyncio
async def test_should_call_only_the_analyzer_and_no_model(displayer, t, monkeypatch: pytest.MonkeyPatch) -> None:
    hosts: list[str] = []

    def answer(request: httpx.Request) -> httpx.Response:
        hosts.append(f"{request.url.host}{request.url.path}")
        return httpx.Response(200, json=[{"entity_type": "PERSON", "start": 0, "end": 11, "score": 0.9}])

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(answer), **kwargs)
    )
    analyzer = PresidioAnalyzerClient(PresidioAnalyzerSettings(API_BASE="http://analyzer", API_KEY=SecretStr("k")))
    chat = FakeThreadContext()

    await send("Anna Muster ruft an.", chat, displayer, t, analyzer)
    await send("<PERSON_1> called back.", chat, displayer, t, analyzer)

    assert hosts == ["analyzer/analyze"]


def test_should_hand_nothing_to_memory() -> None:
    assert MemoryStorageRequestedEvent not in AnonymiserAgent.get_output_events()
