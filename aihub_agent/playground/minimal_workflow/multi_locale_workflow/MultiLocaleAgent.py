from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import StopEvent, StartEvent
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgentConfig import MultiLocaleAgentConfig

from playground.minimal_workflow.multi_locale_workflow.events.MultiLocaleEvent import MultiLocaleEvent


class MultiLocaleAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, t: LocaleHandler, agent_config: MultiLocaleAgentConfig) -> MultiLocaleEvent:
        print(f"[MultiLocaleAgent.start_step] Start step in locale {event.locale}.")
        print(f"[MultiLocaleAgent.start_step] Lib Core says: {t('lib.common.test')}.")
        print(f"[MultiLocaleAgent.start_step] Agents Core says: {t('agents.thought.test')}.")
        print(f"[MultiLocaleAgent.start_step] Local Agent says: {t('myagent.myscope.test')}.")
        print(f"[MultiLocaleAgent.start_step] Config says: {t(agent_config.locale_path)}.")
        return MultiLocaleEvent(payload=t(agent_config.locale_path))

    @step()
    async def end_step(self, event: MultiLocaleEvent) -> StopEvent:
        print("[MultiLocaleAgent.stop_step] Stop step.")
        return StopEvent()
