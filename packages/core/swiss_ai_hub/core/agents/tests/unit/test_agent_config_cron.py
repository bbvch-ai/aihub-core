from typing import Annotated, Self

import pytest
from pydantic import Field, ValidationError

from swiss_ai_hub.core.agents.agent_config import CRON_CONFIG_KEY, AgentConfig
from swiss_ai_hub.core.form.elements.cron_input import CronInput
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule


class _SubclassConfig(AgentConfig):
    """Reproduces the override shape every real agent config uses: re-list the base identity fields by
    hand rather than calling `super().as_form()`. The point is that such an override needs no `cron=`
    line and still ends up with a working schedule."""

    extra_setting: Annotated[str | InputText, Field(description="Something of the blueprint's own.")] = "x"

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            extra_setting=InputText(label=LocaleString(en="Extra")),
        )


def _form_names(config: AgentConfig) -> list[str]:
    return [element.name for element in config.to_formkit_form()]


def _schema_properties(config: AgentConfig) -> set[str]:
    return set(config.to_configurable_submission_model().model_json_schema()["properties"])


class TestAsFormLeavesCronUnset:
    def test_as_form_does_not_populate_cron(self) -> None:
        """The base cannot know whether its agent is schedulable, so it declines to guess."""
        assert AgentConfig.as_form().cron is None

    def test_an_unset_cron_is_not_configurable(self) -> None:
        """Configurability follows from the value being a form element, which is the whole mechanism
        that keeps a schedule off both published surfaces without filtering either of them."""
        assert CRON_CONFIG_KEY not in AgentConfig.as_form().get_configurable_fields()


class TestNonSchedulableAgentsAreOfferedNoSchedule:
    def test_the_form_carries_no_cron_element(self) -> None:
        assert CRON_CONFIG_KEY not in _form_names(AgentConfig.as_form().for_discovery(is_schedulable=False))

    def test_the_form_carries_no_empty_cron_group_either(self) -> None:
        """`to_formkit_form()` emits a placeholder group for a nullable *Form*-typed field so the UI can
        offer an enable toggle. CronSchedule is deliberately a plain BaseModel to stay off that path —
        otherwise every agent in the platform would ship an empty schedule fieldset."""
        elements = AgentConfig.as_form().for_discovery(is_schedulable=False).to_formkit_form()
        assert not [element for element in elements if element.name == CRON_CONFIG_KEY]

    def test_the_submission_schema_does_not_advertise_cron(self) -> None:
        """Stripping only the form would still let the API accept a schedule for an agent that can
        never be fired on one."""
        assert CRON_CONFIG_KEY not in _schema_properties(AgentConfig.as_form().for_discovery(is_schedulable=False))

    def test_a_hand_declared_cron_is_cleared(self) -> None:
        """A blueprint must not be able to offer a schedule it will never be fired on."""
        config = AgentConfig.as_form()
        config.cron = AgentConfig.cron_form_field()

        assert config.for_discovery(is_schedulable=False).cron is None


class TestSchedulableAgentsAreOfferedASchedule:
    def test_the_form_carries_the_cron_element(self) -> None:
        config = AgentConfig.as_form().for_discovery(is_schedulable=True)
        element = next(e for e in config.to_formkit_form() if e.name == CRON_CONFIG_KEY)

        assert element.formkit == "cronInput"

    def test_the_submission_schema_advertises_cron(self) -> None:
        assert CRON_CONFIG_KEY in _schema_properties(AgentConfig.as_form().for_discovery(is_schedulable=True))

    def test_a_subclass_that_never_mentions_cron_still_gets_one(self) -> None:
        """This is what makes the promotion cheap: none of the real config overrides need a `cron=` line,
        because the base leaves it unset and the runner injects it."""
        config = _SubclassConfig.as_form().for_discovery(is_schedulable=True)

        assert CRON_CONFIG_KEY in _form_names(config)
        assert {"extra_setting", CRON_CONFIG_KEY} <= _schema_properties(config)

    def test_the_element_resolves_its_labels(self) -> None:
        """A missing i18n key surfaces as the path itself, which would ship to the Admin UI verbatim."""
        element = AgentConfig.cron_form_field()

        assert element.label.en == "Schedule"
        assert "lib.agents.config" not in f"{element.help.en}{element.timezone_placeholder.en}"


class TestSubmittedSchedulesValidate:
    def test_a_submitted_schedule_validates_into_a_cron_schedule(self) -> None:
        """The data half of the duality: what an admin submits must land as a CronSchedule, not a dict."""
        config = AgentConfig.as_form().for_discovery(is_schedulable=True)
        submission_model = config.to_configurable_submission_model()

        submitted = submission_model.model_validate(
            {
                "agent_id": "demo",
                "name": {"en": "Demo"},
                "description": {"en": "Demo"},
                "icon": "mage:clock",
                CRON_CONFIG_KEY: {
                    "minute": "0",
                    "hour": "9",
                    "day_of_month": "*",
                    "month": "*",
                    "day_of_week": "1-5",
                    "timezone": "Europe/Zurich",
                },
            }
        )

        assert submitted.cron.expression == "0 9 * * 1-5"

    def test_a_schedule_survives_its_own_dump(self) -> None:
        """A schedule read back from storage was written from a model instance, not from request JSON."""
        schedule = CronSchedule(minute="0", hour="9", day_of_month="*", month="*", day_of_week="*", timezone="UTC")

        assert CronSchedule.model_validate(schedule.model_dump()) == schedule

    def test_the_form_element_is_not_mistaken_for_a_schedule(self) -> None:
        """A form-mode CronInput dict reaching storage must be rejected, not read as "every hour".

        Asserted on the missing positions specifically: `ValueError` alone would also pass if the element
        were rejected for some unrelated reason, and it is the *required* positions that do the rejecting.

        The element is built outside the block because `CronInput` is a Pydantic model too, so a
        `ValidationError` from constructing it would satisfy this assertion without `CronSchedule` ever
        having been asked anything.
        """
        form_element = CronInput(label=LocaleString(en="Schedule")).model_dump()

        with pytest.raises(ValidationError, match="minute"):
            CronSchedule.model_validate(form_element)
