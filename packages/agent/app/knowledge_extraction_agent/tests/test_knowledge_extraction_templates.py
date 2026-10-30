"""Guards on the shipped Knowledge Extraction Agent profile templates, checked against the form the runner publishes,
since a setting outside it would be dropped silently or saved as a profile the Admin UI cannot edit."""

import pytest

from app.knowledge_extraction_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.knowledge_extraction_agent import (
    KnowledgeExtractionAgent,
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop

_TEMPLATES = get_all_templates()

_PUBLISHED_CONFIG = ToolLoop.published_config(
    KnowledgeExtractionAgentConfig.as_form().for_discovery(is_schedulable=False), KnowledgeExtractionAgent
)


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> KnowledgeExtractionAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    assert _TEMPLATES


def test_template_data_validates_against_the_published_form(template: KnowledgeExtractionAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    _PUBLISHED_CONFIG.to_configurable_submission_model().model_validate(template_data)


def test_the_extraction_settings_survive_publishing(template: KnowledgeExtractionAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["record_extraction"]["extraction_model_name"] == (
        template.record_extraction.extraction_model_name
    )
    assert template_data["tool_loop"]["max_tool_calls"] == template.tool_loop.max_tool_calls


def test_the_document_tools_stay_on_and_narrowing_whatever_a_template_says(template: KnowledgeExtractionAgentConfig):
    """Both are fixed by the blueprint's form, so a profile can never switch them off."""
    published = _PUBLISHED_CONFIG.knowledge_documents

    assert (published.enabled, published.narrow_references) == (True, True)
