from agents_core.agents.abstract.Agent import Agent
from agents_core.displayers.EventDisplayer import EventDisplayer
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent, LLMEvent, UserMessageEvent
from playground.LlamaIndexAgent.LlamaIndexAgentConfig import LlamaIndexAgentConfig


class DevAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent | UserMessageEvent, agent_config: LlamaIndexAgentConfig, displayer: EventDisplayer) -> LLMEvent:
        print("[LlamaIndexAgent.start_step]")
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, event.messages)


    @step()
    async def stop_step(self, event: LLMEvent) -> StopEvent:
        return StopEvent()