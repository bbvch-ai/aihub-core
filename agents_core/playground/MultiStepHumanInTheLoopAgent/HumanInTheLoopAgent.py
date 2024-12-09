from agents_core.agents.abstract.Agent import Agent
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent
from playground.MultiStepHumanInTheLoopAgent.Events.FirstStepHumanInTheLoop import FirstStepHumanInTheLoop
from playground.MultiStepHumanInTheLoopAgent.Events.SecondStepHumanInTheLoop import SecondStepHumanInTheLoop


class MultiStepHumanInTheLoopAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> FirstStepHumanInTheLoop.request:
        print("[MultiStepHumanInTheLoopAgent.start_step]")
        return FirstStepHumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def second_hitl(self, event: FirstStepHumanInTheLoop.response) -> SecondStepHumanInTheLoop.request:
        print("[FirstStepHumanInTheLoop.second_hitl]", event.request_event.question, event.response)
        return SecondStepHumanInTheLoop.invoke(question="Are you sure?")

    @step()
    async def end_step(self, event: SecondStepHumanInTheLoop.response) -> StopEvent:
        print("[MultiStepHumanInTheLoopAgent.end_step]", event.request_event.question, event.response)
        return StopEvent()