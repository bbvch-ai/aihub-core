from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import ANONYMISE_CONFIG_KEY, AgentConfig
from swiss_ai_hub.core.form.elements.checkbox import Checkbox
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class _BlueprintConfig(AgentConfig):
    """The override shape every real blueprint uses: base identity fields re-listed by hand, nothing about
    anonymisation. The toggle must still reach its form."""

    system_prompt: Annotated[str | InputText, Field(description="Something of the blueprint's own.")] = "x"

    @classmethod
    def as_form(cls) -> Self:
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            system_prompt=InputText(label=LocaleString(en="System prompt")),
        )


def _form_names(config: AgentConfig) -> list[str]:
    return [element.name for element in config.to_formkit_form()]


def test_should_be_off_when_a_stored_profile_has_no_value() -> None:
    config = AgentConfig(agent_id="a", name=LocaleString(en="A"), description=LocaleString(en="A"))

    assert config.anonymise is False


def test_should_not_be_on_the_base_form_before_discovery() -> None:
    assert ANONYMISE_CONFIG_KEY not in AgentConfig.as_form().get_configurable_fields()


def test_should_offer_the_toggle_on_a_blueprint_form_without_blueprint_code() -> None:
    published = _BlueprintConfig.as_form().for_discovery(is_schedulable=False)

    assert ANONYMISE_CONFIG_KEY in _form_names(published)
    assert isinstance(published.anonymise, Checkbox)


def test_should_offer_the_toggle_on_schedulable_and_other_blueprints_alike() -> None:
    for is_schedulable in (True, False):
        assert ANONYMISE_CONFIG_KEY in _form_names(
            _BlueprintConfig.as_form().for_discovery(is_schedulable=is_schedulable)
        )


def test_should_accept_the_toggle_in_the_submission_schema() -> None:
    published = _BlueprintConfig.as_form().for_discovery(is_schedulable=False)

    schema = published.to_configurable_submission_model().model_json_schema()

    assert schema["properties"][ANONYMISE_CONFIG_KEY]["type"] == "boolean"


def test_should_read_the_stored_toggle_back_at_run_time() -> None:
    config = _BlueprintConfig.model_validate(
        {"agent_id": "hr", "name": {"en": "HR"}, "description": {"en": "HR"}, "anonymise": True}
    )

    assert config.anonymise is True
