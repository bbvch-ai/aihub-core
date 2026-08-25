"""Regression tests for a malformed cron schedule reaching storage.

Same seam and same root cause as the blank-name tests next door: submissions are validated against a model jambo
builds from the JSON schema, and `AgentSchedule`'s croniter and timezone checks are `model_validator`s that the
schema cannot express. Every cron position is a bare string there, so a cleared field arrives as `""` and validates.

The blast radius is what makes this worth its own file. A stored bad schedule does not merely fail to fire —
`AgentDispatcher` re-validates the real config on every control event, so manually triggered runs die too, and they
die before any step runs, which means no `ExceptionEvent` and nothing anywhere to say why.

Runs the real pipeline (`as_form()` -> configurable submission schema -> jambo model -> normalize -> validate)
rather than mocking it, because the defect exists precisely in what that pipeline drops.
"""

from typing import Annotated, Self

import pytest
from fastapi import HTTPException
from pydantic import BaseModel, Field
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form.elements.cron_input import CronInput
from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule
from swiss_ai_hub.jambo import SchemaConverter

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

FILLED = {"de": "Wert", "en": "Value", "fr": "Valeur", "it": "Valore"}

VALIDATORS = [
    InstanceConfigHelper.validate_config_for_create,
    InstanceConfigHelper.validate_config_for_update,
]

VALID_SCHEDULE = {
    "minute": "0",
    "hour": "7",
    "day_of_month": "*",
    "month": "*",
    "day_of_week": "1-5",
    "timezone": "Europe/Zurich",
}

MALFORMED_SCHEDULES = [
    pytest.param({**VALID_SCHEDULE, "minute": ""}, id="cleared-position"),
    pytest.param({**VALID_SCHEDULE, "hour": "banana"}, id="not-a-cron-position"),
    pytest.param({**VALID_SCHEDULE, "day_of_month": "99"}, id="position-out-of-range"),
    pytest.param({**VALID_SCHEDULE, "timezone": "Mars/Olympus"}, id="unknown-timezone"),
    pytest.param({k: v for k, v in VALID_SCHEDULE.items() if k != "month"}, id="missing-position"),
]


class ScheduledConfig(AgentConfig):
    """Stands in for any schedulable blueprint — the field name is what the scheduler reads, not the class."""

    schedule: Annotated[AgentSchedule | CronInput | None, Field(description="When this profile runs.")] = None

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            schedule=CronInput(label="Schedule"),
        )


def _model() -> type[BaseModel]:
    return SchemaConverter.build(ScheduledConfig.as_form().to_configurable_submission_model().model_json_schema())


def _config(**overrides) -> dict:
    return {"agent_id": "my-agent", "name": FILLED, "description": FILLED, "icon": "mage:robot", **overrides}


def _validate(validator, config: dict) -> BaseModel:
    return validator(InstanceConfigHelper.normalize_form_configuration(config), _model())


@pytest.mark.parametrize("validator", VALIDATORS)
@pytest.mark.parametrize("schedule", MALFORMED_SCHEDULES)
def test_a_malformed_schedule_is_rejected(validator, schedule):
    with pytest.raises(HTTPException) as exc_info:
        _validate(validator, _config(schedule=schedule))

    assert exc_info.value.status_code == 400
    assert "schedule" in exc_info.value.detail


def test_the_generated_model_alone_would_have_stored_it():
    """Pins the reason this guard has to exist at all rather than the config model being trusted.

    If jambo ever starts carrying `model_validator`s across, this fails and the guard becomes removable — which is
    worth being told about, because it is duplicated validation the moment that happens.
    """
    cleared = _config(schedule={**VALID_SCHEDULE, "minute": ""})

    assert _model().model_validate(InstanceConfigHelper.normalize_form_configuration(cleared)) is not None


@pytest.mark.parametrize("validator", VALIDATORS)
def test_a_valid_schedule_is_accepted(validator):
    assert _validate(validator, _config(schedule=VALID_SCHEDULE)) is not None


@pytest.mark.parametrize("validator", VALIDATORS)
@pytest.mark.parametrize("absent", [pytest.param(None, id="explicit-null"), pytest.param({}, id="empty-object")])
def test_an_unscheduled_profile_is_left_alone(validator, absent):
    """Clearing the enable toggle is how scheduling is switched off, and it must not read as a malformed cron."""
    assert _validate(validator, _config(schedule=absent)) is not None


@pytest.mark.parametrize("validator", VALIDATORS)
def test_a_blueprint_with_no_schedule_field_is_left_alone(validator):
    assert _validate(validator, _config()) is not None
