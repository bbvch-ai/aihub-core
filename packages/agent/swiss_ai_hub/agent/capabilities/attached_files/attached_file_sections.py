import asyncio
import logging
import math
import time
from array import array
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from datetime import UTC, datetime
from itertools import chain
from typing import Any, ClassVar
from uuid import uuid4
from weakref import WeakKeyDictionary

from llama_index.core import Document
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai import (
    DEFAULT_METADATA,
    EmbeddingQueryClamp,
    ExtractedDocument,
    IngestedNode,
    MarkdownStructuralNodeParser,
    rerank_nodes,
)
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService
from swiss_ai_hub.core.persistence import (
    CREATED_AT,
    DOCUMENT_TITLE,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    NODE_CONTENT_TYPE_TEXT,
    SOURCE,
    UPDATED_AT,
)

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_lexical_ranking import AttachedFileLexicalRanking
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_rank_fusion import AttachedFileRankFusion
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_section_cache import AttachedFileSectionCache
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig

logger = logging.getLogger(__name__)

# The embedding provider of the compose stacks fails from about 40 requests in flight and its quota is shared by every
# stage, so each agent process sends at most this many at once, whatever the number of files and users.
EMBEDDING_CONCURRENCY = 4
GOLDEN_RATIO_CONJUGATE = (math.sqrt(5) - 1) / 2


