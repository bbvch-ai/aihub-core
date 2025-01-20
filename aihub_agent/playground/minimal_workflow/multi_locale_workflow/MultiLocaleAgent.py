from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import StopEvent, StartEvent

from playground.minimal_workflow.multi_locale_workflow.events.EventA import EventA


class MultiLocaleAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, t: LocaleHandler) -> StopEvent:
        print(f"[MultiLocaleAgent.start_step] Start step in locale {event.locale}.")
        print(f"[MultiLocaleAgent.start_step] Lib Core says: {t('lib.common.test')}.")
        print(f"[MultiLocaleAgent.start_step] Agents Core says: {t('agents.prompt.test')}.")
        print(f"[MultiLocaleAgent.start_step] Local Agent says: {t('myagent.myscope.test')}.")
        return EventA(payload=t("lib.common.test"))

    @step()
    async def end_step(self, event: EventA) -> StopEvent:
        print("[MultiLocaleAgent.stop_step] Stop step.")
        return StopEvent()
