"""Regression tests for issue #135 — saving an agent/process with a blank name or description.

`InstanceConfigHelper` is the single validation seam for both agent and process configs, on both
the create and the update path, so exercising it here covers all four combinations.

The tests run the real pipeline (`as_form()` -> configurable submission schema -> jambo model ->
normalize -> validate) rather than mocking it: the defect only existed *because* the jambo-built
model drops `AgentConfig`'s own validators, so a mocked model would not reproduce it.
"""

import pytest
from fastapi import HTTPException
from pydantic import BaseModel
from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form import FormkitElement, Group, InputText, Repeater
from swiss_ai_hub.core.form.base.html_element import HtmlElement
from swiss_ai_hub.core.processes.process_config import ProcessConfig
from swiss_ai_hub.jambo import SchemaConverter

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

FILLED = {"de": "Wert", "en": "Value", "fr": "Valeur", "it": "Valore"}

VALIDATORS = [
    InstanceConfigHelper.validate_config_for_create,
    InstanceConfigHelper.validate_config_for_update,
]

BLANK_NAMES = [
    pytest.param({"de": None, "en": None, "fr": None, "it": None, "null": "My Agent"}, id="deselected-language"),
    pytest.param({"de": None, "en": None, "fr": None, "it": None}, id="all-locales-null"),
    pytest.param({"de": "", "en": "", "fr": "", "it": ""}, id="all-locales-empty"),
    pytest.param({"de": None, "en": "   ", "fr": None, "it": None}, id="whitespace-only"),
]


def _agent_model() -> type[BaseModel]:
    return SchemaConverter.build(AgentConfig.as_form().to_configurable_submission_model().model_json_schema())


def _process_model() -> type[BaseModel]:
    return SchemaConverter.build(ProcessConfig.as_form().to_configurable_submission_model().model_json_schema())


def _agent_config(**overrides) -> dict:
    return {
        "agent_id": "my-agent",
        "name": FILLED,
        "description": FILLED,
        "icon": "mage:robot",
        **overrides,
    }


def _validate(validator, config: dict, model: type[BaseModel]) -> BaseModel:
    return validator(InstanceConfigHelper.normalize_form_configuration(config), model)


@pytest.mark.parametrize("validator", VALIDATORS)
@pytest.mark.parametrize("blank_name", BLANK_NAMES)
def test_blank_name_is_rejected(validator, blank_name):
    with pytest.raises(HTTPException) as exc_info:
        _validate(validator, _agent_config(name=blank_name), _agent_model())

    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("validator", VALIDATORS)
def test_blank_description_is_rejected(validator):
    with pytest.raises(HTTPException) as exc_info:
        _validate(validator, _agent_config(description={"de": "", "en": "", "fr": "", "it": ""}), _agent_model())

    assert exc_info.value.status_code == 400


@pytest.mark.parametrize("validator", VALIDATORS)
def test_deselected_language_names_the_offending_field(validator):
    """The `"null"` key is what the frontend produced once the language toggle was cleared; it
    defeats `normalize_empty_locale_strings`, so this shape reached storage before the fix."""
    blank = {"de": None, "en": None, "fr": None, "it": None, "null": "My Agent"}

    with pytest.raises(HTTPException) as exc_info:
        _validate(validator, _agent_config(name=blank), _agent_model())

    assert "name" in exc_info.value.detail
    assert "description" not in exc_info.value.detail


@pytest.mark.parametrize("validator", VALIDATORS)
def test_single_populated_locale_is_accepted(validator):
    """Only one language is ever mandatory — the other three stay optional."""
    instance = _validate(
        validator, _agent_config(name={"de": None, "en": "Hello", "fr": None, "it": None}), _agent_model()
    )

    assert instance.name.en == "Hello"


@pytest.mark.parametrize("validator", VALIDATORS)
def test_fully_populated_config_is_accepted(validator):
    instance = _validate(validator, _agent_config(), _agent_model())

    assert instance.name.de == "Wert"
    assert instance.description.it == "Valore"


@pytest.mark.parametrize("validator", VALIDATORS)
def test_process_config_is_guarded_by_the_same_seam(validator):
    config = {"process_id": "my-process", "name": FILLED, "description": FILLED, "icon": "mage:broadcast"}

    with pytest.raises(HTTPException) as exc_info:
        _validate(validator, {**config, "name": {"de": "", "en": "", "fr": "", "it": ""}}, _process_model())

    assert exc_info.value.status_code == 400
    assert _validate(validator, config, _process_model()).name.en == "Value"


def test_config_without_identity_fields_is_left_alone():
    """The guard only fires for configs that actually declare name/description."""

    class Unrelated(BaseModel):
        some_setting: str

    InstanceConfigHelper.validate_identity_locale_fields(Unrelated(some_setting="x"))


class TestUndeclaredFields:
    """The walk that holds a submission to the elements its owner announced (#1850).

    Exercised directly rather than through a service, because the shapes that matter are the ones a
    well-behaved frontend never produces: a group that arrived as the wrong type, a repeater whose
    entries are not objects, a decorative element carrying no name at all.
    """

    @staticmethod
    def _elements() -> list[FormkitElement]:
        return [
            InputText(name="title", label="Title"),
            HtmlElement(el="h2", children="Section"),
            Group(name="enrichment", children=[InputText(name="model", label="Model")]),
            Repeater(name="sources", children=[InputText(name="model", label="Model")]),
        ]

    @staticmethod
    def _reject(config: dict) -> str:
        with pytest.raises(HTTPException) as exc_info:
            InstanceConfigHelper.reject_undeclared_fields(TestUndeclaredFields._elements(), config)
        assert exc_info.value.status_code == 400
        return exc_info.value.detail

    def test_a_configuration_of_only_announced_fields_is_accepted(self):
        InstanceConfigHelper.reject_undeclared_fields(
            self._elements(),
            {"title": "t", "enrichment": {"model": "m"}, "sources": [{"model": "m"}]},
        )

    def test_a_disabled_nullable_group_is_not_walked(self):
        """A cleared sub-form submits `null`; there is nothing to hold to the announced children."""
        InstanceConfigHelper.reject_undeclared_fields(self._elements(), {"enrichment": None, "sources": []})

    def test_a_group_of_the_wrong_type_is_left_to_the_model_validator(self):
        """`validate_config_for_create` already names it; reporting it twice would say two different things."""
        InstanceConfigHelper.reject_undeclared_fields(self._elements(), {"enrichment": "not-an-object"})

    def test_repeater_entries_that_are_not_objects_are_left_to_the_model_validator(self):
        InstanceConfigHelper.reject_undeclared_fields(self._elements(), {"sources": ["not-an-object", 3]})

    def test_an_element_without_a_name_declares_nothing_and_matches_nothing(self):
        """A decorative element carries no name, so it must neither declare a key nor crash the walk."""
        assert "bogus" in self._reject({"bogus": 1})

    def test_a_formkit_bookkeeping_key_is_ignored_at_every_depth(self):
        """`normalize_form_configuration` only strips these at the top level."""
        InstanceConfigHelper.reject_undeclared_fields(
            self._elements(),
            {"_form_name": "X", "enrichment": {"model": "m", "__enabled": True}},
        )

    def test_every_offending_path_is_reported_in_one_exception(self):
        detail = self._reject(
            {
                "bogus": 1,
                "enrichment": {"model": "m", "deep": 2},
                "sources": [{"model": "m"}, {"model": "m", "deeper": 3}],
            }
        )
        assert "bogus" in detail
        assert "enrichment.deep" in detail
        assert "sources.1.deeper" in detail
