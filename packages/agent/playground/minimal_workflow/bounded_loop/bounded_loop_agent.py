from typing import ClassVar

from swiss_ai_hub.core.events.agent import StopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.bounded_loop.bounded_loop_agent_config import BoundedLoopAgentConfig
from playground.minimal_workflow.bounded_loop.events.begin_event import BeginEvent
from playground.minimal_workflow.bounded_loop.events.bounded_loop_a_event import BoundedLoopAEvent
from playground.minimal_workflow.bounded_loop.events.decision_event import DecisionEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.workflow.decorators.step import step


class BoundedLoopAgent(Agent):
    """Agent demonstrating bounded loop patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Bounded Loop Agent", de="Begrenzte Schleife Agent", fr="Agent Boucle Limitée", it="Agente Loop Limitato"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for bounded loop demo",
        de="Agent für begrenzte Schleife Demo",
        fr="Agent pour démo boucle limitée",
        it="Agente per demo loop limitato",
    )
    icon: ClassVar[str] = "mage:refresh"

    @step()
    async def start_step(self, event: UserMessageEvent, run_context: RunContext) -> BeginEvent:
        print("[SimpleAgent.start_step]")
        await run_context.set("loop_count", 0)
        return BeginEvent(count=0)

    @step()
    async def process_a_step(self, event: BeginEvent) -> BoundedLoopAEvent:
        print("[BoundedLoopAgent.process_a_step]")
        return BoundedLoopAEvent()

    @step()
    async def decision_step(
        self, event: BoundedLoopAEvent, agent_config: BoundedLoopAgentConfig, run_context: RunContext
    ) -> DecisionEvent | BeginEvent:
        loop_count = await run_context.get("loop_count")
        print("[BoundedLoopAgent.decision_step]", loop_count)
        if loop_count < agent_config.loop_max:
            await run_context.set("loop_count", loop_count + 1)
            return BeginEvent(count=loop_count + 1)

        return DecisionEvent()

    @step()
    async def end_step(self, event: DecisionEvent) -> StopEvent:
        print("[SimpleAgent.end_step]")
        return StopEvent()
