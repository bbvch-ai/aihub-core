from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMEvent, StopEvent, UserMessageEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.agents.basic.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_agent.workflow.decorators.step import step


class LLMWrappingAgent(Agent):
    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
