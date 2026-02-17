from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class MockKnowledgeBaseAgent(Agent):
    """Minimal worker agent for demo — returns a hardcoded knowledge base result."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Mock Knowledge Base Agent",
        de="Mock-Wissensbasis-Agent",
        fr="Agent Base de Connaissances Mock",
        it="Agente Base di Conoscenza Mock",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Returns hardcoded knowledge base results for testing",
        de="Gibt fest codierte Wissensbasis-Ergebnisse für Tests zurück",
        fr="Renvoie des résultats codés en dur pour les tests",
        it="Restituisce risultati codificati per i test",
    )
    icon: ClassVar[str] = "mage:book"

    @step()
    async def answer(self, event: UserMessageEvent) -> StopEvent:
        """Answer with a hardcoded knowledge base result."""
        query = event.messages[-1].content if event.messages else ""
        return StopEvent(result=f"Knowledge base result for: '{query}' — Bern is the de facto capital of Switzerland.")
