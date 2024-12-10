from agents_core.agents.abstract.Agent import Agent
from agents_core.displayers.EventDisplayer import EventDisplayer
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent
from playground.LlamaIndexAgent.LlamaIndexAgentConfig import LlamaIndexAgentConfig


class LlamaIndexAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent, agent_config: LlamaIndexAgentConfig, displayer: EventDisplayer) -> StopEvent:
        print("[LlamaIndexAgent.start_step]")
        llm, cost_tracker = agent_config.llm.to_llama_index()

        await displayer.display_llm(llm.stream_chat(messages=event.messages))
        await displayer.display_llm_costs(agent_config.llm.name, cost_tracker)

        return StopEvent()