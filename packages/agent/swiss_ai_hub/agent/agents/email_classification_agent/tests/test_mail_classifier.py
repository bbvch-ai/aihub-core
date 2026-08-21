from types import SimpleNamespace

import pytest
from swiss_ai_hub.core.imap import EmailClassificationSettings, MailCategory

from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import MailClassifier

_SUPPORT = MailCategory(category="support_request", imap_folder="Triage/Support", description="Needs an action.")
_INVOICE = MailCategory(category="invoice", imap_folder="Triage/Invoices", description="A bill.")


def _settings(categories: list[MailCategory] | None = None) -> EmailClassificationSettings:
    return EmailClassificationSettings(
        categories=[_SUPPORT, _INVOICE] if categories is None else categories,
        fallback_folder="Triage/Uncategorised",
    )


def _selection(selected_index: int | None) -> SimpleNamespace:
    return SimpleNamespace(selected_index=selected_index, reason="stated reason")


# --- resolving a model selection into a verdict ---


def test_a_selection_resolves_to_its_category():
    verdict = MailClassifier._resolve(_selection(1), _settings())

    assert verdict.category == _INVOICE
    assert verdict.category_name == "invoice"


def test_a_declined_selection_falls_back():
    """Declining is the only route to the fallback folder — there is no score to second-guess it with."""
    verdict = MailClassifier._resolve(_selection(None), _settings())

    assert verdict.category is None
    assert verdict.category_name is None


def test_the_reason_survives_a_fallback():
    """A message dropped into the fallback folder still has to be explainable in the audit trail."""
    assert MailClassifier._resolve(_selection(None), _settings()).reason == "stated reason"


def test_the_response_schema_bounds_the_index_to_the_configured_categories():
    """An index rather than a folder name is what stops an injected instruction naming a folder that does not exist."""
    model = MailClassifier._selection_model(category_count=2)

    assert model(selected_index=1, reason="ok").selected_index == 1
    assert model(selected_index=None, reason="ok").selected_index is None
    with pytest.raises(ValueError):
        model(selected_index=2, reason="ok")
    with pytest.raises(ValueError):
        model(selected_index=-1, reason="ok")


# --- config validation, which must fail the run rather than mis-file ---


def test_no_categories_is_rejected():
    settings = _settings(categories=[])
    with pytest.raises(ValueError, match="no categories are configured"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_an_empty_fallback_folder_is_rejected():
    settings = _settings()
    settings.fallback_folder = ""
    with pytest.raises(ValueError, match="fallback_folder is empty"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_duplicate_category_names_are_rejected():
    duplicate = MailCategory(category="support_request", imap_folder="Other", description="Also support.")
    settings = _settings(categories=[_SUPPORT, duplicate])
    with pytest.raises(ValueError, match="category names must be unique"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_duplicate_category_folders_are_rejected():
    """Two categories filing into one folder makes the run summary unauditable — you cannot tell them apart."""
    duplicate = MailCategory(category="escalation", imap_folder="Triage/Support", description="Escalated support.")
    settings = _settings(categories=[_SUPPORT, duplicate])
    with pytest.raises(ValueError, match="category folders must be unique"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_a_valid_taxonomy_passes():
    EmailClassificationAgent._validate(_settings(), "INBOX")


def test_a_category_folder_equal_to_the_inbox_is_rejected():
    """Filing out of the inbox is the only dedup there is.

    A target equal to the inbox defeats it outright: on the COPY + UID EXPUNGE path the original is replaced by a
    fresh unread copy in the same folder, so the next run picks the copy up, archives it again, and never terminates.
    """
    into_inbox = MailCategory(category="everything", imap_folder="INBOX", description="Straight back where it came.")
    settings = _settings(categories=[into_inbox])
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_a_fallback_folder_equal_to_the_inbox_is_rejected():
    settings = _settings()
    settings.fallback_folder = "INBOX"
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, "INBOX")


def test_the_inbox_check_uses_the_configured_folder_not_a_hardcoded_name():
    """A mailbox reading from something other than INBOX must be protected just the same."""
    settings = _settings()
    settings.fallback_folder = "Shared/Support"
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, "Shared/Support")


def test_a_fallback_folder_that_is_also_a_category_folder_is_rejected():
    """Sharing the folder makes per_category and fallback_count indistinguishable in the run summary."""
    settings = _settings()
    settings.fallback_folder = _SUPPORT.imap_folder
    with pytest.raises(ValueError, match="is also a category folder"):
        EmailClassificationAgent._validate(settings, "INBOX")
