from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import LLMEvent, StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.llama_index_workflow.LlamaIndexAgentConfig import (
    LlamaIndexAgentConfig,
)


class LlamaIndexAgent(Agent):
    agent_config_type: type[LlamaIndexAgentConfig] = LlamaIndexAgentConfig

    @step()
    async def start_step(
        self,
        event: UserMessageEvent,
        agent_config: LlamaIndexAgentConfig,
        displayer: EventDisplayer,
    ) -> LLMEvent:
        print("[LlamaIndexAgent.start_step]")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
