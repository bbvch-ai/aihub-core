from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.processes.process_config import ProcessConfig


def _label() -> LocaleString:
    return LocaleString(de="Name", en="Name", fr="Nom", it="Nome")


def test_required_locale_input_emits_locale_required_rule():
    """FormKit's own `required` passes on any non-empty object, and this element's value is
    always a `{de, en, fr, it}` object — so a blank one would slip through (issue #135)."""
    element = LocaleInput(label=_label(), required=True)
    assert element.validation == "localeRequired"


def test_optional_locale_input_emits_no_rule():
    assert LocaleInput(label=_label(), required=False).validation == ""


def test_additional_rules_are_appended_after_locale_required():
    element = LocaleInput(label=_label(), required=True, additional_validation_rules="length:3")
    assert element.validation == "localeRequired|length:3"


def test_additional_rules_survive_without_required():
    element = LocaleInput(label=_label(), required=False, additional_validation_rules="length:3")
    assert element.validation == "length:3"


def test_agent_identity_locale_fields_render_as_locale_required():
    """`to_formkit_form()` derives `required` from the annotation, so the identity fields
    pick the rule up without `as_form()` setting anything."""
    validations = {element.name: element.validation for element in AgentConfig.as_form().to_formkit_form()}
    assert validations["name"] == "localeRequired|localeMaxLength:120"
    assert validations["description"] == "localeRequired|localeMaxLength:500"


def test_max_length_emits_locale_max_length_rule_and_prop():
    element = LocaleInput(label=_label(), max_length=120)
    assert element.validation == "localeMaxLength:120"
    assert element.model_dump(by_alias=True)["maxLength"] == 120


def test_process_identity_locale_fields_carry_length_limits():
    validations = {element.name: element.validation for element in ProcessConfig.as_form().to_formkit_form()}
    assert validations["name"] == "localeRequired|localeMaxLength:120"
    assert validations["description"] == "localeRequired|localeMaxLength:500"


def test_validate_value_rejects_any_locale_over_the_limit():
    element = LocaleInput(label=_label(), max_length=5)
    messages = element.validate_value("name", {"de": "kurz", "en": "too long"}, LocaleHandler(locale="en"))
    assert messages == ["must be at most 5 characters per language (en)"]


def test_validate_value_accepts_values_within_the_limit():
    element = LocaleInput(label=_label(), max_length=5)
    assert element.validate_value("name", {"de": "kurz", "en": None}, LocaleHandler(locale="en")) == []


def test_validate_value_ignores_surrounding_whitespace_like_the_frontend_rule():
    element = LocaleInput(label=_label(), max_length=5)
    assert element.validate_value("name", {"en": "  short  "}, LocaleHandler(locale="en")) == []
