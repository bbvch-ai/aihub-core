import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

LOCALE_STRING_DEF = {
    "type": "object",
    "properties": {
        "de": {"type": "string"},
        "en": {"type": "string"},
        "fr": {"type": "string"},
        "it": {"type": "string"},
    },
}


def _schema(required: list[str]) -> dict:
    """A config schema with localized name/description/system_prompt and a plain agent_id."""
    return {
        "$defs": {"LocaleString": LOCALE_STRING_DEF},
        "properties": {
            "agent_id": {"type": "string"},
            "name": {"$ref": "#/$defs/LocaleString"},
            "description": {"$ref": "#/$defs/LocaleString"},
            "system_prompt": {"$ref": "#/$defs/LocaleString"},
        },
        "required": required,
    }


def test_localized_field_names_detects_ref_allof_and_anyof():
    schema = {
        "$defs": {"LocaleString": LOCALE_STRING_DEF},
        "properties": {
            "agent_id": {"type": "string"},
            "name": {"$ref": "#/$defs/LocaleString"},
            "description": {"allOf": [{"$ref": "#/$defs/LocaleString"}]},
            "system_prompt": {"anyOf": [{"$ref": "#/$defs/LocaleString"}, {"type": "null"}]},
        },
    }
    assert InstanceConfigHelper._localized_field_names(schema) == {"name", "description", "system_prompt"}


def test_validate_required_locale_fields_rejects_every_empty_required_field():
    config = {"agent_id": "x", "name": None, "description": None, "system_prompt": None}
    with pytest.raises(HTTPException) as exc:
        InstanceConfigHelper.validate_required_locale_fields(
            config, _schema(["agent_id", "name", "description", "system_prompt"])
        )
    assert exc.value.status_code == 400
    assert "description, name, system_prompt" in exc.value.detail


def test_validate_required_locale_fields_passes_when_all_required_have_content():
    config = {"agent_id": "x", "name": {"en": "Hi"}, "description": {"de": "Bot"}, "system_prompt": {"en": "sys"}}
    InstanceConfigHelper.validate_required_locale_fields(
        config, _schema(["agent_id", "name", "description", "system_prompt"])
    )


def test_validate_required_locale_fields_ignores_optional_localized_field():
    config = {"agent_id": "x", "name": {"en": "Hi"}, "description": {"en": "Bot"}, "system_prompt": None}
    InstanceConfigHelper.validate_required_locale_fields(config, _schema(["name", "description"]))


def test_validate_required_locale_fields_ignores_non_localized_required_field():
    config = {"agent_id": None, "name": {"en": "Hi"}, "description": {"en": "Bot"}}
    InstanceConfigHelper.validate_required_locale_fields(config, _schema(["agent_id", "name", "description"]))


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ({}, False),
        ({"de": "", "en": "", "fr": "", "it": ""}, False),
        ({"en": "Hello"}, True),
        (LocaleString(), False),
        (LocaleString(fr="Bonjour"), True),
    ],
)
def test_locale_value_has_content(value, expected):
    assert InstanceConfigHelper._locale_value_has_content(value) is expected


def test_build_locale_entities_stores_empty_entity_for_missing_description():
    entities = InstanceConfigHelper.build_locale_entities(None, None, "RAGAgent", "mage:robot")
    assert entities.description.to_locale_string().has_content() is False
    assert entities.description.de is None and entities.description.en is None
    # Name still falls back to a populated default so it never persists blank.
    assert entities.name.to_locale_string().has_content() is True


def test_build_locale_entities_uses_provided_description():
    entities = InstanceConfigHelper.build_locale_entities(
        LocaleString(en="Name"), LocaleString(en="Desc"), "RAGAgent", "mage:robot"
    )
    assert entities.description.en == "Desc"
