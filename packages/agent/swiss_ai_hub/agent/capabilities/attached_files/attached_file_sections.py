import asyncio
import math
import time
from collections.abc import Callable

from llama_index.core import Document
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai import (
    DEFAULT_METADATA,
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

from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig


class AttachedFileSections:
    """An attached file split the way ingestion splits knowledge, and the sections that matter most for a query.

    The file's markdown goes through the same structural parser as ingested documents, so a section keeps its
    headings and a table is split between rows, never inside one. For a file too large to fit, the query and the
    sections are embedded to shortlist the closest ones, the shortlist is reranked the way retrieved knowledge is,
    and sections are taken in rank order until the room is full.
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

    async def rank(self, sections: list[IngestedNode], query: str) -> list[IngestedNode]:
        """The sections, most relevant first."""
        api_key = await LiteLLMService.api_key_for_user(self._user) if self._user else None
        embed_model, _ = self._config.embedding_model.to_llama_index(api_key=api_key)
        query_embedding, section_embeddings = await asyncio.gather(
            embed_model.aget_query_embedding(query),
            embed_model.aget_text_embedding_batch([section.content for section in sections]),
        )
        similarity = {
            section.id: self.cosine(query_embedding, embedding)
            for section, embedding in zip(sections, section_embeddings, strict=True)
        }
        shortlist = sorted(sections, key=lambda section: similarity[section.id], reverse=True)[
            : self._config.shortlist_size
        ]
        reranking_model = self._config.reranking_model.model_copy(update={"top_n": len(shortlist)})
        return await rerank_nodes(shortlist, query, reranking_model, self._user)

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
    def cosine(left: list[float], right: list[float]) -> float:
        norm = math.sqrt(sum(value * value for value in left)) * math.sqrt(sum(value * value for value in right))
        return sum(a * b for a, b in zip(left, right, strict=True)) / norm if norm else 0.0
