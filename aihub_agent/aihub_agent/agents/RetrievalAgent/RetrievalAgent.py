from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrieval.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from aihub_lib.generative_ai.retrieval.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RagAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from aihub_agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.workflow.decorators.step import step


class RetrievalAgent(Agent):
    """
    The agent is a simplified Retrieval-Augmented Generation agent that focuses on retrieving relevant
    information from a knowledge base without any additional steps.
    This can be useful if we want to separate the retrieval process from the generation process,
    when we have for example different data sources and each source has its own retrieval agent.
    """

    @step(
        name=LocaleString(en="Retrieve nodes"),
        description=LocaleString(en="Retrieves relevant nodes from the knowledge base."),
    )
    async def retrieve_step(
        self,
        event: QuestionStartEvent,
        retrieve_step_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = retrieve_step_config.embed_model.to_llama_index()

        vector_store = retrieve_step_config.vector_store.to_llama_index()

        nodes = retrieve_nodes(
            message=event.question,
            retrieve_k=retrieve_step_config.retrieve_k,
            embed_model=embedding,
            index_namespaces=retrieve_step_config.index_namespaces,
            query_mode=retrieve_step_config.query_mode,
            node_types=retrieve_step_config.node_types,
            vector_store=vector_store,
        )
        if retrieve_step_config.retrieve_prev_next:
            nodes = retrieve_prev_next_nodes(
                vector_store=vector_store,
                nodes=nodes,
                num_nodes=retrieve_step_config.retrieve_prev_next.num_nodes,
                prev_next_mode=retrieve_step_config.retrieve_prev_next.mode,
            )

        return RetrieverEvent.from_nodes(nodes)

    @step(
        name=LocaleString(en="Order nodes by documents"),
        description=LocaleString(en="Orders the retrieved nodes by their source documents."),
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
        name=LocaleString(en="Stop step"),
        description=LocaleString(en="Stops the agent and returns the ordered nodes as context messages."),
    )
    async def stop_step(
        self, event: InOrderNodeCombinerEvent, retriever_event: RetrieverEvent
    ) -> RetrievalResponseEvent:
        return RetrievalResponseEvent(context_message=event.context_message, nodes=retriever_event.nodes)
