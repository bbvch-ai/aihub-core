import asyncio

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class LongRunningAgent(Agent):
    @step()
    async def start_step(self, _: UserMessageEvent, displayer: EventDisplayer) -> StopEvent:
        for i in range(20):
            await displayer.display_chunk(f"{i}\n", model_name="model")
            await asyncio.sleep(1)
        return StopEvent()
