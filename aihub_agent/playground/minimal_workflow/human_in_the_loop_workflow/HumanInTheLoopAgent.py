from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class HumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> HumanInTheLoop.input.request:
        print("[HumanInTheLoopAgent.start_step]")
        return HumanInTheLoop.input.invoke(question="Shall I continue?")

    @step()
    async def end_step(self, event: HumanInTheLoop.input.response) -> StopEvent:
        print(
            "[HumanInTheLoopAgent.end_step]",
            event.request_event.question,
            event.response,
        )
        return StopEvent()
