from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_lib.nats.events.human_in_the_loop import (
    HumanInTheLoopChat,
    HumanInTheLoopConfirmation,
    HumanInTheLoopInput,
)

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.HitlDemoAgent.events.HitlTypeSelection import HitlTypeSelection
from aihub_agent.workflow.decorators.step import step


class HitlDemoAgent(Agent):
    """Demo agent that showcases all three HITL types: input, confirmation, and chat."""

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
