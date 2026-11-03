"""Guards on the shipped Universal Agent profile templates.

A template is published through the blueprint's form, which keeps only the fields that form makes configurable and
offers the blueprint's own tool names as options. A setting outside either would be dropped silently or saved as a
profile the Admin UI cannot edit, so both are checked against the form the runner actually publishes.
"""

import pytest
from swiss_ai_hub.core.i18n import LocaleString

from app.universal_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.universal_agent import UniversalAgent, UniversalAgentConfig
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import SEARCH_KNOWLEDGE_TOOL
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import EXTRACT_RECORDS_TOOL
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop

_LOCALES = ("de", "en", "fr", "it")

_TEMPLATES = get_all_templates()

_PUBLISHED_CONFIG = ToolLoop.published_config(
    UniversalAgentConfig.as_form().for_discovery(is_schedulable=False), UniversalAgent
)


@pytest.fixture(params=_TEMPLATES, ids=lambda template: template.agent_id)
def template(request: pytest.FixtureRequest) -> UniversalAgentConfig:
    return request.param


def test_at_least_one_template_is_shipped():
    """An empty list renders no Templates group at all, leaving the blueprint with a blank form only."""
    assert _TEMPLATES


def test_template_data_validates_against_the_published_form(template: UniversalAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    _PUBLISHED_CONFIG.to_configurable_submission_model().model_validate(template_data)


def test_tool_settings_survive_publishing(template: UniversalAgentConfig):
    """`tool_loop` is configurable only once the runner publishes it, so a plain `as_form()` would drop it."""
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["tool_loop"]["disabled_tools"] == template.tool_loop.disabled_tools
    assert template_data["knowledge_tool"]["every_readable_collection"] == (
        template.knowledge_tool.every_readable_collection
    )


def test_tool_settings_name_only_tools_the_blueprint_offers(template: UniversalAgentConfig):
    tool_names = set(UniversalAgent.tools.names())
    configured = {*template.tool_loop.disabled_tools, *(rule.tool for rule in template.tool_loop.approvals)}

    assert configured <= tool_names, configured - tool_names


def test_every_template_can_search_knowledge(template: UniversalAgentConfig):
    """Searching the organisation's documents is what sets this blueprint apart from a plain chat."""
    assert SEARCH_KNOWLEDGE_TOOL not in template.tool_loop.disabled_tools
    assert template.knowledge_tool.every_readable_collection or template.knowledge_tool.sources


def test_name_and_description_are_translated(template: UniversalAgentConfig):
    for field in (template.name, template.description):
        assert isinstance(field, LocaleString)
        for locale in _LOCALES:
            assert getattr(field, locale)


def test_instructions_are_translated_when_set(template: UniversalAgentConfig):
    if template.instructions is None:
        return
    assert isinstance(template.instructions, LocaleString)
    for locale in _LOCALES:
        assert getattr(template.instructions, locale)


def test_agent_ids_are_unique():
    agent_ids = [template.agent_id for template in _TEMPLATES]
    assert len(set(agent_ids)) == len(agent_ids)


def test_memory_model_is_enabled_on_gemma(template: UniversalAgentConfig):
    """A set `memory_llm` is what switches its toggle on; left unset the form opens it disabled."""
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["user_memory"]["memory_llm"] == "text-generation/gemma-4-31B-it"


def test_kimi_answers_and_gemma_runs_the_task_steps(template: UniversalAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["llm"]["model_name"] == "text-generation/Kimi-K2.6"
    assert template_data["task_llm"]["model_name"] == "text-generation/gemma-4-31B-it"


def test_organization_memory_is_left_for_the_admin_to_enable(template: UniversalAgentConfig):
    template_data = template.to_template_data(_PUBLISHED_CONFIG).model_dump()

    assert template_data["org_memory"] is None


@pytest.mark.parametrize("template", get_all_templates(), ids=lambda template: template.agent_id)
def test_a_template_offering_extraction_never_asks_for_a_confirmation(template: UniversalAgentConfig):
    """API and bot clients cannot answer a confirmation, so the run would stop there; a broad extraction asks the user
    in the conversation instead."""
    if not template.knowledge_documents.enabled:
        pytest.skip("this template does not offer the document tools")
    rules = {rule.tool: rule.policy for rule in template.tool_loop.approvals}

    assert rules[EXTRACT_RECORDS_TOOL] == ToolApprovalPolicy.NEVER


def test_the_workplace_assistant_keeps_the_document_tools_off():
    """The everyday assistant: its users rarely need tables across documents, and fewer tools keep its choice
    reliable."""
    workplace = next(template for template in get_all_templates() if template.agent_id == "workplace-assistant")

    assert workplace.knowledge_documents.enabled is False
