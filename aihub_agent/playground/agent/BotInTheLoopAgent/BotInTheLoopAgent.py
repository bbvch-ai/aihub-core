from aihub_agent.agents.Agent import Agent
from aihub_lib.nats.context.run.RunContext import RunContext
from aihub_lib.nats.events.bot_in_the_loop.BotInTheLoop import BotInTheLoop

from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StopEvent, UserMessageEvent


class BotInTheLoopAgent(Agent):
    @step()
    async def start_step(self, _: UserMessageEvent, run_context: RunContext) -> BotInTheLoop.request:
        print("[BotInTheLoopAgent.start_step]")
        user = await run_context.get("user")

        # IMPORTANT: Only provide the Slack channel ID (starts with C)
        # Do NOT include bot_id or team_id - they will be fetched automatically
        return BotInTheLoop.invoke(
            user=user,
            question="Are we there yet?",
            slack_channel_id="C08MCK6LEBY",  # Only the channel ID is needed
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
                slack_channel_id=event.request_event.slack_channel_id,
            )
