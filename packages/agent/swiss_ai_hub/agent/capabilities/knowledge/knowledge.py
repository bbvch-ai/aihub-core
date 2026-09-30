import asyncio
import logging
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.events.agent import KnowledgeReference, KnowledgeSearchedEvent, SearchKnowledgeEvent
from swiss_ai_hub.core.generative_ai import (
    IngestedNode,
    KnowledgeCollectionLabel,
    ReferencedKnowledge,
    UserScopedRetrievers,
    combine_nodes_in_order,
    rerank_nodes,
    retrieve_from_all_sources,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_config import KnowledgeConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class Knowledge(Capability):
    """
    The knowledge collections the user referenced on the message, as one call:

    - `search(references, query)` is answered with `KnowledgeSearchedEvent`, one context block with what those
      collections hold for the query, empty when nothing was referenced. Pass the block to `Conversation.compose(...)`
      next to the memories and attached files.

    It is independent of a knowledge agent's own configured retrieval: a reference adds a search on top. Only
    collections the asking user may read are searched; the others are named in the block so the answer says so.
    """

    calls: ClassVar[dict] = {SearchKnowledgeEvent: (KnowledgeSearchedEvent,)}
    required_config: ClassVar[type[KnowledgeFields]] = KnowledgeFields

    SearchRequest = SearchKnowledgeEvent
    Searched = KnowledgeSearchedEvent

    @staticmethod
    def search(
        references: list[KnowledgeReference] | None, query: str, cite_sources: bool = True
    ) -> SearchKnowledgeEvent:
        return SearchKnowledgeEvent(references=list(references or []), query=query, cite_sources=cite_sources)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge.steps.search_knowledge.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge.steps.search_knowledge.description"),
        icon="mdi:bookshelf",
    )
    async def search_step(
        agent: Agent,
        request: SearchKnowledgeEvent,
        knowledge: KnowledgeFields,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        access: AccessChecker | None = None,
    ) -> KnowledgeSearchedEvent:
        """Search the referenced collections the user may read, and answer with the best of it as one block."""
        if not request.references:
            return KnowledgeSearchedEvent()
        searchable, refused = await asyncio.to_thread(
            ReferencedKnowledge.partition, request.references, access, UserScopedRetrievers.namespaces_of
        )
        found = await Knowledge._find(searchable, request.query, knowledge.knowledge, t, user) if searchable else []
        refused_labels = await asyncio.to_thread(
            lambda: [KnowledgeCollectionLabel.of_reference(reference, t.locale) for reference in refused]
        )
        return KnowledgeSearchedEvent(
            block=Knowledge._block(found, refused_labels, t, request.cite_sources),
            grounding_nodes=found,
            refused=refused,
        )

    @staticmethod
    async def _find(
        references: list[KnowledgeReference],
        query: str,
        config: KnowledgeConfig,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> list[IngestedNode]:
        """The best sections for the query; ordered by retrieval score when the reranker is unavailable.

        The fallback keeps the turn answering from the referenced collections rather than failing on the ranking.
        """
        retrievers = await asyncio.to_thread(ReferencedKnowledge.retrievers, references, config.retrieve_k)
        nodes = await retrieve_from_all_sources(query, retrievers, t, user)
        if not nodes:
            return []
        try:
            return await rerank_nodes(nodes, query, config.reranking_model, user)
        except Exception:
            logger.exception("[knowledge] Could not rerank the referenced collections, keeping retrieval order")
            return sorted(nodes, key=lambda node: node.score or 0.0, reverse=True)[: config.reranking_model.top_n]

    @staticmethod
    def _block(
        found: list[IngestedNode], refused_labels: list[str], t: LocaleHandler, cite_sources: bool
    ) -> list[ChatMessage]:
        """The documents as retrieved knowledge is rendered, followed by the collections the answer must not use."""
        block = []
        if found:
            block.append(
                combine_nodes_in_order(found, t, AgentLocaleString.from_i18n_path("agent.knowledge.prompt.context"))
            )
            if cite_sources:
                block.append(ChatMessage(role=MessageRole.SYSTEM, content=t("lib.prompt.citations.instruction")))
        if refused_labels:
            collections = ", ".join(f'"{label}"' for label in refused_labels)
            block.append(ChatMessage(role=MessageRole.SYSTEM, content=t("agent.knowledge.prompt.refused", collections=collections)))
        if not found and not refused_labels:
            block.append(ChatMessage(role=MessageRole.SYSTEM, content=t("agent.knowledge.prompt.nothing_found")))
        return block
