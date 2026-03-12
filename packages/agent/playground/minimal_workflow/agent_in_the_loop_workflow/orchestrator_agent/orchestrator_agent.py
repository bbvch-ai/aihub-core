from typing import ClassVar

from swiss_ai_hub.core.events.agent import AgentInTheLoop, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.agent_in_the_loop_workflow.orchestrator_agent.events.orchestration_result_event import (
    OrchestrationResultEvent,
)
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class OrchestratorAgent(Agent):
    """Agent demonstrating orchestration of sub-agents."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Orchestrator Agent", de="Orchestrator Agent", fr="Agent Orchestrateur", it="Agente Orchestratore"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for orchestration demo",
        de="Agent für Orchestrierungs Demo",
        fr="Agent pour démo orchestration",
        it="Agente per demo orchestrazione",
    )
    icon: ClassVar[str] = "mage:broadcast"

    @step()
    async def start_step(self, event: UserMessageEvent) -> AgentInTheLoop.request:
        print("[OrchestratorAgent.start_step]", event)
        return AgentInTheLoop.invoke(agent_id="worker_agent", agent_class="WorkerAgent", start_event=event)

    @step()
    async def end_step(self, response: AgentInTheLoop.response) -> OrchestrationResultEvent:
        print("[OrchestratorAgent.end_step]", response.stop_event)
        return OrchestrationResultEvent(result=response.stop_event.result)

    @step()
    async def exception_step(self, response: AgentInTheLoop.exception) -> OrchestrationResultEvent:
        print("[OrchestratorAgent.exception_step]", response.exception_event)
        return OrchestrationResultEvent(result=-1)
