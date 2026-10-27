from typing import Any

import pytest
from pydantic import ValidationError
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.agents.release_notes_agent import ReleaseNotesAgent, ReleaseNotesAgentConfig
from swiss_ai_hub.agent.agents.release_notes_agent.release_language import ReleaseLanguage

_FORM = ReleaseNotesAgentConfig.as_form()


def _stored(**fields: Any) -> ReleaseNotesAgentConfig:
    """A profile as the dispatcher builds it: the deployment-fixed values merged with what the admin saved."""
    submitted = {
        "agent_id": "release-notes",
        "name": {"en": "Release notes"},
        "description": {"en": "Writes release notes."},
        "icon": "mage:robot",
        "llm": {"model_name": "text-generation/gemma-4-31B-it"},
        "jira": {
            "base_url": "https://acme.atlassian.net",
            "deployment": "cloud",
            "email": "a@acme.ch",
            "api_token": "t",
        },
        **fields,
    }
    return ReleaseNotesAgentConfig.model_validate(Form.deep_merge(_FORM.get_non_configurable_values(), submitted))


def test_the_blueprint_passes_its_own_workflow_validation():
    ReleaseNotesAgent.validate_workflow(ReleaseNotesAgentConfig)


def test_the_admin_configures_the_connection_projects_and_languages_but_not_the_limits():
    configurable = set(ConfigSpecs.from_form(_FORM, ReleaseNotesAgentConfig.__name__).config_schema["properties"])

    assert {
        "jira",
        "project_keys",
        "extra_jql",
        "language",
        "translate_into",
        "audience",
        "link_tickets",
        "merge_related_tickets",
    } <= (configurable)
    assert not {
        "max_release_tickets",
        "tickets_per_batch",
        "max_concurrent_calls",
        "max_description_chars",
        "max_notes_per_merge",
    } & (configurable)


def test_language_options_are_named_in_their_own_language():
    options = {option["value"]: option["label"] for option in _FORM.language.options}

    assert options == {"de": "Deutsch", "en": "English", "fr": "Français", "it": "Italiano"}
    assert _FORM.translate_into.options == _FORM.language.options


def test_a_stored_profile_gives_its_languages_back_as_members():
    config = _stored(language="de", translate_into=["en", "de", "fr", "en"])

    assert config.writing_language() is ReleaseLanguage.DE
    assert config.translation_targets() == [ReleaseLanguage.EN, ReleaseLanguage.FR]


def test_a_profile_whose_last_project_was_removed_has_none():
    assert _stored(project_keys="").projects() == []
    assert _stored(project_keys=["ENG", "SD"]).projects() == ["ENG", "SD"]


def test_the_release_cap_replaces_the_connection_limit_for_the_read_only():
    config = _stored()

    assert config.capped_jira().max_tickets == 300
    assert config.jira.max_tickets == 1000


def test_a_direct_save_cannot_lift_the_limits_past_their_bounds():
    with pytest.raises(ValidationError, match="max_release_tickets"):
        _stored(max_release_tickets=50_000)


def test_a_profile_without_translations_can_be_saved():
    """The API rejects a blank field the form marks required, and an empty list is blank."""
    elements = {element.name: element for element in _FORM.to_formkit_form()}

    assert not elements["translate_into"].required
    assert elements["translate_into"].nullable
    assert _stored(translate_into=None).translation_targets() == []


def test_related_tickets_are_merged_unless_the_profile_turns_it_off():
    assert _stored().merge_related_tickets is True
    assert _stored(merge_related_tickets=False).merge_related_tickets is False
    assert _stored().max_notes_per_merge == 40


def test_the_translation_switch_and_the_renamed_fields_read_plainly():
    elements = {element.name: element for element in _FORM.to_formkit_form()}

    assert elements["translate_into"].toggle_label is not None
    assert elements["audience"].placeholder is not None
    assert "link_tickets" in elements
    assert "show_ticket_keys" not in elements
    assert _stored(language="de", translate_into=["fr"]).languages() == [ReleaseLanguage.DE, ReleaseLanguage.FR]
