from llama_index.core.base.llms.types import ChatMessage, MessageRole
from typing import List

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.basic.FewShotAgent.events.LimitChatHistoryWithContextEvent import (
    LimitChatHistoryWithContextEvent,
)
from aihub_agent.agents.common.events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.MultiHopRAGAgent.configs.MultiHopRAGAgentConfig import MultiHopRAGAgentConfig
from aihub_agent.agents.rag.MultiHopRAGAgent.events.ConcatenationEvent import ConcatenationEvent
from aihub_agent.agents.rag.MultiHopRAGAgent.events.DecomposeQueryEvent import DecomposeQueryEvent
from aihub_agent.agents.rag.MultiHopRAGAgent.ops.decompose_chat_history import decompose_chat_history
from aihub_agent.agents.rag.RAGAgent.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.RAGAgent.events.FewShotAcceptEvent import FewShotAcceptEvent
from aihub_agent.agents.rag.RAGAgent.events.FewShotRejectEvent import FewShotRejectEvent
from aihub_agent.agents.rag.RAGAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.guards.few_shot_guard import few_shot_guard
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import ExceptionEvent, LLMEvent, StopEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent


class MultiHopRAGAgent(Agent):
    """
    Implements a Multi Hop Retrieval-Augmented Generation (RAG) Agent.

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
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: MultiHopRAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step()
    async def decompose_query_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        agent_config: MultiHopRAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> List[DecomposeQueryEvent]:
        """
        Decomposes the chat history and user query into multiple queries.
        """
        await displayer.display_thought(t("agent.thought.decompose_query"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            decomposed_chat_history = await decompose_chat_history(
                chat_history=event.limited_history,
                message=start_event.user_query,
                t=t,
                llm=llm,
                hops=agent_config.hops,
                decompose_prompt=agent_config.decompose_chat_history_prompt,
            )
            events = [
                DecomposeQueryEvent(decomposed_query=decomposed_chat) for decomposed_chat in decomposed_chat_history
            ]
            return events

    @step()
    async def few_shot_guard_step(
        self,
        event: DecomposeQueryEvent,
        agent_config: MultiHopRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        if not agent_config.few_shot_guard_examples:
            return FewShotAcceptEvent(reasoning=t("agent.thought.no_few_shot_examples"))

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            guard_result = await few_shot_guard(
                llm=llm,
                t=t,
                user_query=event.decomposed_query.content,
                examples=agent_config.few_shot_guard_examples,
            )

        if not guard_result.success:
            return FewShotRejectEvent(reasoning=guard_result.reasoning)

        return FewShotAcceptEvent(reasoning=guard_result.reasoning)

    @step()
    async def retrieve_step(
        self,
        event: DecomposeQueryEvent,
        _: FewShotAcceptEvent,
        retrieve_step_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = retrieve_step_config.embed_model.to_llama_index()
        nodes = retrieve_nodes(
            message=event.decomposed_query.content,
            index_namespaces=retrieve_step_config.index_namespaces,
            query_mode=retrieve_step_config.query_mode,
            node_types=retrieve_step_config.node_types,
            retrieve_k=retrieve_step_config.retrieve_k,
            embed_model=embedding,
            vector_store=retrieve_step_config.vector_store,
        )
        return RetrieverEvent.from_nodes(nodes)

    @step()
    async def concatenation_step(
        self, events: List[RetrieverEvent], agent_config: MultiHopRAGAgentConfig, run_context: RunContext
    ) -> ConcatenationEvent | None:
        """
        Concatenates the nodes from 5 retrieval steps into one list of nodes.
        """
        # flag for only running the step one time once all events are present
        concatenated = await run_context.get("concatenated", False)
        if concatenated or len(events) < agent_config.hops:
            return None

        documents = []
        [documents.extend(event.documents) for event in events]

        seen_ids = set()
        unique_documents = []
        for doc in documents:
            if doc.id not in seen_ids:
                unique_documents.append(doc)
                seen_ids.add(doc.id)

        await run_context.set("concatenated", True)
        return ConcatenationEvent(documents=unique_documents)

    @step()
    async def order_nodes_by_documents_step(
        self,
        event: ConcatenationEvent,
        t: LocaleHandler,
        agent_config: MultiHopRAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        """
        Orders the retrieved nodes based on their source documents.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        ordered_nodes = combine_nodes_in_order(
            context_nodes=event.documents,
            locale_handler=t,
            context_prompt=agent_config.context_prompt,
        )
        return InOrderNodeCombinerEvent(context_message=ordered_nodes)

    @step()
    async def limit_chat_history_with_context_step(
        self,
        event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        agent_config: MultiHopRAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Includes the combined context and truncates chat history again.
        """
        chat_history = chat_history_event.limited_history
        system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
        limited_chat_history = limit_chat_history_with_context(
            chat_history=chat_history_event.limited_history,
            context_messages=[event.context_message],
            system_messages=system_messages,
            last_user_message=ChatMessage(role=MessageRole.USER, content=start_event.user_query),
            tokenizer=agent_config.llm.tokenizer,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryWithContextEvent(limited_history_with_context=limited_chat_history)

    @step()
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent,
        agent_config: MultiHopRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        """
        Generates a response using the configured LLM.
        """
        messages = event.limited_history_with_context
        await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, messages)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        """
        Signals the completion of the workflow.
        """
        return StopEvent()

    @step()
    async def exception_step(self, event: FewShotRejectEvent) -> ExceptionEvent:
        """
        The input question was rejected.
        """
        return ExceptionEvent(message=event.reasoning)
