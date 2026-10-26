"""Guards on the shipped Web Page Assistant profile templates.

A template is published through the blueprint's form, which keeps only the fields that form makes configurable, so
each one is checked against the form the runner actually publishes.
"""

import pytest

from app.web_fetch_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.web_fetch_agent import WebFetchAgentConfig
from swiss_ai_hub.agent.capabilities.web_fetch.web_fetch_config import WebFetchConfig

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()

_PUBLISHED_CONFIG = WebFetchAgentConfig.as_form().for_discovery(is_schedulable=False)


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> WebFetchAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    """An empty list renders no Templates group at all, leaving the blueprint with a blank form only."""
    assert _TEMPLATES


def test_agent_ids_are_unique():
    agent_ids = [template.agent_id for template in _TEMPLATES]
    assert len(set(agent_ids)) == len(agent_ids)


@pytest.mark.parametrize("locale", _LOCALES)
def test_name_description_and_prompt_are_translated(template: WebFetchAgentConfig, locale: str):
    assert getattr(template.name, locale)
    assert getattr(template.description, locale)
    assert getattr(template.system_prompt, locale)


def test_template_data_validates_against_the_published_form(template: WebFetchAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    _PUBLISHED_CONFIG.to_configurable_submission_model().model_validate(template_data)


def test_templates_read_links_with_the_default_limits(template: WebFetchAgentConfig):
    assert template.web_fetch == WebFetchConfig()


def test_templates_ship_unscheduled(template: WebFetchAgentConfig):
    """Scheduling is opt-in per profile; a shipped cron would start firing the moment the profile is saved."""
    assert template.cron is None
