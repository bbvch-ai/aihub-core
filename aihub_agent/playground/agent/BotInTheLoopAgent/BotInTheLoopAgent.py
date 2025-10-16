from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.workflow.decorators.step import step


class BotInTheLoopAgent(Agent):
    @step()
    async def start_step(self, _: UserMessageEvent, run_context: RunContext) -> BotInTheLoop.request:
        print("[BotInTheLoopAgent.start_step]")
        user = await run_context.get("user")

        # IMPORTANT: Only provide the Slack channel ID (starts with C)
        # Do NOT include bot_id or team_id - they will be fetched automatically
        return BotInTheLoop.invoke(
            user=user, question="Are we there yet?", teams_channel_id="19:e633e0fc55604e4f9d46f9ba46f50045@thread.tacv2"
        )

    @step()
    async def end_step(self, event: BotInTheLoop.response) -> BotInTheLoop.request | StopEvent:
        # Print basic response information
        print(
            "[BotInTheLoopAgent.end_step]",
            f"Question: {event.request_event.question}",
            f"Response: {event.response}",
        )

        # Print responder information if available
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
            # For subsequent messages, we can use the same conversation_id from the request event
            # This will be the original channel ID for convenience
            return BotInTheLoop.invoke(
                user=event.request_event.user,
                question="What about now?",
                teams_channel_id=event.request_event.teams_channel_id,
            )
