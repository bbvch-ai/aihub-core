from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.FirstStepHumanInTheLoop import (
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.SecondStepHumanInTheLoop import (
    SecondStepHumanInTheLoop,
)


class MultistepHumanInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        print("[MultistepHumanInTheLoopAgent.start_step]")
        return FirstStepHumanInTheLoop.invoke(message="Shall I continue?")

    @step()
    async def second_hitl(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
        print(
            "[FirstStepHumanInTheLoop.second_hitl]",
            event.request_event.message,
            event.response,
        )
        return SecondStepHumanInTheLoop.invoke(message="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print(
            "[MultistepHumanInTheLoopAgent.end_step]",
            event.request_event.message,
            event.response,
        )
        return StopEvent()
