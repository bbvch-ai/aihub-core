from typing import List

from llama_index.core.base.llms.types import MessageRole, ChatMessage

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.rag.Configs.MultiHopRAGAgentConfig import MultiHopRAGAgentConfig
from aihub_agent.agents.rag.Events.ConcatenationEvent import ConcatenationEvent
from aihub_agent.agents.rag.Events.DecomposeQueryEvent import DecomposeQueryEvent
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.utils.decompose_chat_history import decompose_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import StopEvent, LLMEvent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent, Document
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
        event: StartEvent | UserMessageEvent,
        agent_config: MultiHopRAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        user_messages = [msg for msg in event.messages if msg.role == MessageRole.USER]
        try:
            await run_context.set("user_query", user_messages[-1].content)
        except IndexError:
            raise ValueError("No user messages found in the event.")
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        serialized_chat_history = [msg.model_dump() for msg in limited_chat_history]
        await run_context.set("chat_history", serialized_chat_history)

        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step()
    async def decompose_query_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: MultiHopRAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> List[DecomposeQueryEvent]:
        """
        Condenses the chat history and user query into a standalone question.
        """
        await displayer.display_thought(t("agent.thought.condense_question"))
        user_query = await run_context.get("user_query")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            decomposed_chat_history = decompose_chat_history(
                chat_history=event.limited_history,
                message=user_query,
                t=t,
                llm=llm,
                hops=agent_config.hops,
                decompose_prompt=agent_config.decompose_chat_history_prompt,
            )
            events = [
                DecomposeQueryEvent(decomposed_chat_history=decomposed_chat)
                for decomposed_chat in decomposed_chat_history
            ]
            return events

    @step()
    async def retrieve_step(
        self,
        event: DecomposeQueryEvent,
        agent_config: MultiHopRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = agent_config.retrieve_step_config.embed_model.to_llama_index()
        nodes = retrieve_nodes(
            message=event.decomposed_chat_history.content,
            index_name=agent_config.retrieve_step_config.index_name,
            index_namespaces=agent_config.retrieve_step_config.index_namespaces,
            query_mode=agent_config.retrieve_step_config.query_mode,
            node_types=agent_config.retrieve_step_config.node_types,
            retrieve_k=agent_config.retrieve_step_config.retrieve_k,
            embed_model=embedding,
        )
        return RetrieverEvent.from_nodes(nodes)

    @step()
    async def concatenation_step(self, events: List[RetrieverEvent], agent_config: MultiHopRAGAgentConfig) -> ConcatenationEvent | None:
        """
        Concatenates the nodes from 5 retrieval steps into one list of nodes.
        """
        if len(events) < agent_config.hops:
            return None

        documents = []
        [documents.extend(event.documents) for event in events]

        seen_ids = set()
        unique_documents = []
        for doc in documents:
            if doc.id not in seen_ids:
                unique_documents.append(doc)
                seen_ids.add(doc.id)

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
        agent_config: MultiHopRAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Includes the combined context and truncates chat history again.
        """
        serialized_chat_history = await run_context.get("chat_history")
        chat_history = [ChatMessage.model_validate(msg) for msg in serialized_chat_history]

        system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
        last_user_message = await run_context.get("user_query")
        limited_chat_history = limit_chat_history_with_context(
            chat_history=chat_history,
            context_messages=[event.context_message],
            system_messages=system_messages,
            last_user_message=ChatMessage(role=MessageRole.USER, content=last_user_message),
            tokenizer_for_model=agent_config.llm.name,
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
        await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.limited_history_with_context)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        """
        Signals the completion of the workflow.
        """
        return StopEvent()
