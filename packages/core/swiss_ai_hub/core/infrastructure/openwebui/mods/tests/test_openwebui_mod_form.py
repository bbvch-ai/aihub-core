import pytest

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_form import OpenWebuiModForm
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest

pytestmark = pytest.mark.unit


def test_inference_preserves_types_and_uses_existing_controls():
    elements = OpenWebuiModForm.build({
        "enabled": False, "count": 0, "ratio": 0.25, "text": "", "optional": None,
        "translations": {"en": "Hello", "de": None}, "tags": ["one"],
        "nested": {"count": 2}, "rows": [{"name": "First", "enabled": True}],
    }, {})
    controls = {element.name: element.formkit for element in elements}
    assert controls == {
        "enabled": "primeToggleSwitch", "count": "primeInputNumber", "ratio": "primeInputNumber",
        "text": "primeInputText", "optional": "primeInputText", "translations": "localeInput",
        "tags": "chipsInput", "nested": "group", "rows": "repeater",
    }
    assert elements[0].value is False
    assert elements[1].value == 0
    assert elements[4].nullable
    assert elements[-1].children[0].value == "First"


def test_explicit_hints_use_existing_localized_controls_and_validation():
    elements = OpenWebuiModForm.build({"note": "", "level": "low", "text": {"en": "Hello"}}, {
        "note": {"control": "primeTextarea", "rows": 5, "required": True, "label": {"de": "Notiz", "en": "Note"}},
        "level": {"options": ["low", "high"]},
        "text": {"maxLength": 100},
    })
    assert elements[0].formkit == "primeTextarea"
    assert elements[0].label.de == "Notiz"
    assert elements[0].rows == 5
    assert "required" in elements[0].validation
    assert elements[1].formkit == "primeSelect"
    assert "localeMaxLength:100" in elements[2].validation


def test_nested_hints_do_not_need_duplicate_defaults():
    form = OpenWebuiModForm.build({"section": {"note": "Keep this", "count": 3}}, {
        "section": {"children": [{"name": "note", "control": "primeTextarea", "rows": 4}]},
    })
    assert form[0].children[0].formkit == "primeTextarea"
    assert form[0].children[0].value == "Keep this"
    assert form[0].children[1].formkit == "primeInputNumber"


@pytest.mark.parametrize("hints", [
    {"control": "primePassword"}, {"control": "secretFileInput"}, {"control": "modelSelect"},
    {"control": "tenantSelect"}, {"control": "knowledgeDatabaseSelector"},
    {"control": "primeSelect", "optionsApiMode": "chat"},
    {"control": []}, {"control": {}}, {"control": None}, {"control": ""},
    {"control": "arbitraryWidget"}, {"$el": "script"}, {"attrs": {"onclick": "alert(1)"}},
    {"name": "other"}, {"value": "different"}, {"maxLenght": 20},
])
def test_unsupported_services_secrets_or_schema_properties_are_rejected(hints):
    with pytest.raises(ValueError):
        OpenWebuiModForm.build({"field": "value"}, {"field": hints})


def test_unrepresentable_legacy_values_are_not_coerced_into_text_inputs():
    assert OpenWebuiModForm.build({"mixed": [1, "two"], "key.with.dots": "keep"}, {}) == []


def test_manifest_validates_hints_without_executing_mod_code():
    manifest = OpenWebuiModManifest.model_validate({
        "format": 1, "id": "test", "name": "Test", "version": "1", "frontend": "main.js",
        "default_settings": {"text": {"en": "Hello"}}, "settings_fields": {"text": {"maxLength": 100}},
    })
    assert manifest.settings_form()[0]["maxLength"] == 100
    # Derived presentation is not persisted in the source manifest or runtime settings.
    assert "settings_form" not in manifest.model_dump()
    assert OpenWebuiModManifest.model_validate_json(manifest.model_dump_json()) == manifest


@pytest.mark.parametrize("control", [
    "primeInputText", "primeTextarea", "primeInputNumber", "primeCheckbox", "primeToggleSwitch",
    "primeToggleButton", "primeSlider", "primeKnob", "primeRating", "primeColorPicker", "primeDatePicker",
    "primeInputMask", "primeInputOtp", "chipsInput", "cronInput", "iconSelector", "localeInput",
    "primeSelect", "primeMultiSelect", "primeListbox", "primeRadioButton", "primeSelectButton", "primeCascadeSelect",
])
def test_self_contained_platform_controls_accept_their_existing_definitions(control):
    hints = {"control": control}
    if control in {"primeSelect", "primeMultiSelect", "primeListbox", "primeRadioButton", "primeSelectButton", "primeCascadeSelect"}:
        hints.update(options=[{"label": "One", "value": "one"}], optionLabel="label", optionValue="value")
    assert OpenWebuiModForm.build({}, {"field": hints})[0].formkit == control


def test_required_field_without_a_default_is_visible_not_implicitly_nullable():
    element = OpenWebuiModForm.build({}, {"note": {"required": True}})[0]
    assert element.required
    assert not element.nullable


def test_explicit_nullable_group_preserves_a_null_default():
    element = OpenWebuiModForm.build({"group": None}, {"group": {"control": "group", "children": []}})[0]
    assert element.nullable


def test_nested_repeaters_are_not_inferred_and_explicit_requests_are_rejected():
    defaults = {"rows": [{"label": "First", "nested_rows": [{"label": "Nested"}]}]}
    form = OpenWebuiModForm.build(defaults, {})
    assert [child.name for child in form[0].children] == ["label"]
    with pytest.raises(ValueError, match="inside repeater rows"):
        OpenWebuiModForm.build(defaults, {"rows": {"children": [{"name": "nested_rows", "control": "repeater"}]}})


@pytest.mark.parametrize(("hints", "detail"), [
    ({"control": "primeTextare"}, "unknown control 'primeTextare'"),
    ({"control": "primeTextarea", "rows": "many"}, "rows:"),
    ({"control": "primeSelect", "options": "invalid"}, "options."),
])
def test_validation_errors_identify_the_setting_without_listing_internal_types(hints, detail):
    with pytest.raises(ValueError) as caught:
        OpenWebuiModForm.build({"message": ""}, {"message": hints})
    message = str(caught.value)
    assert message.startswith("Field 'message':")
    assert detail in message
    assert "tagged-union" not in message
    assert len(message) < 200
