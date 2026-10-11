"""Ranking a file too large to fit: lexical and dense evidence fused, exact identifiers kept, the embedding requests
bounded, and the sections and embeddings of a file kept so a later question costs a lookup."""

import asyncio
from array import array
from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import EndpointConnectionError
from swiss_ai_hub.core.events.agent import UserUploadedFile
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    ExtractedDocument,
    IngestedNode,
    ParseCacheBucket,
)

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_lexical_ranking import AttachedFileLexicalRanking
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_rank_fusion import AttachedFileRankFusion
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import AttachedFileReader
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_section_cache import AttachedFileSectionCache
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections import (
    EMBEDDING_CONCURRENCY,
    AttachedFileSections,
)
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig

SECTIONS_MODULE = "swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections"
READER_MODULE = "swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader"
IDENTIFIER = "ORD-145678"


def _section(index: int, content: str) -> IngestedNode:
    return IngestedNode(
        id=f"node-{index}",
        content=content,
        document_id="file-1",
        source="orders.xlsx",
        namespace="",
        index=index,
        created_at="2026-10-11T00:00:00Z",
        updated_at="2026-10-11T00:00:00Z",
        inserted_at="2026-10-11T00:00:00Z",
    )


def _table(rows: int = 1000, identifier_at: int = 870) -> list[IngestedNode]:
    """Sections that all share the query's common words, one of them holding the identifier."""
    return [
        _section(
            index,
            f"| ORD-{100000 + index} | order status shipped | region North | units {index % 50} |"
            if index != identifier_at
            else f"| {IDENTIFIER} | order status open | region West | units 7 |",
        )
        for index in range(rows)
    ]


def _counter(text: str) -> list[int]:
    return [0] * len(text.split())


class FakeEmbedModel:
    """Embeds every text alike except the ones holding `outlier`, which point away from the query; records how many
    requests are in flight at once."""

    embed_batch_size = 10

    def __init__(self, outlier: str = IDENTIFIER, fail_query: bool = False, delay: float = 0.01) -> None:
        self.outlier = outlier
        self.fail_query = fail_query
        self.delay = delay
        self.in_flight = 0
        self.peak = 0
        self.texts: list[str] = []
        self.batches_finished = 0

    async def _request(self) -> None:
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
        finally:
            self.in_flight -= 1

    async def aget_query_embedding(self, query: str) -> list[float]:
        await self._request()
        if self.fail_query:
            raise RuntimeError("embedding provider down")
        return [1.0, 0.0]

    async def aget_text_embedding_batch(self, texts: list[str]) -> list[list[float]]:
        self.texts.extend(texts)
        await self._request()
        self.batches_finished += 1
        return [[0.0, 1.0] if self.outlier in text else [1.0, 0.1] for text in texts]


def _picker(config: AttachedFilesConfig | None = None) -> AttachedFileSections:
    return AttachedFileSections(config or AttachedFilesConfig(), _counter, None)


def _patched(model: FakeEmbedModel):
    return (
        patch.object(EmbeddingModelConfig, "to_llama_index", return_value=(model, None)),
        patch(f"{SECTIONS_MODULE}.rerank_nodes", new=AsyncMock(side_effect=lambda nodes, *_args, **_kwargs: nodes)),
    )


class TestLexicalRanking:
    def test_an_identifier_deep_in_a_table_ranks_first(self):
        ranked = AttachedFileLexicalRanking.rank(_table(), f"What is the status of order {IDENTIFIER}?")

        assert IDENTIFIER in ranked[0].content

    def test_the_parts_of_a_hyphenated_term_count(self):
        assert AttachedFileLexicalRanking.terms("status of ORD-145678") == [
            "status",
            "of",
            "ord-145678",
            "ord",
            "145678",
        ]

    def test_no_shared_word_ranks_nothing(self):
        assert AttachedFileLexicalRanking.rank(_table(10), "summarise the complaints") == []

    def test_a_word_found_almost_everywhere_never_lowers_a_score(self):
        assert AttachedFileLexicalRanking.idf(total=1000, containing=999) > 0


