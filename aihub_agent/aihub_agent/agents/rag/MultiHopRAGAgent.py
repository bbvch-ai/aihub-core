from aihub_agent.agents.rag.Events.ConcatenationEvent import ConcatenationEvent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_lib.nats.events.semantic.llm import LLMEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.rag.RAGAgent import RAGAgent
from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.rag.Events.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step


class MultiHopRAGAgent(RAGAgent):
    """
    Builds on the Retrieval-Augmented Generation (RAG) Agent.

    The MultiHopRAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.
    The user input is decomposed into sub-questions which are used to retrieve a larger number of relevant documents.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Decompose standalone question into sub-question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    """

    @step()
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> StandaloneQuestionCondenserEvent:
        """
        Condenses the chat history and user query into a standalone question.
        """
        await displayer.display_thought(t("agent.thought.condense_question"))
        user_query = await run_context.get("user_query")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            condensed_question = condense_standalone_question(
                chat_history=event.limited_history,
                message=user_query,
                t=t,
                llm=llm,
                condense_prompt=agent_config.condense_question_prompt,
            )
            return StandaloneQuestionCondenserEvent(condensed_chat_message=condensed_question)

    @step()
    async def decompose_standalone_question_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Decomposes the standalone question into sub-questions.
        """
        # TODO: add llm to query for decomposition
        pass

    @step()
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        retrieve_step_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> ConcatenationEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = retrieve_step_config.embed_model.to_llama_index()
        nodes = retrieve_nodes(
            message=event.condensed_chat_message.content,
            index_name=retrieve_step_config.index_name,
            index_namespaces=retrieve_step_config.index_namespaces,
            query_mode=retrieve_step_config.query_mode,
            node_types=retrieve_step_config.node_types,
            retrieve_k=retrieve_step_config.retrieve_k,
            embed_model=embedding,
        )
        return ConcatenationEvent(nodes)

    @step()
    async def concatenation_step(self, events: FixedList(ConcatenationEvent, 5)) -> RetrieverEvent:
        """
        Concatenates the nodes from 5 retrieval steps into one list of nodes.
        """
        nodes = []
        [nodes.extend(event.nodes) for event in events]

        return RetrieverEvent.from_nodes(nodes)
