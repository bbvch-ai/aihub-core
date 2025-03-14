from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.common.events.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.common.events.StandaloneQuestionCondenserEvent import StandaloneQuestionCondenserEvent
from aihub_agent.agents.rag.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.configs.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.events.ContextInsufficientEvent import ContextInsufficientEvent
from aihub_agent.agents.rag.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.rag.events.ContextSufficientEvent import ContextSufficientEvent
from aihub_agent.agents.rag.events.FewShotAcceptEvent import FewShotAcceptEvent
from aihub_agent.agents.rag.events.FewShotRejectEvent import FewShotRejectEvent
from aihub_agent.agents.rag.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
from aihub_lib.generative_ai.guards.few_shot_guard import few_shot_guard
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.utils.retrieve_nodes import retrieve_nodes
from aihub_lib.generative_ai.utils.retrieve_prev_next_nodes import retrieve_prev_next_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events.control.stop import StopEvent
from aihub_lib.nats.events.semantic.llm import LLMEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    """

    @step()
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        await run_context.set("hop_count", 1)
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step()
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        """
        Condenses the chat history and user query into a standalone question.
        """
        await displayer.display_thought(t("agent.thought.condense_question"))
        user_query = start_event.user_query
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
    async def few_shot_guard_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        if not agent_config.few_shot_guard_examples:
            return FewShotAcceptEvent(reasoning=t("agent.thought.no_few_shot_examples"))

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            if isinstance(event, StandaloneQuestionCondenserEvent):
                guard_result = await few_shot_guard(
                    llm=llm,
                    t=t,
                    user_query=event.condensed_chat_message.content,
                    examples=agent_config.few_shot_guard_examples,
                )
            else:
                guard_result = await few_shot_guard(
                    llm=llm,
                    t=t,
                    user_query=event.new_query,
                    examples=agent_config.few_shot_guard_examples,
                )

        if not guard_result.success:
            return FewShotRejectEvent(reasoning=guard_result.reasoning)

        return FewShotAcceptEvent(reasoning=guard_result.reasoning)

    @step()
    async def retrieve_step(
        self,
        standalone_question_event: StandaloneQuestionCondenserEvent,
        _: FewShotAcceptEvent,
        retrieve_step_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from the knowledge base.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        embedding, _ = retrieve_step_config.embed_model.to_llama_index(model_parameter=None)
        nodes = retrieve_nodes(
            message=standalone_question_event.condensed_chat_message.content,
            retrieve_k=retrieve_step_config.retrieve_k,
            embed_model=embedding,
            index_namespaces=retrieve_step_config.index_namespaces,
            query_mode=retrieve_step_config.query_mode,
            node_types=retrieve_step_config.node_types,
            vector_store=retrieve_step_config.vector_store,
        )
        if retrieve_step_config.retrieve_prev_next:
            nodes = retrieve_prev_next_nodes(
                vector_store=retrieve_step_config.vector_store,
                nodes=nodes,
                num_nodes=retrieve_step_config.retrieve_prev_next.num_nodes,
                prev_next_mode=retrieve_step_config.retrieve_prev_next.mode,
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
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: InOrderNodeCombinerEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> ContextSufficientEvent | ContextInsufficientEvent:
        """
        Guards the context to ensure it is sufficient for generating a response.
        """
        if not agent_config.check_context_sufficiency:
            return ContextSufficientEvent()
        async with agent_config.llm.cost_reporting_llm(
            displayer, system_prompt=t("lib.guards.context_sufficient_guard.message")
        ) as llm:
            guard_result = await context_sufficient_guard(
                llm=llm,
                t=t,
                user_query=user_query_event.condensed_chat_message.content,
                context=event.context_message.content,
            )

        if guard_result.success:
            await displayer.display_thought(t("agent.thought.context_sufficient"))
            return ContextSufficientEvent()

        hop_count = await run_context.get("hop_count")
        if hop_count < agent_config.max_hops:
            await displayer.display_thought(t("agent.thought.max_hops_reached"))
            return ContextInsufficientEvent(reasoning=guard_result.reasoning)

        await run_context.set("hop_count", hop_count + 1)
        await displayer.display_thought(t("agent.thought.trying_another_retrieval_hop"))
        return ContextInsufficientWithQueryEvent(reasoning=guard_result.reasoning, new_query=guard_result.new_query)

    @step()
    async def limit_chat_history_with_context_step(
        self,
        nodes_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Includes the combined context and truncates chat history again.
        """
        chat_history = chat_history_event.limited_history
        system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
        limited_chat_history = limit_chat_history_with_context(
            chat_history=chat_history_event.limited_history,
            context_messages=[nodes_event.context_message],
            system_messages=system_messages,
            last_user_message=ChatMessage(role=MessageRole.USER, content=start_event.user_query),
            tokenizer=agent_config.llm.tokenizer,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryWithContextEvent(limited_history_with_context=limited_chat_history)

    @step()
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        """
        Generates a response using the configured LLM.
        """
        if isinstance(event, FewShotRejectEvent) or isinstance(event, ContextInsufficientEvent):
            messages = limited_history_without_context.limited_history + [
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=PromptTemplate(t("agents.prompt.guard.reject")).format(reason=event.reasoning),
                ),
            ]
        else:
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
