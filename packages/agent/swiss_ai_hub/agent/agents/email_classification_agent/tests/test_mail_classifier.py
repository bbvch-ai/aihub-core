from types import SimpleNamespace

import pytest
from swiss_ai_hub.core.imap import EmailClassificationSettings, MailCategory

from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import MailClassifier

_SUPPORT = MailCategory(category="support_request", imap_folder="Triage/Support", description="Needs an action.")
_INVOICE = MailCategory(category="invoice", imap_folder="Triage/Invoices", description="A bill.")


def _settings(threshold: float = 0.6, categories: list[MailCategory] | None = None) -> EmailClassificationSettings:
    return EmailClassificationSettings(
        categories=[_SUPPORT, _INVOICE] if categories is None else categories,
        fallback_folder="Triage/Uncategorised",
        confidence_threshold=threshold,
    )


def _selection(selected_index: int | None, confidence: float) -> SimpleNamespace:
    return SimpleNamespace(selected_index=selected_index, confidence=confidence, reason="stated reason")


# --- resolving a model selection into a verdict ---


def test_a_confident_selection_resolves_to_its_category():
    verdict = MailClassifier._resolve(_selection(1, 0.9), _settings())

    assert verdict.category == _INVOICE
    assert verdict.category_name == "invoice"


def test_confidence_exactly_at_the_threshold_is_accepted():
    """The threshold is a floor, not a strict bound — otherwise a 0.6 setting rejects a 0.6 answer."""
    assert MailClassifier._resolve(_selection(0, 0.6), _settings(threshold=0.6)).category == _SUPPORT


def test_confidence_below_the_threshold_falls_back():
    verdict = MailClassifier._resolve(_selection(0, 0.59), _settings(threshold=0.6))

    assert verdict.category is None
    assert verdict.category_name is None


def test_a_declined_selection_falls_back_however_confident():
    """The explicit 'none of these' route exists because self-reported confidence is poorly calibrated —
    a model can be confidently sure that nothing fits."""
    assert MailClassifier._resolve(_selection(None, 1.0), _settings()).category is None


def test_the_reason_survives_a_fallback():
    """A misfile into the fallback folder still has to be explainable in the audit trail."""
    assert MailClassifier._resolve(_selection(0, 0.1), _settings()).reason == "stated reason"


def test_the_response_schema_bounds_the_index_to_the_configured_categories():
    """An index rather than a folder name is what stops an injected instruction naming a folder that does not exist."""
    model = MailClassifier._selection_model(category_count=2)

    assert model(selected_index=1, confidence=0.5, reason="ok").selected_index == 1
    assert model(selected_index=None, confidence=0.5, reason="ok").selected_index is None
    with pytest.raises(ValueError):
        model(selected_index=2, confidence=0.5, reason="ok")
    with pytest.raises(ValueError):
        model(selected_index=-1, confidence=0.5, reason="ok")


# --- config validation, which must fail the run rather than mis-file ---


def test_no_categories_is_rejected():
    with pytest.raises(ValueError, match="no categories are configured"):
        EmailClassificationAgent._validate(_settings(categories=[]))


def test_an_empty_fallback_folder_is_rejected():
    settings = _settings()
    settings.fallback_folder = ""
    with pytest.raises(ValueError, match="fallback_folder is empty"):
        EmailClassificationAgent._validate(settings)


def test_duplicate_category_names_are_rejected():
    duplicate = MailCategory(category="support_request", imap_folder="Other", description="Also support.")
    with pytest.raises(ValueError, match="category names must be unique"):
        EmailClassificationAgent._validate(_settings(categories=[_SUPPORT, duplicate]))


def test_duplicate_category_folders_are_rejected():
    """Two categories filing into one folder makes the run summary unauditable — you cannot tell them apart."""
    duplicate = MailCategory(category="escalation", imap_folder="Triage/Support", description="Escalated support.")
    with pytest.raises(ValueError, match="category folders must be unique"):
        EmailClassificationAgent._validate(_settings(categories=[_SUPPORT, duplicate]))


def test_a_valid_taxonomy_passes():
    EmailClassificationAgent._validate(_settings())
