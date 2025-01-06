from aihub_lib.nats.events.semantic.llm import LLMEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.nats.events.control.start import StartEvent
from aihub_lib.nats.events.control.stop import StopEvent

from aihub_agent.agents.rag.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.rag.RetrieverStepConfig import RetrieverStepConfig
from aihub_agent.agents.rag.StandaloneQuestionCondenserEvent import (
    StandaloneQuestionCondenserEvent,
)
from aihub_agent.agents.rag.condense_standalone_question_step import (
    condense_standalone_question_step,
)
from aihub_agent.agents.rag.limit_chat_history_step import limit_chat_history_step
from aihub_agent.agents.rag.retriever_step import retriever_step
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step


class RAGAgent(Agent):
    @step()
    async def start(self, event: StartEvent):
        pass

    @step()
    async def limit_chat_history(self) -> LimitChatHistoryEvent:
        return limit_chat_history_step()

    @step()
    async def condense_standalone_question(
        self, event: LimitChatHistoryEvent
    ) -> StandaloneQuestionCondenserEvent:
        return condense_standalone_question_step()

    @step()
    async def retrieve(
        self,
        event: StandaloneQuestionCondenserEvent,
        retrieve_config: RetrieverStepConfig,
        displayer: EventDisplayer,
    ) -> RetrieverEvent:
        await displayer.display_thought("agent.thought.searching_knowledge")
        return retriever_step(
            message=event.condensed_chat_message.content, config=retrieve_config
        )

    @step()
    async def order_nodes_by_documents(self):
        pass

    @step()
    async def limit_chat_history_with_context(self):
        pass

    @step()
    async def respond_with_llm(
        self, event, agent_config: RAGAgentConfig, displayer: EventDisplayer
    ) -> LLMEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                agent_config.llm, llm, event.messages
            )

    @step()
    def stop(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