class TestFusionAndPinning:
    def test_reciprocal_rank_fusion_rewards_agreement(self):
        a, b, c = _section(0, "a"), _section(1, "b"), _section(2, "c")

        assert AttachedFileRankFusion.fuse([[a, b, c], [b, a, c]])[-1] == c

    @pytest.mark.asyncio
    async def test_an_identifier_ranked_last_by_the_embedding_still_reaches_the_reranker(self, in_memory_parse_cache):
        sections = _table()
        cache = AttachedFileSectionCache()
        vectors = {s.index: array("f", [0.0, 1.0] if IDENTIFIER in s.content else [1.0, 0.1]) for s in sections}
        await cache.put_embeddings("content-1", "embedding/bge-m3:native", vectors)
        model = FakeEmbedModel()
        embed, rerank = _patched(model)

        with embed, rerank as reranked:
            await _picker().rank(sections, f"status of order {IDENTIFIER}", "content-1")

        shortlist = reranked.await_args.args[0]
        assert IDENTIFIER in shortlist[0].content
        assert model.texts == []


class TestBoundedEmbedding:
    @pytest.mark.asyncio
    async def test_a_ranking_embeds_no_more_than_the_character_cap(self):
        model = FakeEmbedModel()
        config = AttachedFilesConfig(max_embedded_chars=5_000)
        embed, rerank = _patched(model)

        with embed, rerank:
            await _picker(config).rank(_table(), "summarise the open orders")

        assert sum(len(text) for text in model.texts) <= 5_000

    @pytest.mark.asyncio
    async def test_three_files_ranked_at_once_keep_the_requests_in_flight_bounded(self):
        model = FakeEmbedModel(delay=0.02)
        embed, rerank = _patched(model)

        with embed, rerank:
            await asyncio.gather(*(_picker().rank(_table(300), "region West") for _ in range(3)))

        assert 0 < model.peak <= EMBEDDING_CONCURRENCY

    @pytest.mark.asyncio
    async def test_a_failing_query_embedding_cancels_the_batches_and_surfaces_its_error(self):
        model = FakeEmbedModel(fail_query=True, delay=0.05)
        embed, rerank = _patched(model)

        with embed, rerank, pytest.raises(RuntimeError, match="embedding provider down"):
            await _picker().rank(_table(), "region West")

        finished = model.batches_finished
        await asyncio.sleep(0.2)
        assert model.batches_finished == finished
        assert model.in_flight == 0

    @pytest.mark.asyncio
    async def test_the_concurrency_limit_works_on_a_new_event_loop(self):
        """Pytest gives this test a loop of its own; a semaphore bound to an earlier test's loop would refuse it."""
        model = FakeEmbedModel()
        embed, rerank = _patched(model)

        with embed, rerank:
            await _picker().rank(_table(100), "region West")

        assert model.peak >= 1


def _upload(file_id: str = "7f1c6a8e-3b2d-4c5e-9f10-2a3b4c5d6e7f", name: str = "handbook.pdf") -> UserUploadedFile:
    return UserUploadedFile(filename=name, file_type="application/pdf", file_id=file_id)


def _document(text: str = "# Handbook\n\nIntro.\n<!-- PageBreak -->\n## Remote\n\nTwo days.", pages: int = 2):
    return ExtractedDocument(
        title="Handbook",
        content=text,
        content_type="application/pdf",
        source_filename="handbook.pdf",
        document_parser="MineruLoader",
        number_of_pages=pages,
    )


