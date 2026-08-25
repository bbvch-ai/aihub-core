from typing import Annotated, Self
from zoneinfo import ZoneInfo, available_timezones

from croniter import croniter
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CronSchedule(BaseModel):
    """The cron schedule of one agent profile: the five standard cron positions plus a timezone.

    The positions are kept as separate fields rather than a single "0 12 * * *" string so the Admin UI
    (#1581) can offer per-position editing and presets without parsing, and so a malformed position is
    rejected at the field that caused it.

    The timezone is what makes "every day at 12:00" mean the same wall-clock time year-round: cron
    occurrences are computed in this zone and converted to UTC, so a daily schedule survives DST shifts.

    Deliberately a plain `BaseModel`, not a `Form`, even though it is the data half of a duality pair
    with `CronInput`. Being a `Form` bought nothing — it never renders as a nested group, because in form
    mode the field holds the `CronInput` instead — and cost two things. It emitted a `_form_name`
    computed field, so a schedule could not survive its own `model_dump()` while unknown keys were
    forbidden; and `to_formkit_form()` treats a nullable `Form`-typed field as a sub-form to be wrapped
    in a placeholder `Group`, which for a field on the `AgentConfig` base would mean *every* agent's form
    carrying an empty schedule fieldset.
    """

    # Every position is required. Defaulting them would make an unrecognised payload — a form-mode
    # CronInput dict that reached storage, say — validate silently into "every hour" and start
    # unattended runs nobody configured. Surplus keys are tolerated: requiring every position is what
    # actually rejects an unrecognised payload, and it does so on the missing fields rather than the
    # surplus ones.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    minute: Annotated[str, Field(description="Cron minute position (0-59).")]
    hour: Annotated[str, Field(description="Cron hour position (0-23).")]
    day_of_month: Annotated[str, Field(description="Cron day-of-month position (1-31).")]
    month: Annotated[str, Field(description="Cron month position (1-12).")]
    day_of_week: Annotated[str, Field(description="Cron day-of-week position (0-6, Sunday is 0).")]
    timezone: Annotated[
        str,
        Field(description="IANA timezone the cron positions are interpreted in, e.g. 'Europe/Zurich'."),
    ] = "UTC"

    @property
    def expression(self) -> str:
        """The five positions as a standard cron expression."""
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"

    @property
    def zone_info(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @model_validator(mode="after")
    def _validate_expression_and_timezone(self) -> Self:
        """Reject malformed crons and unknown timezones at configuration time rather than at fire time."""
        if not croniter.is_valid(self.expression):
            raise ValueError(f"Invalid cron expression: {self.expression!r}")
        if self.timezone not in available_timezones():
            raise ValueError(f"Unknown timezone: {self.timezone!r}")
        return self
