"""Profiles are loaded the way the dispatcher loads them: what the Admin UI stored, which holds only the form's inputs,
merged over the form's non-configurable values, so the profile stays the hard boundary without being re-saved."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from swiss_ai_hub.core.events.agent import KnowledgeReference
from swiss_ai_hub.core.form import Form, transform_formkit_arrays
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import KnowledgeDocumentTools
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import RecordSelectionTools

_FORM = KnowledgeExtractionAgentConfig.as_form()
_FINANCE_SOURCE = {
    "vector_store": {"collection_name": "finance", "index_namespaces": ["invoices"], "all_namespaces": False}
}
_DISCOVERING = {"path_glob": None, "discovery": True}


def _stored(knowledge_documents: dict[str, Any] | None = None) -> dict[str, Any]:
    """What the Admin UI saves for a profile: the form's inputs a profile needs, and nothing the form fixes."""
    stored: dict[str, Any] = {
        "agent_id": "invoice-tables",
        "name": {"en": "Invoice tables"},
        "description": {"en": "Tables from the finance invoices."},
        "icon": "mdi:table-search",
        "instructions": None,
        "llm": {"model_name": "text-generation/dummy"},
        "knowledge_tool": {"sources": [_FINANCE_SOURCE]},
        "record_extraction": {"extraction_model_name": "text-generation/dummy"},
    }
    if knowledge_documents is not None:
        stored["knowledge_documents"] = knowledge_documents
    return stored


def _loaded(stored: dict[str, Any]) -> KnowledgeExtractionAgentConfig:
    """Mirrors `AgentDispatcher.handle_event` and `_resolve_agent_config_dict`: merge over the form's fixed values,
    turn FormKit arrays into lists, validate."""
    merged = Form.deep_merge(_FORM.get_non_configurable_values(), stored)
    return KnowledgeExtractionAgentConfig.model_validate(transform_formkit_arrays(merged))


@pytest.mark.parametrize(
    "knowledge_documents",
    [_DISCOVERING, {"path_glob": "invoices/**", "discovery": False}, None],
    ids=["discovery-without-glob", "glob-without-discovery", "never-saved"],
)
def test_a_profile_saved_through_the_admin_ui_keeps_the_document_tools_on_and_narrowing(
    knowledge_documents: dict[str, Any] | None,
):
    config = _loaded(_stored(knowledge_documents))

    assert config.knowledge_documents.enabled is True
    assert config.knowledge_documents.narrow_references is True
    assert config.knowledge_tool.every_readable_collection is False
    saved = knowledge_documents or {"path_glob": None, "discovery": False}
    assert config.knowledge_documents.path_glob == saved["path_glob"]
    assert config.knowledge_documents.discovery is saved["discovery"]


def test_a_direct_save_cannot_switch_the_boundary_off():
    stored = _stored({"enabled": False, "narrow_references": False, "discovery": True})
    stored["knowledge_tool"] = {"every_readable_collection": True, "sources": [_FINANCE_SOURCE]}

    config = _loaded(stored)

    assert config.knowledge_documents.enabled is True
    assert config.knowledge_documents.narrow_references is True
    assert config.knowledge_tool.every_readable_collection is False


def test_a_profile_saved_with_discovery_offers_the_document_tools_and_the_selection():
    context = MagicMock(agent_config=_loaded(_stored(_DISCOVERING)))

    assert KnowledgeDocumentTools(context).spec_functions == [
        "list_knowledge_documents",
        "search_knowledge_content",
        "read_knowledge_document",
        "rank_knowledge_documents",
    ]
    assert RecordSelectionTools(context).spec_functions == ["select_knowledge_documents"]


@pytest.mark.parametrize(
    ("reference", "expected", "ignored"),
    [
        (KnowledgeReference(database="hr", namespace="policies"), ["finance/invoices"], True),
        (KnowledgeReference(database="finance", namespace="invoices"), ["finance/invoices"], False),
    ],
    ids=["outside-the-profile", "inside-the-profile"],
)
def test_a_reference_only_narrows_among_a_saved_profiles_collections(
    reference: KnowledgeReference, expected: list[str], ignored: bool
):
    stored = _stored(_DISCOVERING)
    stored["knowledge_tool"] = {"sources": {"0": _FINANCE_SOURCE}}
    live = {"finance": ["invoices"], "hr": ["policies"]}
    with (
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope.UserScopedRetrievers.namespaces_of",
            side_effect=lambda database: live.get(database, []),
        ),
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope.KnowledgeCollectionResolver.pair_of",
            side_effect=lambda ref: BucketNamespacePair(bucket_name=ref.database, namespace_name=ref.namespace),
        ),
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope.KnowledgeCollectionLabel.of_reference",
            return_value="label",
        ),
    ):
        scope = KnowledgeDocumentScope.of(_loaded(stored), [reference], None, "en")

    assert [entry.identifier for entry in scope.collections] == expected
    assert scope.ignored == ([reference] if ignored else [])


def test_the_callers_document_settings_stay_unchanged():
    documents = KnowledgeDocumentConfig(enabled=False)

    config = KnowledgeExtractionAgentConfig(
        agent_id="extraction-test",
        name=LocaleString(en="Extraction"),
        description=LocaleString(en="Extraction fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        knowledge_documents=documents,
    )

    assert config.knowledge_documents.enabled is True
    assert documents.enabled is False


def test_other_blueprints_keep_the_document_tools_off_by_default():
    assert KnowledgeDocumentConfig().enabled is False
    assert KnowledgeDocumentConfig().narrow_references is False
    assert KnowledgeDocumentConfig.model_validate({"path_glob": None}).enabled is False
