from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent, LLMEvent, UserMessageEvent
from playground.minimal_workflow.LlamaIndexAgent.LlamaIndexAgentConfig import (
    LlamaIndexAgentConfig,
)


class LlamaIndexAgent(Agent):

    @step()
    async def start_step(
            self,
            event: StartEvent | UserMessageEvent,
            agent_config: LlamaIndexAgentConfig,
            displayer: EventDisplayer,
    ) -> LLMEvent:
        print("[LlamaIndexAgent.start_step]")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(
                agent_config.llm, llm, event.messages
            )

    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()
