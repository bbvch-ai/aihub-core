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

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.rag.Configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.Configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.Events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.Events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.rag.Events.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Limit chat history to fit input token limits.
    - Condense follow-up questions into standalone questions.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    """

    @step()
    async def limit_chat_history_step(
        self,
        event: StartEvent | UserMessageEvent,
        agent_config: RAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        """
        Limits the chat history to the token limit defined in the agent configuration.

        Args:
            event (StartEvent | UserMessageEvent): Incoming event with user or system messages.
            agent_config (RAGAgentConfig): Configuration for the RAG agent.
            run_context (RunContext): Context to store intermediate values.

        Returns:
            LimitChatHistoryEvent: Event with the limited chat history.
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
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> StandaloneQuestionCondenserEvent:
        """
        Condenses a follow-up question into a standalone question.

        Args:
            event (LimitChatHistoryEvent): Event with limited chat history.
            agent_config (RAGAgentConfig): Configuration for the RAG agent.
            t (LocaleHandler): Locale handler for translations.
            displayer (EventDisplayer): Displayer for user-visible events.
            run_context (RunContext): Context to store intermediate values.

        Returns:
            StandaloneQuestionCondenserEvent: Event with the condensed standalone question.
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
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        retrieve_step_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.

        Args:
            event (StandaloneQuestionCondenserEvent): Event with the condensed question.
            retrieve_step_config (RetrieveStepConfig): Configuration for the retrieval step.
            displayer (EventDisplayer): Displayer for user-visible events.
            t (LocaleHandler): Locale handler for translations.

        Returns:
            RetrieverEvent: Event containing the retrieved nodes.
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
        return RetrieverEvent.from_nodes(nodes)

    @step()
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent,
        t: LocaleHandler,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        """
        Orders the retrieved nodes based on the context provided.

        Args:
            event (RetrieverEvent): Event with retrieved nodes.
            t (LocaleHandler): Locale handler for translations.
            agent_config (RAGAgentConfig): Configuration for the RAG agent.
            displayer (EventDisplayer): Displayer for user-visible events.

        Returns:
            InOrderNodeCombinerEvent: Event containing ordered nodes.
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
        agent_config: RAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Limits chat history by including context messages.

        Args:
            event (InOrderNodeCombinerEvent): Event with ordered context nodes.
            agent_config (RAGAgentConfig): Configuration for the RAG agent.
            run_context (RunContext): Context to store intermediate values.

        Returns:
            LimitChatHistoryWithContextEvent: Event containing the limited chat history with context.
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
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        """
        Generates a response using the configured LLM based on the limited chat history with context.

        Args:
            event (LimitChatHistoryWithContextEvent): Event with limited chat history.
            agent_config (RAGAgentConfig): Configuration for the RAG agent.
            displayer (EventDisplayer): Displayer for user-visible events.
            t (LocaleHandler): Locale handler for translations.

        Returns:
            LLMEvent: Event containing the response generated by the LLM.
        """
        await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.limited_history_with_context)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        """
        Signals the completion of the workflow.

        Args:
            event (LLMEvent): Event indicating the response generation completion.

        Returns:
            StopEvent: Event signaling the end of the process.
        """
        return StopEvent()
