from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from playground.minimal_workflow.multi_locale_workflow.events.MultiLocaleEvent import MultiLocaleEvent
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgentConfig import MultiLocaleAgentConfig
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class MultiLocaleAgent(Agent):
    """Agent demonstrating multi-locale patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Multi Locale Agent", de="Multi-Locale Agent", fr="Agent Multi-Locale", it="Agente Multi-Locale"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for multi-locale demo",
        de="Agent für Multi-Locale Demo",
        fr="Agent pour démo multi-locale",
        it="Agente per demo multi-locale",
    )
    icon: ClassVar[str] = "mage:globe"

    @step()
    async def start_step(
        self, event: UserMessageEvent, t: LocaleHandler, agent_config: MultiLocaleAgentConfig
    ) -> MultiLocaleEvent:
        print(f"[MultiLocaleAgent.start_step] Start step in locale {event.locale}.")
        print(f"[MultiLocaleAgent.start_step] Lib Core says: {t('lib.common.test')}.")
        print(f"[MultiLocaleAgent.start_step] Agents Core says: {t('agent.thought.test')}.")
        print(f"[MultiLocaleAgent.start_step] Local Agent says: {t('myagent.myscope.test')}.")
        print(f"[MultiLocaleAgent.start_step] Config says: {t(agent_config.locale_path)}.")
        return MultiLocaleEvent(payload=t(agent_config.locale_path))

    @step()
    async def end_step(self, _: MultiLocaleEvent) -> StopEvent:
        print("[MultiLocaleAgent.stop_step] Stop step.")
        return StopEvent()
