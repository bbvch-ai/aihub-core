"""Guards on the shipped profile templates.

The credential assertions are the reason this file exists. `Form.to_template_data` filters on
`get_configurable_fields()`, which walks top-level fields only, so the entire nested `imap` group — password included —
is serialized into the discovery event and rendered in the Admin UI. A template that ever gained a real host or
password would leak it to every user who can see the Templates tab.
"""

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from app.email_classification_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> EmailClassificationAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    """An empty list renders no Templates group at all, which is the bug this whole file exists to prevent."""
    assert _TEMPLATES


def test_no_mailbox_credentials_are_shipped(template: EmailClassificationAgentConfig):
    assert template.imap.host == ""
    assert template.imap.username == ""
    assert template.imap.password == ""


def test_at_least_three_categories_are_predefined(template: EmailClassificationAgentConfig):
    assert len(template.classification.categories) >= 3


def test_every_category_is_fully_described(template: EmailClassificationAgentConfig):
    """A category with no description gives the model nothing to classify on — folder names alone do not separate."""
    for category in template.classification.categories:
        assert category.category
        assert category.imap_folder
        assert category.description


def test_the_taxonomy_passes_the_agents_own_validation(template: EmailClassificationAgentConfig):
    """A template must never produce a config that the agent rejects at runtime.

    This now also covers the fallback-vs-category and target-vs-inbox rules, which `_validate` enforces for every
    config rather than only for the shipped templates.
    """
    EmailClassificationAgent._validate(template.classification, template.imap.inbox_folder)


def test_name_and_description_are_translated(template: EmailClassificationAgentConfig):
    for field in (template.name, template.description):
        assert isinstance(field, LocaleString)
        for locale in _LOCALES:
            assert getattr(field, locale)


def test_agent_ids_are_unique():
    agent_ids = [template.agent_id for template in _TEMPLATES]
    assert len(set(agent_ids)) == len(agent_ids)
