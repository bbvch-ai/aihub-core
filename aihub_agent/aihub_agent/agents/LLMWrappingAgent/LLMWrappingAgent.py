from __future__ import annotations

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMStopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_agent.workflow.decorators.step import step


class LLMWrappingAgent(Agent):
    agent_config_type: type[LLMWrappingAgentConfig] = LLMWrappingAgentConfig

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgent.agent_config_type,
        displayer: EventDisplayer,
    ) -> LLMStopEvent:
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages, as_stop_step=True)
