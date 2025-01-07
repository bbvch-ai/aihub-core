from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events.semantic.llm import LLMEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent

from aihub_agent.agents.rag.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.rag.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.LimitChatHistoryStepConfig import LimitChatHistoryStepConfig
from aihub_agent.agents.rag.LimitChatHistoryWithContextEvent import (
    LimitChatHistoryWithContextEvent,
)
from aihub_agent.agents.rag.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.RetrieveStepConfig import RetrieveStepConfig
from aihub_agent.agents.rag.StandaloneQuestionCondenserEvent import (
    StandaloneQuestionCondenserEvent,
)
from aihub_agent.agents.rag.combine_nodes_in_order import combine_nodes_in_order
from aihub_agent.agents.rag.condense_standalone_question import (
    condense_standalone_question,
)
from aihub_agent.agents.rag.limit_chat_history import limit_chat_history
from aihub_agent.agents.rag.limit_chat_history_with_context import (
    limit_chat_history_with_context,
)
from aihub_agent.agents.rag.retrieve_nodes import retrieve_nodes
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step


class RAGAgent(Agent):

    # @step()
    # async def start_step(self, event: StartEvent | UserMessageEvent, run_context: RunContext):

    @step()
    async def limit_chat_history_step(
        self,
        event: StartEvent | UserMessageEvent,
        limit_chat_history_config: LimitChatHistoryStepConfig,
        run_context: RunContext,
    ) -> LimitChatHistoryEvent:
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=limit_chat_history_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step()
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        condense_standalone_question_config,
        t: LocaleHandler,
        run_context: RunContext,
    ) -> StandaloneQuestionCondenserEvent:
        condensed_question = condense_standalone_question(
            chat_history=event.limited_history,
            message=event.limited_history[-1].content,
            t=t,
            llm=condense_standalone_question_config.llm,
            condense_prompt=condense_standalone_question_config.condense_prompt,
        )
        return StandaloneQuestionCondenserEvent(
            condensed_chat_message=condensed_question
        )

    @step()
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        retrieve_config: RetrieveStepConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        nodes = retrieve_nodes(
            message=event.condensed_chat_message.content,
            index_name=retrieve_config.index_name,
            index_namespaces=retrieve_config.index_namespaces,
            query_mode=retrieve_config.query_mode,
            node_types=retrieve_config.node_types,
            retrieve_k=retrieve_config.retrieve_k,
            embed_model=retrieve_config.embed_model,
        )
        return RetrieverEvent(documents=nodes)

    @step()
    async def order_nodes_by_documents_step(
        self, event: RetrieverEvent, t: LocaleHandler
    ) -> InOrderNodeCombinerEvent:
        ordered_nodes = combine_nodes_in_order(
            context_nodes=event.documents, locale_handler=t, context_prompt=None
        )
        return InOrderNodeCombinerEvent(context_message=ordered_nodes)

    @step()
    async def limit_chat_history_with_context_step(
        self,
        event: InOrderNodeCombinerEvent,
        run_context: RunContext,
    ) -> LimitChatHistoryWithContextEvent:
        chat_history = await run_context.get("chat_history")
        limited_chat_history = limit_chat_history_with_context(
            chat_history=chat_history,
            context_messages=[event.context_message],
            number_of_input_tokens=limit_chat_history_config.number_of_input_tokens,
        )
        return LimitChatHistoryWithContextEvent(limited_history=limited_chat_history)

    @step()
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                agent_config.llm, llm, event.limited_history_with_context
            )

    @step()
    def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
