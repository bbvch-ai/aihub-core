from aihub_lib.nats.events import StopEvent
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.workflow.decorators.step import step
from playground.agent.BotInTheLoopAgent.events.BotInTheLoopAgentStartEvent import BotInTheLoopAgentStartEvent


class BotInTheLoopAgent(Agent):
    @step()
    async def start_step(
        self, start_event: BotInTheLoopAgentStartEvent, run_context: RunContext
    ) -> BotInTheLoop.request:
        print("[BotInTheLoopAgent.start_step]")
        user = await run_context.get("user")
        question = "Are we there yet?"

        return BotInTheLoop.invoke(
            user=user,
            question=question,
            channel_config=start_event.channel_config,
        )

    @step()
    async def end_step(self, event: BotInTheLoop.response) -> BotInTheLoop.request | StopEvent:
        print(
            "[BotInTheLoopAgent.end_step]",
            f"Question: {event.request_event.question}",
            f"Response: {event.response}",
        )

        if event.responder:
            print(
                "[Responder Info]",
                f"User ID: {event.responder.user_id}",
                f"Name: {event.responder.user_name or 'N/A'}",
            )
            if event.responder.additional_info:
                print(f"Additional Info: {event.responder.additional_info}")
        else:
            print("[Responder Info] No responder information available")

        if event.response == "yes":
            return StopEvent()
        else:
            follow_up_question = "What about now?"
            return BotInTheLoop.invoke(
                user=event.request_event.user,
                question=follow_up_question,
                channel_config=event.request_event.channel_config,
            )
