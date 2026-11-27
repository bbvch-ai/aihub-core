from typing import ClassVar

from swiss_ai_hub.core.events.agent import HumanInTheLoopConfirmation, StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.in_the_loop_timeout_workflow.question_settled_event import QuestionSettledEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class InTheLoopTimeoutAgent(Agent):
    """Asks a person to confirm and carries on without them when nobody answers within the deadline."""

    name: ClassVar[LocaleString] = LocaleString(en="In The Loop Timeout Agent")
    description: ClassVar[LocaleString] = LocaleString(en="Falls back when a question goes unanswered")
    icon: ClassVar[str] = "mage:clock"

    ANSWER_WITHIN_SECONDS: ClassVar[float] = 2

    @step()
    async def ask_step(self, event: StartEvent) -> HumanInTheLoopConfirmation.request:
        return HumanInTheLoopConfirmation.invoke(
            question="Shall I continue?", timeout_seconds=InTheLoopTimeoutAgent.ANSWER_WITHIN_SECONDS
        )

    @step()
    async def answered_step(self, answer: HumanInTheLoopConfirmation.response) -> QuestionSettledEvent:
        return QuestionSettledEvent(outcome="confirmed" if answer.response else "declined")

    @step()
    async def unanswered_step(self, timeout: HumanInTheLoopConfirmation.timeout) -> QuestionSettledEvent:
        return QuestionSettledEvent(outcome=f"no answer within {timeout.timeout_seconds:g}s, continuing anyway")

    @step()
    async def end_step(self, settled: QuestionSettledEvent) -> StopEvent:
        return StopEvent()
