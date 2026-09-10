from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.i18n.locale_string import LocaleString


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
    assert validations["name"] == "localeRequired"
    assert validations["description"] == "localeRequired"
