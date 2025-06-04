from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMStopEvent, UserMessageEvent
from aihub_lib.nats.workflow.decorators.step import step

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig


class LLMWrappingAgent(Agent):
    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMStopEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages, as_stop_step=True)
