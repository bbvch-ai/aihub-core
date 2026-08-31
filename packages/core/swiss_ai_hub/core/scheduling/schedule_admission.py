import logging

from pydantic import ValidationError

from swiss_ai_hub.core.agents.agent_config import CRON_CONFIG_KEY
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

logger = logging.getLogger(__name__)


class ScheduleAdmission:
    """Decides whether a schedule may be saved, from what it will cost rather than from what it has cost.

    A cron expression is a declaration, not traffic. `CronScheduleCalculator` can say exactly how many
    runs it produces before a single one has fired, so the question "is this more than this deployment
    wants?" is answerable while an admin is still looking at the form — where the answer can name the
    problem and be acted on. Measuring the same number at run time instead can only stop runs after the
    fact, silently, in a subsystem nobody is watching.

    Two ceilings, because they answer different questions. The per-profile one bounds a single schedule
    and defaults to the tightest expression cron can produce, so out of the box it rejects nothing that
    can be written. The aggregate one bounds every schedule together — 400 hourly profiles are 288,000
    runs a month and each of those configs is unremarkable on its own — and defaults to off, because the
    right total depends on how many agents a deployment runs and what they cost.

    Deliberately not a spend limit. This bounds how often an agent starts, not what it does once started
    (#1766) or what it costs over time (#1767, #1452, #441). A run-count ceiling cannot see the run that
    loops fifty times, and pretending otherwise is how a guard ends up trusted for a job it cannot do.
    """

    @staticmethod
    def rejection_reason(
        schedule: CronSchedule,
        agent_class: str,
        agent_id: str,
        settings: SchedulerSettings | None = None,
    ) -> str | None:
        """Why this schedule may not be saved, or None if it may.

        Returns prose rather than raising, so the HTTP layer owns its own status code and the same check
        stays usable from anywhere else that writes a profile.
        """
        settings = settings or SchedulerSettings()

        # Bounded by whichever ceiling can actually reject something. One more than a ceiling is all that
        # has to be counted to know it was passed, which keeps an absurd expression cheap to refuse — and
        # when no ceiling is enforced there is nothing to count for, so an admin's save waits on nothing.
        budget = ScheduleAdmission._counting_budget(settings)
        if budget is None:
            return None

        runs = CronScheduleCalculator.runs_per_month(schedule, budget)

        per_profile = settings.enforced_profile_ceiling
        if per_profile is not None and runs > per_profile:
            return (
                f"this schedule runs more than {per_profile} times per 30 days, which is more than this "
                f"deployment allows for a single agent"
            )

        return ScheduleAdmission._aggregate_rejection_reason(runs, agent_class, agent_id, settings)

    @staticmethod
    def _counting_budget(settings: SchedulerSettings) -> int | None:
        """How far the schedule being saved has to be counted, or None if neither ceiling can reject it.

        Counting to a ceiling nothing can reach is not free: confirming an every-minute schedule sits
        within the default 43,200 means stepping croniter 43,200 times, about half a second, spent inside
        the request an admin is waiting on to reach an answer that was never in doubt.
        """
        ceilings = [c for c in (settings.enforced_profile_ceiling, settings.enforced_total_ceiling) if c is not None]
        return max(ceilings) + 1 if ceilings else None

    @staticmethod
    def _aggregate_rejection_reason(
        runs: int,
        agent_class: str,
        agent_id: str,
        settings: SchedulerSettings,
    ) -> str | None:
        ceiling = settings.enforced_total_ceiling
        if ceiling is None:
            return None

        already_scheduled = ScheduleAdmission._runs_scheduled_elsewhere(agent_class, agent_id, ceiling)
        total = already_scheduled + runs
        if total <= ceiling:
            return None

        # Counting stops once the ceiling is passed, so past that point the figure is a floor and not a
        # total. Saying so is the difference between a number an admin can act on and one that quietly
        # understates their estate by an order of magnitude.
        floor = "at least " if already_scheduled > ceiling else ""
        return (
            f"this schedule would bring all scheduled agents to {floor}{total} runs per 30 days, over "
            f"this deployment's limit of {ceiling}; {floor}{already_scheduled} are already scheduled "
            f"elsewhere"
        )

    @staticmethod
    def _runs_scheduled_elsewhere(agent_class: str, agent_id: str, budget: int) -> int:
        """Runs every *other* stored schedule produces in 30 days, counted no further than `budget`.

        The profile being saved is excluded by identity so an edit is measured against its siblings
        rather than against its own previous value, which would make raising a schedule impossible once
        the total sat near the ceiling.

        Bounded, like every other enumeration this subsystem does over a span it does not control: once
        the running total has passed the ceiling the verdict cannot change, so counting on would only
        make a rejection slower to reach.
        """
        counted = 0
        for config in AgentConfigEntityDocument.find_with_config_key(CRON_CONFIG_KEY):
            if config.agent_class == agent_class and config.agent_id == agent_id:
                continue

            raw = (config.config_data or {}).get(CRON_CONFIG_KEY)
            if CronSchedule.is_unscheduled(raw):
                continue
            try:
                stored = CronSchedule.model_validate(raw)
            except ValidationError:
                # A row that predates this validation, or one written before its class declared a cron.
                # It cannot be parsed, so it cannot be counted — and refusing every save until someone
                # finds it would be a far worse failure than undercounting the total.
                logger.warning(
                    "Not counting %s/%s toward the scheduled-run total: its stored schedule is not valid",
                    config.agent_class,
                    config.agent_id,
                )
                continue

            counted += CronScheduleCalculator.runs_per_month(stored, budget - counted + 1)
            if counted > budget:
                return counted
        return counted
