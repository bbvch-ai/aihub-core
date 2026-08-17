from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form.elements.cron_input import CronInput
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.scheduling import AgentSchedule


class ScheduledDemoAgentConfig(AgentConfig):
    """Config for the scheduled demo agent.

    The `schedule` field is what the scheduler reads to decide when this profile runs. It is declared
    per blueprint rather than injected platform-side, so a schedulable agent stays a normal agent whose
    schedule is just another configurable setting.
    """

    schedule: Annotated[
        AgentSchedule | CronInput | None,
        Field(description="Cron schedule controlling when this profile runs automatically."),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            schedule=CronInput(
                label=LocaleString(en="Schedule", de="Zeitplan", fr="Planification", it="Pianificazione"),
                help=LocaleString(
                    en="When this profile runs automatically. Leave empty to disable scheduled runs.",
                    de="Wann dieses Profil automatisch läuft. Leer lassen, um geplante Läufe zu deaktivieren.",
                    fr="Quand ce profil s'exécute automatiquement. Laisser vide pour désactiver.",
                    it="Quando questo profilo viene eseguito automaticamente. Lasciare vuoto per disattivare.",
                ),
            ),
        )
