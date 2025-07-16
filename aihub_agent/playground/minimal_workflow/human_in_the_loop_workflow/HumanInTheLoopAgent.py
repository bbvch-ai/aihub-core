from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgentConfig import HumanInTheLoopAgentConfig


class HumanInTheLoopAgent(Agent):
    agent_config_type: type[HumanInTheLoopAgentConfig] = HumanInTheLoopAgentConfig

    @step()
    async def start_step(self, event: StartEvent) -> HumanInTheLoop.request:
        print("[HumanInTheLoopAgent.start_step]")
        return HumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def end_step(self, event: HumanInTheLoop.response) -> StopEvent:
        print(
            "[HumanInTheLoopAgent.end_step]",
            event.request_event.question,
            event.response,
        )
        return StopEvent()
