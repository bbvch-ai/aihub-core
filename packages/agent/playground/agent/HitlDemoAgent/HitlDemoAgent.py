from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    HumanInTheLoopChat,
    HumanInTheLoopConfirmation,
    HumanInTheLoopInput,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleString

from playground.agent.HitlDemoAgent.events import HitlTypeSelection
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class HitlDemoAgent(Agent):
    """Demo agent that showcases all three HITL types: input, confirmation, and chat."""

    name: ClassVar[LocaleString] = LocaleString(
        en="HITL Demo Agent", de="HITL Demo Agent", fr="Agent Démo HITL", it="Agente Demo HITL"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Demo agent for HITL types",
        de="Demo Agent für HITL Typen",
        fr="Agent démo pour types HITL",
        it="Agente demo per tipi HITL",
    )
    icon: ClassVar[str] = "mage:stop"

    @step()
    async def ask_hitl_type(self, event: UserMessageEvent) -> HitlTypeSelection.request:
        """Ask user which HITL type to demonstrate."""
        print("[HitlDemoAgent.ask_hitl_type] Asking user which HITL type to test")
        return HitlTypeSelection.invoke(
            question="Which HITL type would you like to test? (input, confirmation, or chat)"
        )

    @step()
    async def invoke_selected_hitl(
        self, event: HitlTypeSelection.response
    ) -> HumanInTheLoopInput.request | HumanInTheLoopConfirmation.request | HumanInTheLoopChat.request:
        """Invoke the selected HITL type based on user's choice."""
        choice = event.response.lower().strip()
        print(f"[HitlDemoAgent.invoke_selected_hitl] User selected: {choice}")

        if "confirmation" in choice:
            return HumanInTheLoopConfirmation.invoke("Do you confirm this action?")
        elif "chat" in choice:
            return HumanInTheLoopChat.invoke("This is a chat-style question. What is your response?")
        else:  # Default to input
            return HumanInTheLoopInput.invoke("Please enter your text input:")

    @step()
    async def handle_hitl_response(
        self,
        event: HumanInTheLoopInput.response | HumanInTheLoopConfirmation.response | HumanInTheLoopChat.response,
        displayer: EventDisplayer,
    ) -> StopEvent:
        """Handle the HITL response and display the result."""
        if isinstance(event, HumanInTheLoopConfirmation.response):
            result = f"Confirmation received: {'Yes' if event.response else 'No'}"
        else:
            result = f"Response received: {event.response}"

        print(f"[HitlDemoAgent.handle_hitl_response] {result}")
        await displayer.display_chunk(result, model_name="HitlDemoAgent")
        return StopEvent()
