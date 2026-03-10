from typing import ClassVar

from swiss_ai_hub.core.displayers.EventDisplayer import EventDisplayer
from swiss_ai_hub.core.generative_ai.retrieval.combine_nodes_in_order import combine_nodes_in_order
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.events.semantic.retriever.RetrieverEvent import RetrieverEvent

from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from swiss_ai_hub.agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from swiss_ai_hub.agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from swiss_ai_hub.agent.i18n.AgentLocaleString import AgentLocaleString
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
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        retriever = agent_config.retriever
        embedding, _ = retriever.embed_model.to_llama_index()

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
