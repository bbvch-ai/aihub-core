"""Guards on the shipped profile templates.

The connection assertions are the reason this file exists: the whole nested `jira` group, token included, is
serialized into the discovery event and rendered in the Admin UI, so a template with a real URL or token would leak it
to every user who can see the Templates tab.
"""

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from app.release_notes_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.release_notes_agent import ReleaseNotesAgentConfig

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> ReleaseNotesAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    assert _TEMPLATES


def test_no_jira_connection_is_shipped(template: ReleaseNotesAgentConfig):
    assert template.jira.base_url == ""
    assert template.jira.email == ""
    assert template.jira.api_token == ""
    assert template.projects() == []


def test_a_template_survives_the_round_trip_through_a_stored_profile(template: ReleaseNotesAgentConfig):
    stored = ReleaseNotesAgentConfig.model_validate(template.model_dump(mode="json"))

    assert stored.writing_language() == template.writing_language()
    assert stored.translation_targets() == template.translation_targets()
    assert stored.translation_targets(), "a template should show the translation the blueprint offers"


def test_name_and_description_are_translated(template: ReleaseNotesAgentConfig):
    for field in (template.name, template.description):
        assert isinstance(field, LocaleString)
        for locale in _LOCALES:
            assert getattr(field, locale)


def test_agent_ids_are_unique():
    agent_ids = [template.agent_id for template in _TEMPLATES]
    assert len(set(agent_ids)) == len(agent_ids)