class TestSectionCache:
    @pytest.mark.asyncio
    async def test_a_second_read_of_the_same_upload_needs_neither_download_nor_parse(self):
        extract = AsyncMock(return_value=_document())
        with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract):
            first, _ = await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())
            second, event = await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())

        assert extract.await_count == 1
        assert [s.content for s in second.sections] == [s.content for s in first.sections]
        assert second.is_paged and event.number_of_pages == 2

    @pytest.mark.asyncio
    async def test_the_same_file_id_under_another_profile_is_read_afresh(self):
        extract = AsyncMock(return_value=_document())
        with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract):
            await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())
            await AttachedFileReader.read(_upload(), "UniversalAgent", "b", AttachedFileSectionCache())

        assert extract.await_count == 2

    @pytest.mark.asyncio
    async def test_a_reupload_reuses_the_sections_under_its_own_identity(self):
        extract = AsyncMock(return_value=_document())
        other = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
        with (
            patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract),
            patch(f"{READER_MODULE}.AttachedFileSections.parse", wraps=AttachedFileSections.parse) as parse,
        ):
            first, _ = await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())
            again, _ = await AttachedFileReader.read(
                _upload(other, "copy.pdf"), "UniversalAgent", "a", AttachedFileSectionCache()
            )

        assert parse.call_count == 1
        assert {s.document_id for s in again.sections} == {other}
        assert {s.source for s in again.sections} == {"copy.pdf"}
        assert not {s.id for s in first.sections} & {s.id for s in again.sections}

    @pytest.mark.asyncio
    async def test_the_same_content_twice_in_one_turn_gets_unique_node_ids(self):
        other = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
        with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document())):
            outcomes = await AttachedFileReader.read_all([_upload(), _upload(other, "copy.pdf")], "UniversalAgent", "a")

        ids = [s.id for text, _ in outcomes for s in text.sections]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_a_record_whose_sections_expired_reads_the_file_again(self, in_memory_parse_cache):
        extract = AsyncMock(return_value=_document())
        with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract):
            await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())
            for key in [key for key in in_memory_parse_cache if key.endswith("sections.json")]:
                del in_memory_parse_cache[key]
            text, _ = await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())

        assert extract.await_count == 2
        assert text.sections

    @pytest.mark.asyncio
    async def test_an_unreachable_bucket_still_reads_the_file(self, monkeypatch):
        def unreachable(*_args):
            raise EndpointConnectionError(endpoint_url="http://seaweedfs-s3:9000")

        monkeypatch.setattr(ParseCacheBucket, "read", unreachable)
        monkeypatch.setattr(ParseCacheBucket, "write", unreachable)
        with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document())):
            text, _ = await AttachedFileReader.read(_upload(), "UniversalAgent", "a", AttachedFileSectionCache())

        assert text.sections

    @pytest.mark.asyncio
    async def test_embeddings_are_completed_and_kept_for_the_next_question(self):
        cache = AttachedFileSectionCache()
        sections = _table(40)
        await cache.put_embeddings("content-1", "embedding/bge-m3:native", {0: array("f", [1.0, 0.1])})
        model = FakeEmbedModel()
        embed, rerank = _patched(model)

        with embed, rerank:
            await _picker(AttachedFilesConfig(max_embedded_chars=1_000_000)).rank(sections, "region West", "content-1")

        stored = await cache.embeddings("content-1", "embedding/bge-m3:native")
        assert set(stored) == {s.index for s in sections}
        assert len(model.texts) == len(sections) - 1

    @pytest.mark.asyncio
    async def test_another_vector_width_does_not_reuse_embeddings(self):
        cache = AttachedFileSectionCache()
        await cache.put_embeddings("content-1", "embedding/bge-m3:native", {0: array("f", [1.0, 0.1])})
        default = AttachedFilesConfig().embedding_model
        narrower = default.model_copy(
            update={"default_parameter": default.default_parameter.model_copy(update={"dimensions": 512})}
        )
        config = AttachedFilesConfig(embedding_model=narrower)
        model = FakeEmbedModel()
        embed, rerank = _patched(model)

        with embed, rerank:
            await _picker(config).rank(_table(5), "region West", "content-1")

        assert len(model.texts) == 5

    def test_a_new_chunking_starts_a_fresh_cache(self, monkeypatch):
        before = AttachedFileSectionCache.sections_key("content-1")
        monkeypatch.setattr(AttachedFileSectionCache, "FORMAT", AttachedFileSectionCache.FORMAT + 1)

        assert AttachedFileSectionCache.sections_key("content-1") != before
