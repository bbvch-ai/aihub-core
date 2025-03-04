from typing import List

from time import time

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.annotations.custom_types.ListOfSize import FixedList
from aihub_agent.workflow.decorators.step import step
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB

N = 1000


class FanOutAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, config: AgentConfig, context: RunContext) -> List[FanOutA]:
        start = time()
        await context.set("start_time", start)
        payload = "a" * 1024 * 512
        # print("[FanOutAgent.start_step]", config.name.en)
        return [FanOutA(payload=payload) for _ in range(N)]

    @step()
    async def process_a(self, event: FanOutA, config: AgentConfig) -> FanOutB:
        # print("[FanOutAgent.process_a]", event.payload, config.name.en)
        return FanOutB(payload=event.payload)

    @step()
    async def stop_step(self, events: FixedList(FanOutB, N), config: AgentConfig, context: RunContext) -> StopEvent:
        # print("[FanOutAgent.stop_step]", config.name.en)
        start = await context.get("start_time")
        print("Time taken:", time() - start)
        return StopEvent()
