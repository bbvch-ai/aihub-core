import asyncio
import logging
import math
from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import NodeWithScore, TextNode
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig

logger = logging.getLogger(__name__)

SECTION_TOKENS = 400
# How many embedding matches the reranker orders; the reranker is the slower and better judge, so it sees a
# shortlist rather than every section of a long document.
SHORTLIST_SIZE = 40
EXCERPT_SEPARATOR = "\n\n[…]\n\n"


class AttachedFileSectionSelector:
    """Picks the sections of a file that fit `room` tokens and matter most for the query.

    A file that does not fit whole used to keep only its beginning, which answers nothing about a later chapter. It
    is split into sections, the query and the sections are embedded to shortlist the closest ones, the shortlist is
    reranked, and sections are taken in rank order until the room is full, then put back in document order so the
    excerpt still reads top to bottom.
    """

    def __init__(
        self,
        config: AttachedFilesConfig,
        token_counter: Callable[[str], list[int]],
        user: UserIdentity | None,
    ) -> None:
        self._config = config
        self._token_counter = token_counter
        self._user = user

    def split(self, text: str) -> list[str]:
        splitter = SentenceSplitter(
            chunk_size=SECTION_TOKENS,
            chunk_overlap=0,
            tokenizer=lambda chunk: [0] * len(self._token_counter(chunk)),
        )
        return [section for section in splitter.split_text(text) if section.strip()]

    async def select(self, text: str, query: str, room: int) -> str:
        sections = self.split(text)
        ranking = await self.rank(sections, query)
        chosen: list[int] = []
        remaining = room
        for index in ranking:
            tokens = len(self._token_counter(sections[index]))
            if tokens <= remaining:
                chosen.append(index)
                remaining -= tokens
        return EXCERPT_SEPARATOR.join(sections[index] for index in sorted(chosen))

    async def rank(self, sections: list[str], query: str) -> list[int]:
        """Section indices, most relevant first."""
        api_key = await LiteLLMService.api_key_for_user(self._user) if self._user else None
        embed_model, _ = self._config.embedding_model.to_llama_index(api_key=api_key)
        query_embedding, section_embeddings = await asyncio.gather(
            embed_model.aget_query_embedding(query), embed_model.aget_text_embedding_batch(sections)
        )
        similarities = [self.cosine(query_embedding, embedding) for embedding in section_embeddings]
        shortlist = sorted(range(len(sections)), key=lambda index: similarities[index], reverse=True)[:SHORTLIST_SIZE]

        reranker, _ = self._config.reranking_model.to_llama_index(api_key=api_key)
        reranker.top_n = len(shortlist)
        nodes = [NodeWithScore(node=TextNode(text=sections[index], id_=str(index))) for index in shortlist]
        reranked = await asyncio.to_thread(reranker.postprocess_nodes, nodes, query_str=query)
        return [int(node.node.node_id) for node in reranked]

    @staticmethod
    def cosine(left: list[float], right: list[float]) -> float:
        norm = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
        return sum(a * b for a, b in zip(left, right, strict=True)) / norm if norm else 0.0
