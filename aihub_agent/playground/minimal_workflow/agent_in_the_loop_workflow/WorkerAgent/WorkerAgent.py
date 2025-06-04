from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.workflow.decorators.step import step
from aihub_lib.nats.events import UserMessageEvent
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.Events.ExtractNumberEvent import (
    ExtractNumberEvent,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.Events.WorkerStopEvent import WorkerStopEvent


class WorkerAgent(Agent):
    @step()
    async def start_step(self, event: UserMessageEvent) -> ExtractNumberEvent:
        print("[WorkerAgent.start_step]", event)
        return ExtractNumberEvent(number=int(event.messages[-1].content))

    @step()
    async def end_step(self, event: ExtractNumberEvent) -> WorkerStopEvent:
        print("[WorkerAgent.end_step]", event)
        return WorkerStopEvent(result=event.number * 2)
