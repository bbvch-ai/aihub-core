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
from swiss_ai_hub.core.form import Checkbox, FormkitElement, Group, InputText, Repeater
from swiss_ai_hub.core.form.base.html_element import HtmlElement
from swiss_ai_hub.core.imap import EmailClassificationSettings, ImapClientConfig
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


class TestBlankRequiredFields:
    """The walk that holds a submission to the `required` its owner announced (#219).

    `required` on a form element is FormKit's — the user must put something here — while the generated
    model only carries the schema's, which is that the key is present. `""` satisfies the second and not
    the first, so an empty mandatory field validated and was stored; the browser's rule was the sole
    thing rejecting it, and the import endpoint never ran that rule at all.

    A blank also arrives in two different shapes depending on how it got there — an untouched fresh field
    seeds to `None` (no Pydantic default to fall back to), a template's placeholder carries `""` (see
    `test_the_mailbox_template_ships_a_connection_that_must_be_filled_in`) — and the guard has to treat
    both as the same defect rather than leaning on whichever one Pydantic's own type check happens to
    reject for free.
    """

    @staticmethod
    def _elements() -> list[FormkitElement]:
        return [
            InputText(name="title", label="Title", required=True),
            InputText(name="note", label="Note"),
            Checkbox(name="agreed", label="Agreed", required=True),
            HtmlElement(el="h2", children="Section"),
            Group(name="enrichment", children=[InputText(name="model", label="Model", required=True)]),
            Repeater(name="sources", children=[InputText(name="model", label="Model", required=True)]),
        ]

    @staticmethod
    def _filled() -> dict:
        return {
            "title": "t",
            "agreed": False,
            "enrichment": {"model": "m"},
            "sources": [{"model": "m"}],
        }

    @staticmethod
    def _reject(config: dict) -> str:
        with pytest.raises(HTTPException) as exc_info:
            InstanceConfigHelper.reject_blank_required_fields(TestBlankRequiredFields._elements(), config)
        assert exc_info.value.status_code == 400
        return exc_info.value.detail

    def test_a_fully_filled_configuration_is_accepted(self):
        InstanceConfigHelper.reject_blank_required_fields(self._elements(), self._filled())

    def test_an_empty_string_in_a_required_field_is_rejected(self):
        """The template shape of the defect: present, typed correctly, and empty."""
        assert "title" in self._reject({**self._filled(), "title": ""})

    def test_a_null_in_a_required_field_is_rejected(self):
        """The manual-create shape: an untouched field seeds to `None`, not `""` — Pydantic's own type
        check happens to reject this one for a plain `str` field, but the guard must not depend on that
        accident, since the same field can just as easily arrive as `""` instead (see the string test)."""
        assert "title" in self._reject({**self._filled(), "title": None})

    def test_a_missing_required_field_is_rejected_as_blank(self):
        """Named the same way as an empty one — to the person filling the form they are one mistake."""
        config = self._filled()
        del config["title"]
        assert "title" in self._reject(config)

    def test_an_optional_field_may_be_blank(self):
        InstanceConfigHelper.reject_blank_required_fields(self._elements(), {**self._filled(), "note": ""})

    @pytest.mark.parametrize("value", [False, 0, 0.0], ids=["false", "zero", "zero-float"])
    def test_a_falsy_value_is_a_value_and_not_a_blank(self, value):
        """FormKit's `empty()` says the same, which is why an unchecked box satisfies `required` there."""
        InstanceConfigHelper.reject_blank_required_fields(self._elements(), {**self._filled(), "agreed": value})

    def test_whitespace_is_not_blank_because_the_browser_accepted_it(self):
        """Plain `required` does not trim; `required:trim` is a separate opt-in rule. Being stricter here
        would reject a submission the user watched pass validation in the form."""
        InstanceConfigHelper.reject_blank_required_fields(self._elements(), {**self._filled(), "title": "   "})

    def test_a_disabled_nullable_group_is_not_walked(self):
        """A cleared sub-form submits `null`. Requiring the children it is not submitting would make the
        section's toggle impossible to leave off."""
        InstanceConfigHelper.reject_blank_required_fields(
            self._elements(), {**self._filled(), "enrichment": None, "sources": []}
        )

    def test_a_conditional_field_is_skipped(self):
        """Whether it is shown depends on a FormKit expression over the rest of the form, which only the
        browser can evaluate. Rejecting a field the user was never offered is worse than the gap closed here."""
        elements = [InputText(name="folder", label="Folder", required=True, condition_if="$get(enabled).value")]
        InstanceConfigHelper.reject_blank_required_fields(elements, {"folder": ""})

    def test_a_blank_required_field_inside_a_repeater_names_its_row(self):
        config = {**self._filled(), "sources": [{"model": "m"}, {"model": ""}]}
        assert "sources.1.model" in self._reject(config)

    def test_every_offending_path_is_reported_in_one_exception(self):
        detail = self._reject({"enrichment": {"model": ""}, "sources": [{"model": None}]})
        assert "title" in detail
        assert "enrichment.model" in detail
        assert "sources.0.model" in detail

    def test_the_mailbox_template_ships_a_connection_that_must_be_filled_in(self):
        """The reported case, against the real announced form rather than a stand-in: the shared-mailbox
        template ships `ImapClientConfig(host="", username="", password="")` as placeholders for the admin,
        and until now nothing but the browser made them fill it in."""
        elements = ImapClientConfig.as_form().to_formkit_form()
        connection = {"port": 993, "inbox_folder": "INBOX", "max_messages": 50}

        with pytest.raises(HTTPException) as exc_info:
            InstanceConfigHelper.reject_blank_required_fields(
                elements, {**connection, "host": "", "username": "", "password": ""}
            )

        detail = exc_info.value.detail
        assert "host: required field is empty" in detail
        assert "username: required field is empty" in detail
        assert "password: required field is empty" in detail

        InstanceConfigHelper.reject_blank_required_fields(
            elements, {**connection, "host": "imap.example.com", "username": "a@example.com", "password": "pw"}
        )

    def test_a_manual_create_seeds_the_same_fields_to_null_and_is_equally_rejected(self):
        """The other shape the same fields arrive in when nobody used a template: an untouched field with
        no Pydantic default seeds to `None`, not `""`. Both must be caught the same way."""
        elements = ImapClientConfig.as_form().to_formkit_form()
        connection = {"port": 993, "inbox_folder": "INBOX", "max_messages": 50}

        detail = self._detail_of(elements, {**connection, "host": None, "username": None, "password": ""})
        assert "host: required field is empty" in detail
        assert "username: required field is empty" in detail
        assert "password: required field is empty" in detail

    @staticmethod
    def _detail_of(elements: list[FormkitElement], config: dict) -> str:
        with pytest.raises(HTTPException) as exc_info:
            InstanceConfigHelper.reject_blank_required_fields(elements, config)
        return exc_info.value.detail

    def test_a_model_that_inherits_when_unset_is_not_required(self):
        """`classification.model_name` and a category's `knowledge_namespace` both mean "use the default"
        when unset, so the guard must not demand them — they are optional, not blank. Fixed on the
        blueprint side (str | None, default None) alongside this guard."""
        elements = EmailClassificationSettings.as_form().to_formkit_form()

        # Deliberately partial: the point is which paths the walk does *not* name, so the settings the
        # blueprint genuinely requires are left out rather than filled in with noise.
        with pytest.raises(HTTPException) as exc_info:
            InstanceConfigHelper.reject_blank_required_fields(
                elements, {"model_name": None, "categories": [{"knowledge_namespace": None}]}
            )

        detail = exc_info.value.detail
        assert "model_name" not in detail
        assert "knowledge_namespace" not in detail

    def test_knowledge_databases_left_unset_is_not_required(self):
        """Only needed when a category names a collection — genuinely optional, unlike
        `NamespaceSelectionAgentConfig.bucket_names`, which reuses the same `KnowledgeDatabaseSelector`
        element but carries `MinLen(1)` and must stay required. The distinction is per field
        (`str | None` on this one), not per element type — the shared element cannot make both true."""
        elements = EmailClassificationSettings.as_form().to_formkit_form()

        InstanceConfigHelper.reject_blank_required_fields(
            elements,
            {
                "categories": [],
                "knowledge_databases": None,
                "fallback_folder": "a",
                "failure_folder": "b",
                "number_of_input_tokens": 8192,
                "classification_prompt": "p",
            },
        )
