import asyncio
import logging
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.events.agent import (
    KnowledgeReference,
    KnowledgeSearchedEvent,
    RunToolLoopEvent,
    SearchKnowledgeEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
)
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
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_search_arguments import KnowledgeSearchArguments
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope import KnowledgeToolScope
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

SEARCH_KNOWLEDGE_TOOL = "search_knowledge"


@precondition()
async def searches_knowledge(call: ToolCallApprovedEvent) -> bool:
    return call.name == SEARCH_KNOWLEDGE_TOOL


@precondition()
async def answers_a_tool_call(searched: KnowledgeSearchedEvent, decided: ToolCallsDecidedEvent) -> bool:
    return searched.tool_call_id is not None and searched.tool_call_id in decided.tool_call_ids


class Knowledge(Capability):
    """
    Searching our knowledge collections, as one call and as a tool any agent can offer:

    - `search(references, query)` is answered with `KnowledgeSearchedEvent`, one context block with what those
      collections hold for the query, empty when nothing was referenced. Pass the block to `Conversation.compose(...)`
      next to the memories and attached files; a blueprint passes the collections the user referenced.
    - In a tool set, the model chooses when to search and which of the offered collections: the profile's
      (`KnowledgeToolFields`), or every collection the user can read, plus those referenced on the message.

    It is independent of a knowledge agent's own configured retrieval workflow, which keeps its own steps. Only
    collections the asking user may read are searched; the others are named in the block so the answer says so.
    """

    calls: ClassVar[dict] = {SearchKnowledgeEvent: (KnowledgeSearchedEvent,)}
    required_config: ClassVar[type[KnowledgeFields]] = KnowledgeFields

    SearchRequest = SearchKnowledgeEvent
    Searched = KnowledgeSearchedEvent

    tool_name: ClassVar[str] = SEARCH_KNOWLEDGE_TOOL
    tool_config: ClassVar[type[KnowledgeToolFields]] = KnowledgeToolFields
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.knowledge.tool.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.knowledge.tool.approval_summary"),
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered when there is something the user may read to search; the model picks among those collections."""
        config = context.agent_config
        if not isinstance(config, KnowledgeToolFields):
            return None
        offered = KnowledgeToolScope.collections(config.knowledge_tool, context.knowledge_references, context.access)
        if not offered:
            return None
        t = context.t
        collections = {
            f"{reference.database}/{reference.namespace}": KnowledgeCollectionLabel.of_reference(reference, t.locale)
            for reference in offered
        }
        listing = "\n".join(f"- {identifier}: {label}" for identifier, label in collections.items())
        return ToolDefinition(
            name=SEARCH_KNOWLEDGE_TOOL,
            description=t("agent.knowledge.tool.description", collections=listing),
            parameters=KnowledgeSearchArguments.schema_for(list(collections), t),
        )

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
            return KnowledgeSearchedEvent(tool_call_id=request.tool_call_id)
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
            tool_call_id=request.tool_call_id,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge.steps.search_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge.steps.search_as_tool.description"),
        icon="mdi:bookshelf",
        precondition=searches_knowledge,
    )
    async def tool_call_step(
        agent: Agent,
        call: ToolCallApprovedEvent,
        request: RunToolLoopEvent,
        tool: KnowledgeToolFields,
        access: AccessChecker | None = None,
    ) -> SearchKnowledgeEvent | ToolResultEvent:
        """The model chose to search: the same search as a `#` reference, over the offered collections it picked."""
        try:
            arguments = KnowledgeSearchArguments.model_validate(call.arguments)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        offered = await asyncio.to_thread(
            KnowledgeToolScope.collections, tool.knowledge_tool, request.knowledge_references, access
        )
        chosen = [
            reference
            for reference in offered
            if not arguments.collections or f"{reference.database}/{reference.namespace}" in arguments.collections
        ]
        return SearchKnowledgeEvent(
            references=chosen or offered,
            query=arguments.query,
            cite_sources=call.cite_sources,
            tool_call_id=call.tool_call_id,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge.steps.answer_tool_call.description"),
        icon="mdi:bookshelf",
        precondition=answers_a_tool_call,
    )
    async def tool_result_step(
        agent: Agent, searched: KnowledgeSearchedEvent, decided: ToolCallsDecidedEvent
    ) -> ToolResultEvent:
        """Hand what the search found back to the loop: its text for the model, its block for a gathered answer."""
        content = "\n\n".join(message.content for message in searched.block if message.content)
        return ToolResultEvent(
            tool_call_id=searched.tool_call_id,
            name=SEARCH_KNOWLEDGE_TOOL,
            content=content,
            block=searched.block,
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
            block.append(
                ChatMessage(
                    role=MessageRole.SYSTEM, content=t("agent.knowledge.prompt.refused", collections=collections)
                )
            )
        if not found and not refused_labels:
            block.append(ChatMessage(role=MessageRole.SYSTEM, content=t("agent.knowledge.prompt.nothing_found")))
        return block
