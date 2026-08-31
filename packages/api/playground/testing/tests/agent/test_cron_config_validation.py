"""Save-time validation of a profile's cron schedule.

Profile submissions are checked against a model jambo builds from the blueprint's JSON schema, which
reproduces the schema's shape and none of its Python validators. So `"minute": "99"` used to validate
here and reach storage, where the scheduler skipped it with an error log and the admin who typed it got
no feedback at all.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from pydantic import BaseModel
from swiss_ai_hub.core.persistence import AgentInstanceRef
from swiss_ai_hub.core.scheduling import SchedulerSettings

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

_ADMISSION = "swiss_ai_hub.core.scheduling.schedule_admission"

_VALID = {
    "minute": "0",
    "hour": "9",
    "day_of_month": "*",
    "month": "*",
    "day_of_week": "1-5",
    "timezone": "Europe/Zurich",
}


class _AcceptsAnything(BaseModel):
    """Stands in for the jambo-generated model, which accepts a schedule's shape without its validators."""

    model_config = {"extra": "allow"}


def _validate(schedule: object) -> None:
    InstanceConfigHelper.validate_config_for_create(
        {"agent_id": "demo", "cron": schedule},
        _AcceptsAnything,
    )


class TestAcceptsAWorkableSchedule:
    def test_a_valid_schedule_passes(self) -> None:
        _validate(_VALID)

    def test_no_schedule_at_all_passes(self) -> None:
        """Most agents are not schedulable, and a schedulable one need not be scheduled."""
        InstanceConfigHelper.validate_config_for_create({"agent_id": "demo"}, _AcceptsAnything)

    def test_a_non_object_schedule_is_left_to_the_generated_model(self) -> None:
        """Shape is the generated model's job; this check only adds the validators it cannot carry."""
        _validate("0 9 * * 1-5")


class TestRejectsAnUnfireableSchedule:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("minute", "99"),
            ("hour", "25"),
            ("day_of_week", "8"),
            ("month", "not-a-month"),
        ],
    )
    def test_an_out_of_range_position_is_rejected(self, field: str, value: str) -> None:
        with pytest.raises(HTTPException) as raised:
            _validate({**_VALID, field: value})

        assert raised.value.status_code == 400
        assert "Configuration validation failed" in raised.value.detail

    def test_an_unknown_timezone_is_rejected(self) -> None:
        """A bad timezone is silent otherwise: the cron parses, it just never means what was intended."""
        with pytest.raises(HTTPException) as raised:
            _validate({**_VALID, "timezone": "Mars/Olympus_Mons"})

        assert raised.value.status_code == 400

    def test_a_partial_schedule_is_rejected(self) -> None:
        """Defaulting the missing positions would turn a half-filled form into unattended hourly runs."""
        with pytest.raises(HTTPException) as raised:
            _validate({"minute": "0"})

        assert raised.value.status_code == 400

    def test_a_form_mode_element_reaching_storage_is_rejected(self) -> None:
        """A CronInput dict has none of the positions, so it must not validate as "every hour"."""
        with pytest.raises(HTTPException) as raised:
            _validate({"formkit": "cronInput", "label": "Schedule"})

        assert raised.value.status_code == 400

    def test_the_update_path_is_guarded_too(self) -> None:
        """An admin can just as easily break a working schedule as create a broken one."""
        with pytest.raises(HTTPException) as raised:
            InstanceConfigHelper.validate_config_for_update(
                {"agent_id": "demo", "cron": {**_VALID, "minute": "99"}},
                _AcceptsAnything,
            )

        assert raised.value.status_code == 400


class TestAnUntouchedScheduleIsNotASchedule:
    """`normalize_empty_objects_to_none` only nullifies a literally empty dict, but a group of text
    inputs nobody filled in serialises as blank strings."""

    def test_all_blank_positions_are_treated_as_unscheduled(self) -> None:
        """Rejecting this would 400 every save on a schedulable agent whose owner wants no schedule."""
        _validate({key: "" for key in _VALID})

    def test_blank_with_whitespace_is_also_unscheduled(self) -> None:
        _validate({key: "   " for key in _VALID})

    def test_a_partially_filled_schedule_is_still_rejected(self) -> None:
        """Someone who filled in one position meant to set a schedule and got it wrong."""
        with pytest.raises(HTTPException) as raised:
            _validate({**{key: "" for key in _VALID}, "hour": "9"})

        assert raised.value.status_code == 400


class TestRejectsASchedulePastTheDeploymentsCeiling:
    """The second half of save-time validation: not "is this a cron expression" but "is this more work
    than this deployment wants". Both are answerable from the expression alone, so both belong in front
    of the admin who typed it rather than in a counter they will never see."""

    @staticmethod
    def _validate(schedule: dict, settings: SchedulerSettings | None = None) -> None:
        """Drives the real admission check, with the stored estate empty and the knobs settable."""
        with (
            patch(f"{_ADMISSION}.AgentConfigEntityDocument.find_with_config_key", return_value=[]),
            patch(f"{_ADMISSION}.SchedulerSettings", return_value=settings or SchedulerSettings()),
        ):
            InstanceConfigHelper.validate_config_for_create(
                {"agent_id": "demo", "cron": schedule},
                _AcceptsAnything,
                AgentInstanceRef(agent_class="CronDemoAgent", agent_id="demo"),
            )

    def test_the_default_ceiling_accepts_every_minute(self) -> None:
        """Every-minute is a supported schedule. A deployment nobody has configured must not refuse it,
        or the platform is offering something it will not honour."""
        self._validate({**_VALID, "minute": "*", "hour": "*", "day_of_week": "*"})

    def test_an_over_ceiling_schedule_is_a_400_naming_the_problem(self) -> None:
        with pytest.raises(HTTPException) as rejected:
            self._validate(
                {**_VALID, "minute": "*", "hour": "*"},
                SchedulerSettings(MAX_RUNS_PER_PROFILE_PER_MONTH=100),
            )

        assert rejected.value.status_code == 400
        assert "runs more than 100 times per 30 days" in rejected.value.detail

    def test_without_an_identity_the_check_is_skipped(self) -> None:
        """Processes share this helper and carry no schedule; without knowing which profile is being
        written the aggregate check would count it against itself."""
        _validate({**_VALID, "minute": "*", "hour": "*"})
