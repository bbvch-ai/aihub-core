from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import RetrieverEvent
from swiss_ai_hub.core.generative_ai import combine_nodes_in_order, retrieve_nodes, retrieve_prev_next_nodes
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import LiteLLMService

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.retrieval_agent.configs.retrieval_agent_config import RetrievalAgentConfig
from swiss_ai_hub.agent.agents.retrieval_agent.events.question_start_event import QuestionStartEvent
from swiss_ai_hub.agent.agents.retrieval_agent.events.retrieval_response_event import RetrievalResponseEvent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class RetrievalAgent(Agent):
    """
    The agent is a simplified Retrieval-Augmented Generation agent that focuses on retrieving relevant
    information from a knowledge base without any additional steps.
    This can be useful if we want to separate the retrieval process from the generation process,
    when we have for example different data sources and each source has its own retrieval agent.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.retrieval_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.retrieval_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:search"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.retrieve_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.retrieve_nodes.description"),
        icon="mage:search",
    )
    async def retrieve_step(
        self,
        event: QuestionStartEvent,
        agent_config: RetrievalAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        # Populated when the run is started through the API, which passes the authenticated caller.
        # Optional because the other two entry paths — process delegation and scheduling — supply no identity.
        user: UserIdentity | None = None,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        retriever = agent_config.retriever
        api_key = await LiteLLMService.api_key_for_user(user) if user else None
        embedding, _ = retriever.embed_model.to_llama_index(api_key=api_key)

        vector_store = retriever.vector_store.to_llama_index()

        nodes = retrieve_nodes(
            message=event.question,
            retrieve_k=retriever.retrieve_k,
            embed_model=embedding,
            index_namespaces=retriever.vector_store.index_namespaces,
            query_mode=retriever.query_mode,
            node_types=retriever.node_types,
            vector_store=vector_store,
        )
        if retriever.retrieve_prev_next:
            nodes = retrieve_prev_next_nodes(
                vector_store=vector_store,
                nodes=nodes,
                num_nodes=retriever.retrieve_prev_next.num_nodes,
                prev_next_mode=retriever.retrieve_prev_next.mode,
            )

        return RetrieverEvent.from_nodes(nodes)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.order_nodes.name"),
        description=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.order_nodes.description"),
        icon="mage:arrowlist",
    )
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent,
        t: LocaleHandler,
        start_event: QuestionStartEvent,
        agent_config: RetrievalAgentConfig,
    ) -> InOrderNodeCombinerEvent:
        """
        Orders the retrieved nodes based on their source documents.
        """
        ordered_nodes = combine_nodes_in_order(
            context_nodes=event.nodes,
            t=t.in_locale(start_event.locale),
            context_prompt=agent_config.context_prompt,
        )
        return InOrderNodeCombinerEvent(context_message=ordered_nodes)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.retrieval_agent.steps.stop.description"),
        icon="mage:check",
    )
    async def stop_step(
        self, event: InOrderNodeCombinerEvent, retriever_event: RetrieverEvent
    ) -> RetrievalResponseEvent:
        return RetrievalResponseEvent(context_message=event.context_message, nodes=retriever_event.nodes)
