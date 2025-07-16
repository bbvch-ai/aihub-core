from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.simple_workflow.events.SimpleEventA import SimpleEventA
from playground.minimal_workflow.simple_workflow.SimpleAgentConfig import SimpleAgentConfig


class SimpleAgent(Agent):
    agent_config_type: type[SimpleAgentConfig] = SimpleAgentConfig

    @step()
    async def start_step(self, event: UserMessageEvent) -> SimpleEventA:
        print("[SimpleAgent.start_step]", event)
        return SimpleEventA(payload=event.messages[-1].content)

    @step()
    async def end_step(self, event: SimpleEventA) -> StopEvent:
        print("[SimpleAgent.end_step]", event)
        return StopEvent()
