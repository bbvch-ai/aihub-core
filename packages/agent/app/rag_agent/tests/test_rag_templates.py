"""Guards on the shipped Document Intelligence profile templates.

The retriever assertion is the reason this file exists. A template's vector store is prefilled and an admin may save it
unchanged, and ``create_milvus_vector_store`` creates a missing collection on first retrieval — with 1023 partitions and
no matching ``BucketEntity``. A template naming a collection this deployment does not seed would therefore materialize a
phantom corpus that nothing else in the platform knows about.

A template also reaches the Admin UI only through the form the runner publishes, and its values override that form's
defaults when it prefills the create dialog, so what a template means to set is checked on the published data.
"""

import pytest
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings

from app.rag_agent.templates import get_all_templates
from app.rag_agent.templates.jira_story_assistant import build as build_jira_story_assistant
from swiss_ai_hub.agent.agents.rag_agent import RAGAgent, RAGAgentConfig

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()

_SEEDED_COLLECTIONS = {AIHubSettings().DEFAULT_BUCKET_NAME, AIHubSettings().SHARED_BUCKET_NAME}


def _published_config() -> RAGAgentConfig:
    """The form `AgentRunner` announces for the blueprint, built the same way."""
    config = RAGAgentConfig.as_form().for_discovery(is_schedulable=False)
    for capability in RAGAgent.installed_capabilities():
        config = capability.published_config(config, RAGAgent)
    return config


_PUBLISHED_CONFIG = _published_config()


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


def test_template_data_validates_against_the_published_form(template: RAGAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    _PUBLISHED_CONFIG.to_configurable_submission_model().model_validate(template_data)


def test_story_assistant_settings_survive_publishing():
    """Access, memory and query mode differ from the class defaults, which would win over the form's own values if
    the template left them unset. The guard and condensing match the defaults but are pinned because drafting depends
    on them: a rejecting guard withholds every document a draft is grounded on."""
    template_data = build_jira_story_assistant().to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["restrict_to_user_access"] is True
    assert template_data["condense_question"] is True
    assert template_data["context_sufficient_guard"]["check_context_sufficiency"] is False
    assert template_data["user_memory"]["enable_user_memory_retrieval"] is False
    assert template_data["user_memory"]["enable_user_memory_storage"] is False
    assert template_data["org_memory"] is None
    assert [retriever["query_mode"] for retriever in template_data["retrievers"]] == [VectorStoreQueryMode.HYBRID]


def test_story_assistant_prompt_keeps_the_blocks_the_setup_guide_names():
    """The setup guide tells admins to add their templates and switch the markup in these blocks."""
    prompt = build_jira_story_assistant().system_prompt.en

    assert '<template project="default">' in prompt
    assert "</story_templates>" in prompt
    assert "<output_markup>" in prompt


def test_story_assistant_context_prompt_still_renders_the_documents():
    """The template replaces the blueprint's context prompt; without the loop the retrieved documents never reach the
    model, and without the chat block the prompt is not one message."""
    context_prompt = build_jira_story_assistant().context_prompt.en

    assert context_prompt.startswith('{% chat role="user" %}')
    assert "{% for block in context_blocks %}" in context_prompt
    assert context_prompt.rstrip().endswith("{% endchat %}")
