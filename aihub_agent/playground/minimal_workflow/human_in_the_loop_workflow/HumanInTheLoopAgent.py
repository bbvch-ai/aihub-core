from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopInput

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class HumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> HumanInTheLoopInput.request:
        print("[HumanInTheLoopAgent.start_step]")
        return HumanInTheLoopInput.invoke(message="Shall I continue?")

    @step()
    async def end_step(self, event: HumanInTheLoopInput.response) -> StopEvent:
        print(
            "[HumanInTheLoopAgent.end_step]",
            event.request_event.message,
            event.response,
        )
        return StopEvent()
