from typing import ClassVar

from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    ConfiguredAgentConfig,
    StartStepConfig,
)
from playground.minimal_workflow.configured_workflow.events.EventConfiguredA import EventConfiguredA
from playground.minimal_workflow.configured_workflow.events.EventConfiguredB import EventConfiguredB
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class ConfiguredAgent(Agent):
    """Agent demonstrating configuration patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Configured Agent", de="Konfigurierter Agent", fr="Agent Configuré", it="Agente Configurato"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for configuration demo",
        de="Agent für Konfigurations Demo",
        fr="Agent pour démo configuration",
        it="Agente per demo configurazione",
    )
    icon: ClassVar[str] = "mage:settings"

    @step()
    async def start_step(self, event: StartEvent, start_config: StartStepConfig) -> EventConfiguredA:
        print(f"[ConfiguredAgent.start_step] Step config value: '{start_config.some_step_value}'")
        return EventConfiguredA(payload=start_config.some_step_value)

    @step()
    async def middle_step(self, event: EventConfiguredA, agent_config: ConfiguredAgentConfig) -> EventConfiguredB:
        print(f"[ConfiguredAgent.middle_step] Agent config value: '{agent_config.some_agent_value}'")
        return EventConfiguredB(payload=agent_config.some_agent_value)

    @step()
    async def end_step(self, event: EventConfiguredB) -> StopEvent:
        return StopEvent()
