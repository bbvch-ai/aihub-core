from typing import ClassVar

from swiss_ai_hub.core.events.agent import BotInTheLoop, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.agent.bot_in_the_loop_agent.events.bot_in_the_loop_agent_start_event import BotInTheLoopAgentStartEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.workflow.decorators.step import step


class BotInTheLoopAgent(Agent):
    """Agent demonstrating bot-in-the-loop patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Bot In The Loop Agent",
        de="Bot-in-the-Loop Agent",
        fr="Agent Bot dans la Boucle",
        it="Agente Bot-in-the-Loop",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for BITL demo", de="Agent für BITL Demo", fr="Agent pour démo BITL", it="Agente per demo BITL"
    )
    icon: ClassVar[str] = "mage:robot"

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
