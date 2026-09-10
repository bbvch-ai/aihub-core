"""Guards on the shipped Document Intelligence profile templates.

The retriever assertion is the reason this file exists. A template's vector store is prefilled and an admin may save it
unchanged, and ``create_milvus_vector_store`` creates a missing collection on first retrieval — with 1023 partitions and
no matching ``BucketEntity``. A template naming a collection this deployment does not seed would therefore materialize a
phantom corpus that nothing else in the platform knows about.
"""

import pytest
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings

from app.rag_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.rag_agent import RAGAgentConfig

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()

_SEEDED_COLLECTIONS = {AIHubSettings().DEFAULT_BUCKET_NAME, AIHubSettings().SHARED_BUCKET_NAME}


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> RAGAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    """An empty list renders no Templates group at all, leaving the blueprint with a blank form only."""
    assert _TEMPLATES


def test_every_template_retrieves_from_somewhere(template: RAGAgentConfig):
    """A RAG profile with no retriever answers from the model alone, which is the one thing this blueprint is not."""
    assert template.retrievers


def test_no_template_names_an_unseeded_collection(template: RAGAgentConfig):
    """See the module docstring: an unseeded name is created on first use as a 1023-partition phantom corpus."""
    for retriever in template.retrievers:
        assert retriever.vector_store.collection_name in _SEEDED_COLLECTIONS, retriever.vector_store.collection_name


def test_name_and_description_are_translated(template: RAGAgentConfig):
    for field in (template.name, template.description):
        assert isinstance(field, LocaleString)
        for locale in _LOCALES:
            assert getattr(field, locale)


def test_no_description_points_at_a_blueprint_the_tenant_may_not_have(template: RAGAgentConfig):
    """Only the standard blueprints are granted by default, so naming another one dead-ends the admin."""
    for locale in _LOCALES:
        assert "Shared Knowledge Selector" not in getattr(template.description, locale)


def test_agent_ids_are_unique():
    agent_ids = [template.agent_id for template in _TEMPLATES]
    assert len(set(agent_ids)) == len(agent_ids)


def test_templates_ship_unscheduled(template: RAGAgentConfig):
    """Scheduling is opt-in per profile; a shipped cron would start firing the moment the profile is saved."""
    assert template.cron is None
