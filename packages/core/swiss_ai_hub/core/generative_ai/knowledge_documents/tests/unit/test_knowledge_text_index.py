import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents import knowledge_text_index
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index import KnowledgeTextIndex
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_query import KnowledgeTextIndexQuery

pytestmark = pytest.mark.unit


def test_string_ids_are_read_from_their_quoted_text() -> None:
    assert KnowledgeTextIndex._ids([('"abc123"',), ('"we"ird\\id"',)]) == ["abc123", 'we"ird\\id']


@pytest.mark.parametrize("value", ["5", "null", None, '"', '{ "a" : 1 }'])
def test_an_id_that_is_not_a_string_sends_the_search_to_the_scan(value: str | None) -> None:
    assert KnowledgeTextIndex._ids([('"abc"',), (value,)]) is None


def test_too_many_candidates_send_the_search_to_the_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(knowledge_text_index, "MAX_INDEX_CANDIDATES", 2)

    assert KnowledgeTextIndex._ids([('"a"',), ('"b"',)]) == ["a", "b"]
    assert KnowledgeTextIndex._ids([('"a"',), ('"b"',), ('"c"',)]) is None


@pytest.mark.asyncio
async def test_without_a_password_no_connection_is_made(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_PASSWORD", "")
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_HOST", "host.invalid")
    query = KnowledgeTextIndexQuery.from_query("Rechnung", is_regex=False, case_sensitive=False)

    assert await KnowledgeTextIndex.candidate_ids(["kb1", "kb2"], query, 1.0) == {"kb1": None, "kb2": None}


@pytest.mark.asyncio
async def test_an_unreachable_server_sends_every_database_to_the_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_PASSWORD", "secret")
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_HOST", "127.0.0.1")
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_PORT", "9")
    query = KnowledgeTextIndexQuery.from_query("Rechnung", is_regex=False, case_sensitive=False)

    assert await KnowledgeTextIndex.candidate_ids(["kb1"], query, 1.0) == {"kb1": None}
