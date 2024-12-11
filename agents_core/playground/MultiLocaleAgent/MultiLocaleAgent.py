from agents_core.agents.abstract.Agent import Agent
from agents_core.workflow.decorators.step import step
from lib_core.i18n.LocaleHandler import LocaleHandler
from lib_core.nats.events import StopEvent, StartEvent


class MultiLocaleAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent, t: LocaleHandler) -> StopEvent:
        print(f"[MultiLocaleAgent.start_step] Start step in locale {event.locale}.")
        print(f"[MultiLocaleAgent.start_step] Lib Core says: {t('lib.common.test')}.")
        print(f"[MultiLocaleAgent.start_step] Agents Core says: {t('agents.prompt.test')}.")
        print(f"[MultiLocaleAgent.start_step] Local Agent says: {t('myagent.myscope.test')}.")
        pass