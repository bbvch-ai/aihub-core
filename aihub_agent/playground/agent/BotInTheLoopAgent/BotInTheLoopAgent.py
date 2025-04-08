from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.context.thread.ThreadContext import ThreadContext
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent


class BotInTheLoopAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, run_context: RunContext) -> BotInTheLoop.request:
        print("[BotInTheLoopAgent.start_step]")
        user = await run_context.get("user")
        return BotInTheLoop.invoke(user=user, question="Shall I continue?")

    @step()
    async def end_step(self, event: BotInTheLoop.response) -> StopEvent:
        print(
            "[BotInTheLoopAgent.end_step]",
            event.request_event.question,
            event.response,
        )
        return StopEvent()
