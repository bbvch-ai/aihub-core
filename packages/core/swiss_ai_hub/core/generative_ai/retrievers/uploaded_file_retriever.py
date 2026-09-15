import asyncio
import logging
from typing import Annotated, Any

from llama_index.core.schema import NodeWithScore, TextNode
from pymilvus import MilvusClient

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.retrievers.base_retriever import BaseRetriever
from swiss_ai_hub.core.generative_ai.retrievers.uploaded_file_retriever_config import UploadedFileRetrieverConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService
from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    INDEX,
    NAMESPACE,
    SOURCE,
    SOURCE_ORIGIN,
)

logger = logging.getLogger(__name__)


class UploadedFileRetriever(BaseRetriever):
    """Retrieves from the vectors the chat client produced when the user uploaded the file.

    Open WebUI parses every upload through this platform's own parsing API, embeds it with the model this
    platform configures, and writes it to this platform's Milvus — one collection per file. Re-parsing the
    same document inside the agent costs seconds per file and yields the same vectors, so this reads what
    is already there instead.

    The one-collection-per-file layout is also what isolates one user's uploads from another's: there is
    no shared collection to filter, and a file id the caller never received names a collection it cannot
    guess.
    """

    COLLECTION_PREFIX: str = "open_webui_file_"
    VECTOR_FIELD: str = "vector"
    SOURCE_ORIGIN_NAME: str = "user_upload"

    DECISIVELY_BETTER_MATCH: float = 0.1
    """How far another attachment must out-score the one just attached before it leads the prompt instead.

    Naming a document in the question lifts it clear of the field — a question naming one of eleven
    attachments scored it 0.759 against a next-best 0.493 — while a question that names nothing leaves the
    attachments within a few hundredths of each other, 0.519 down to 0.368 across the same eleven. A margin
    of this size is what separates "the user pointed at another file" from "nothing here is singled out, so
    the reference is the file they just attached".
    """

    def __init__(
        self,
        config: UploadedFileRetrieverConfig,
        files: Annotated[list[UserUploadedFile], "Files carried by the start event"],
    ):
        super().__init__(config)
        self.config: UploadedFileRetrieverConfig = config
        self.files: list[UserUploadedFile] = [file for file in files if file.source_file_id]

    @classmethod
    def collection_name_for(cls, source_file_id: str) -> str:
        """Open WebUI names a per-file collection ``file-<id>`` and sanitises ``-`` to ``_`` for Milvus."""
        return f"{cls.COLLECTION_PREFIX}{source_file_id.replace('-', '_')}"

    @trace_fn
    async def retrieve(self, query: str, t: LocaleHandler, user: UserIdentity | None = None) -> list[IngestedNode]:
        if not self.files:
            return []

        embedding = await self._embed_query(query, user)

        settings = MilvusSettings()
        client = MilvusClient(uri=settings.URL, token=settings.get_token())

        results = await asyncio.gather(*[self._search_file(client, file, embedding) for file in self.files])
        return self._ordered_for_the_prompt([node for file_nodes in results for node in file_nodes])

    def _ordered_for_the_prompt(self, nodes: list[IngestedNode]) -> list[IngestedNode]:
        """Order the attachments against each other, which the merge with the knowledge nodes cannot do.

        Every node here came from the same chat client, the same embedding model and the same COSINE index,
        so unlike the uploaded-versus-knowledge merge these scores really are one scale. Left in gather
        order the set is ordered by when the user attached each file, and the downstream combiner groups by
        document in first-appearance order — so the oldest attachment of the thread leads the prompt however
        little it has to do with the question.

        What the user attached to *this* message then leads, because "this document" is a reference no
        similarity score carries — but only while nothing else is decisively a better match. A question
        that names an earlier file scores that file far above the field, and it has to win: the reference
        is only ambiguous when the user did not resolve it themselves.
        """
        by_score = sorted(nodes, key=self._score_of, reverse=True)
        current_turn = {file.source_file_id for file in self.files if file.attached_in_current_turn}
        if not current_turn or not by_score:
            return by_score

        just_attached = [node for node in by_score if node.namespace in current_turn]
        carried = [node for node in by_score if node.namespace not in current_turn]
        if not just_attached:
            return by_score

        beaten_by = self._score_of(by_score[0]) - self._score_of(just_attached[0])
        if beaten_by > self.DECISIVELY_BETTER_MATCH:
            return by_score
        return [*just_attached, *carried]

    @staticmethod
    def _score_of(node: IngestedNode) -> float:
        """An absent score sorts last rather than ahead of every real match."""
        return node.score if node.score is not None else float("-inf")

    async def _embed_query(self, query: str, user: UserIdentity | None) -> list[float]:
        api_key = await LiteLLMService.api_key_for_user(user) if user else None
        embed_model, _ = self.config.embed_model.to_llama_index(api_key=api_key)
        return await embed_model.aget_query_embedding(query)

    async def _search_file(
        self,
        client: MilvusClient,
        file: UserUploadedFile,
        embedding: list[float],
    ) -> list[IngestedNode]:
        collection = self.collection_name_for(file.source_file_id)

        if not await asyncio.to_thread(client.has_collection, collection):
            logger.warning(
                "Uploaded file has no vector collection yet; answering without it. filename=%s collection=%s",
                file.filename,
                collection,
            )
            return []

        await asyncio.to_thread(client.load_collection, collection)
        hits = await asyncio.to_thread(
            client.search,
            collection_name=collection,
            data=[embedding],
            anns_field=self.VECTOR_FIELD,
            limit=self.config.retrieve_k,
            output_fields=["data", "metadata"],
        )

        return [self._to_ingested_node(hit, file, index) for index, hit in enumerate(hits[0] if hits else [])]

    def _to_ingested_node(self, hit: dict[str, Any], file: UserUploadedFile, index: int) -> IngestedNode:
        entity = hit.get("entity") or {}
        metadata = dict(entity.get("metadata") or {})
        metadata.update(
            {
                SOURCE: file.filename,
                SOURCE_ORIGIN: self.SOURCE_ORIGIN_NAME,
                NAMESPACE: file.source_file_id,
                DOCUMENT_ID: file.source_file_id,
                DOCUMENT_TITLE: file.filename,
                INDEX: metadata.get(INDEX, index),
            }
        )
        node = TextNode(id_=str(hit.get("id")), text=(entity.get("data") or {}).get("text", ""), metadata=metadata)
        return IngestedNode.from_llama_index_node_with_score(NodeWithScore(node=node, score=hit.get("distance")))