class AttachedFileSections:
    """An attached file split the way ingestion splits knowledge, and the sections that matter most for a query.

    The file's markdown goes through the same structural parser as ingested documents, so a section keeps its
    headings and a table is split between rows, never inside one. For a file too large to fit, the sections sharing
    the query's words are ranked lexically, a bounded set of candidates is embedded (or taken from the cache) and
    ranked by similarity, both rankings are fused, the best lexical matches are kept whatever the fusion says, and the
    shortlist is reranked the way retrieved knowledge is. Sections are then taken in rank order until the room is full.
    """

    _embedding_slots: ClassVar[WeakKeyDictionary[asyncio.AbstractEventLoop, asyncio.Semaphore]] = WeakKeyDictionary()

    def __init__(
        self,
        config: AttachedFilesConfig,
        token_counter: Callable[[str], list[int]],
        user: UserIdentity | None,
        cache: AttachedFileSectionCache | None = None,
    ) -> None:
        self._config = config
        self._token_counter = token_counter
        self._user = user
        self._cache = cache or AttachedFileSectionCache()

    @staticmethod
    def parse(document: ExtractedDocument, file_id: str, filename: str) -> list[IngestedNode]:
        """Text only: an upload's image links point nowhere the model could open."""
        now = int(time.time())
        metadata = {
            **DEFAULT_METADATA,
            SOURCE: filename,
            NAMESPACE: "",
            DOCUMENT_TITLE: document.title or filename,
            LANGUAGE: None,
            CREATED_AT: now,
            UPDATED_AT: now,
            INSERTED_AT: now,
        }
        parser = MarkdownStructuralNodeParser.from_defaults(metadata=metadata)
        nodes = parser.get_nodes_from_documents([Document(id_=file_id, text=document.content)])
        return [
            IngestedNode.from_llama_index_node(node).model_copy(update={"content_type": NODE_CONTENT_TYPE_TEXT})
            for node in nodes
        ]

    @staticmethod
    def restamp(sections: list[IngestedNode], file_id: str, filename: str, title: str) -> list[IngestedNode]:
        """Cached sections may come from another upload of the same content: the citation id derives from the
        document id, and node ids must stay unique when the same content is attached twice in one turn."""
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        return [
            section.model_copy(
                update={
                    "id": str(uuid4()),
                    "document_id": file_id,
                    "source": filename,
                    "document_title": title,
                    "created_at": now,
                    "updated_at": now,
                    "inserted_at": now,
                }
            )
            for section in sections
        ]

    async def rank(
        self, sections: list[IngestedNode], query: str, content_sha256: str | None = None
    ) -> list[IngestedNode]:
        """The sections, most relevant first. Embeddings already computed for this content are reused, and new ones
        are kept for the next question about it. When embedding fails, the sections sharing the query's words are
        still reranked: the reranker is another model, and an embedding group in cooldown would otherwise cost the
        turn every exact match and leave it with the file's beginning."""
        relevance_query = EmbeddingQueryClamp.clamp(query, model_name=self._config.embedding_model.model_name)
        lexical = await asyncio.to_thread(AttachedFileLexicalRanking.rank, sections, relevance_query)
        try:
            dense, keep_embeddings = await self._dense(sections, lexical, relevance_query, content_sha256)
        except Exception:
            if not lexical:
                raise
            logger.warning("[attached-files] Could not embed, ranking by the query's words alone", exc_info=True)
            dense, keep_embeddings = [], None
        shortlist = self.shortlist(lexical, dense)
        reranking_model = self._config.reranking_model.model_copy(update={"top_n": len(shortlist)})
        reranking = rerank_nodes(shortlist, relevance_query, reranking_model, self._user)
        if keep_embeddings is None:
            return await reranking
        reranked, _ = await asyncio.gather(reranking, keep_embeddings)
        return reranked

    async def _dense(
        self, sections: list[IngestedNode], lexical: list[IngestedNode], query: str, content_sha256: str | None
    ) -> tuple[list[IngestedNode], Coroutine[Any, Any, None] | None]:
        """The candidates in embedding order, and the write keeping new embeddings for the next question, if any."""
        model = self._embedding_model_key()
        digest = await asyncio.to_thread(AttachedFileSectionCache.sections_digest, sections) if content_sha256 else ""
        cached = await self._cache.embeddings(content_sha256, model, digest) if content_sha256 else {}
        candidates = self._candidates(sections, lexical, cached)
        uncached = [section for section in candidates if self._key(section) not in cached]
        query_embedding, embedded = await self._embed(query, uncached)
        # A model alias pointed at another model changes the width under the same key; its old vectors are dropped.
        usable = {key: vector for key, vector in cached.items() if len(vector) == len(query_embedding)}
        vectors = {**usable, **embedded}
        dense = await asyncio.to_thread(self.dense_order, candidates, vectors, query_embedding)
        if not content_sha256 or (not embedded and len(usable) == len(cached)):
            return dense, None
        return dense, self._cache.put_embeddings(content_sha256, model, vectors, digest)

    def shortlist(self, lexical: list[IngestedNode], dense: list[IngestedNode]) -> list[IngestedNode]:
        """Fusion alone can rank an exact identifier out: when most sections share some word with the query, one
        ranked first lexically and last by the embedding loses to dozens ranked a little lower in both."""
        pinned = lexical[: self._config.lexical_pinned]
        pinned_keys = {self._key(section) for section in pinned}
        fused = AttachedFileRankFusion.fuse([lexical, dense])
        rest = [section for section in fused if self._key(section) not in pinned_keys]
        return [*pinned, *rest][: max(self._config.shortlist_size, len(pinned))]

    def fill(self, sections: list[IngestedNode], room: int) -> list[IngestedNode]:
        """The sections that fit `room`, taken in the given order and returned in document order."""
        chosen: list[IngestedNode] = []
        remaining = room
        for section in sections:
            tokens = len(self._token_counter(section.content))
            if tokens <= remaining:
                chosen.append(section)
                remaining -= tokens
        return sorted(chosen, key=lambda section: section.index or 0)

    def fill_leading(self, sections: list[IngestedNode], room: int) -> list[IngestedNode]:
        """The sections that fit `room`, from the first on and without a gap, for pages read in order."""
        chosen: list[IngestedNode] = []
        remaining = room
        for section in sections:
            tokens = len(self._token_counter(section.content))
            if tokens > remaining:
                break
            chosen.append(section)
            remaining -= tokens
        return chosen

    @staticmethod
    def dense_order(
        sections: list[IngestedNode], vectors: dict[int, array], query_embedding: Sequence[float]
    ) -> list[IngestedNode]:
        """Run in a thread: a fully cached large file is thousands of vectors compared in pure Python."""
        query_norm = math.sqrt(sum(value * value for value in query_embedding))
        scored = [
            (AttachedFileSections.cosine(query_embedding, vectors[key], query_norm), section)
            for section in sections
            if (key := AttachedFileSections._key(section)) in vectors
        ]
        return [section for _, section in sorted(scored, key=lambda pair: pair[0], reverse=True)]

    @staticmethod
    def spread(sections: list[IngestedNode]) -> list[IngestedNode]:
        """Sections in an order whose every prefix covers the whole file, so a question sharing no word with it still
        gets candidates from its beginning to its end."""
        count = len(sections)
        positions = dict.fromkeys(int((step * GOLDEN_RATIO_CONJUGATE) % 1 * count) for step in range(count))
        order = [*positions, *(position for position in range(count) if position not in positions)]
        return [sections[position] for position in order]

    @staticmethod
    def cosine(left: Sequence[float], right: Sequence[float], left_norm: float | None = None) -> float:
        """`left_norm` spares recomputing the query's norm for every section."""
        if left_norm is None:
            left_norm = math.sqrt(sum(value * value for value in left))
        norm = left_norm * math.sqrt(sum(value * value for value in right))
        return sum(a * b for a, b in zip(left, right, strict=True)) / norm if norm else 0.0

    def _candidates(
        self, sections: list[IngestedNode], lexical: list[IngestedNode], cached: dict[int, array]
    ) -> list[IngestedNode]:
        """Every section already embedded, plus as many more as `max_embedded_chars` allows: the lexical matches
        first, then sections spread over the file."""
        chosen = [section for section in sections if self._key(section) in cached]
        taken = {self._key(section) for section in chosen}
        room = self._config.max_embedded_chars
        for section in chain(lexical, self.spread(sections)):
            key = self._key(section)
            if key in taken or len(section.content) > room:
                continue
            taken.add(key)
            chosen.append(section)
            room -= len(section.content)
        return chosen

    async def _embed(self, query: str, sections: list[IngestedNode]) -> tuple[list[float], dict[int, array]]:
        """The query and the sections, a few batches at a time. One failure cancels the rest, which a bare gather
        left running against the provider for a minute after the turn had given up."""
        api_key = await LiteLLMService.api_key_for_user(self._user) if self._user else None
        embed_model, _ = self._config.embedding_model.to_llama_index(api_key=api_key)
        size = embed_model.embed_batch_size
        batches = [sections[start : start + size] for start in range(0, len(sections), size)]
        slots = self._slots()

        async def in_a_slot[T](call: Callable[[], Awaitable[T]]) -> T:
            async with slots:
                return await call()

        try:
            async with asyncio.TaskGroup() as group:
                query_task = group.create_task(in_a_slot(lambda: embed_model.aget_query_embedding(query)))
                batch_tasks = [
                    group.create_task(
                        in_a_slot(lambda batch=batch: embed_model.aget_text_embedding_batch([s.content for s in batch]))
                    )
                    for batch in batches
                ]
        except ExceptionGroup as failure:
            raise failure.exceptions[0] from failure
        finally:
            await embed_model.aclose()
        embedded = {
            self._key(section): array("f", vector)
            for batch, task in zip(batches, batch_tasks, strict=True)
            for section, vector in zip(batch, task.result(), strict=True)
        }
        return query_task.result(), embedded

    @classmethod
    def _slots(cls) -> asyncio.Semaphore:
        """One per event loop: a semaphore binds to the loop it first waits on, and a second loop (a second test)
        would be refused it."""
        loop = asyncio.get_running_loop()
        if loop not in cls._embedding_slots:
            cls._embedding_slots[loop] = asyncio.Semaphore(EMBEDDING_CONCURRENCY)
        return cls._embedding_slots[loop]

    def _embedding_model_key(self) -> str:
        """The model and its vector width: the same model can be configured to a different number of dimensions."""
        model = self._config.embedding_model
        return f"{model.model_name}:{model.default_parameter.dimensions or 'native'}"

    @staticmethod
    def _key(section: IngestedNode) -> int:
        return section.index or 0
