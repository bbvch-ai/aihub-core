from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.imap import DraftEmailSettings, EmailClassificationSettings, MailCategory

from swiss_ai_hub.agent.agents.email_classification_agent.configs.knowledge_delegation_config import (
    KnowledgeDelegationConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import (
    ClassificationOutcome,
    MailClassifier,
)
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.token_budget import MAX_SUBJECT_CHARACTERS

_SUPPORT = MailCategory(category="support_request", imap_folder="Triage/Support", description="Needs an action.")
_INVOICE = MailCategory(category="invoice", imap_folder="Triage/Invoices", description="A bill.")


def _settings(categories: list[MailCategory] | None = None) -> EmailClassificationSettings:
    return EmailClassificationSettings(
        categories=[_SUPPORT, _INVOICE] if categories is None else categories,
        fallback_folder="Triage/Uncategorised",
    )


def _no_drafting() -> DraftEmailSettings:
    """Drafting off — the taxonomy checks below are about classification and must not depend on draft settings."""
    return DraftEmailSettings(enable_draft=False)


def _drafting(drafts_folder: str = "Drafts") -> DraftEmailSettings:
    return DraftEmailSettings(enable_draft=True, drafts_folder=drafts_folder)


def _counter(text: str) -> list[int]:
    """One token per four characters — enough to exercise the budget without a real tokenizer."""
    return [0] * (len(text) // 4 + 1)


def _parsed(body: str = "The delivery never arrived.", subject: str = "Missing delivery") -> ParsedMessage:
    return ParsedMessage(
        message_id="1",
        sender="alice@test",
        subject=subject,
        date=datetime(2026, 8, 25, 9, 0, tzinfo=UTC),
        body_text=body,
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
    draft = _no_drafting()
    with pytest.raises(ValueError, match="no categories are configured"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_an_empty_fallback_folder_is_rejected():
    settings = _settings()
    settings.fallback_folder = ""
    draft = _no_drafting()
    with pytest.raises(ValueError, match="fallback_folder is empty"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_duplicate_category_names_are_rejected():
    duplicate = MailCategory(category="support_request", imap_folder="Other", description="Also support.")
    settings = _settings(categories=[_SUPPORT, duplicate])
    draft = _no_drafting()
    with pytest.raises(ValueError, match="category names must be unique"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_duplicate_category_folders_are_rejected():
    """Two categories filing into one folder makes the run summary unauditable — you cannot tell them apart."""
    duplicate = MailCategory(category="escalation", imap_folder="Triage/Support", description="Escalated support.")
    settings = _settings(categories=[_SUPPORT, duplicate])
    draft = _no_drafting()
    with pytest.raises(ValueError, match="category folders must be unique"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_valid_taxonomy_passes():
    EmailClassificationAgent._validate(_settings(), _no_drafting(), "INBOX", _counter)


def test_a_category_folder_equal_to_the_inbox_is_rejected():
    """Filing out of the inbox is the only dedup there is.

    A target equal to the inbox defeats it outright: on the COPY + UID EXPUNGE path the original is replaced by a
    fresh unread copy in the same folder, so the next run picks the copy up, archives it again, and never terminates.
    """
    into_inbox = MailCategory(category="everything", imap_folder="INBOX", description="Straight back where it came.")
    settings = _settings(categories=[into_inbox])
    draft = _no_drafting()
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_fallback_folder_equal_to_the_inbox_is_rejected():
    settings = _settings()
    settings.fallback_folder = "INBOX"
    draft = _no_drafting()
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_the_inbox_check_uses_the_configured_folder_not_a_hardcoded_name():
    """A mailbox reading from something other than INBOX must be protected just the same."""
    settings = _settings()
    settings.fallback_folder = "Shared/Support"
    draft = _no_drafting()
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, draft, "Shared/Support", _counter)


def test_a_fallback_folder_that_is_also_a_category_folder_is_rejected():
    """Sharing the folder makes per_category and fallback_count indistinguishable in the run summary."""
    settings = _settings()
    settings.fallback_folder = _SUPPORT.imap_folder
    draft = _no_drafting()
    with pytest.raises(ValueError, match="is also a category folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


# --- drafting configuration, validated before the run spends anything ---


def test_drafting_enabled_with_no_opted_in_category_is_rejected():
    """Paying for a drafting pass that cannot produce a single draft is a misconfiguration, not a quiet no-op."""
    settings = _settings()
    draft = _drafting()
    with pytest.raises(ValueError, match="no category is set to get a drafted reply"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_drafts_folder_equal_to_the_inbox_is_rejected():
    """A draft appended into the inbox arrives unread, so the next run classifies and replies to the agent's own
    draft — the same unterminating loop an inbox-equal category folder would cause."""
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True})])
    draft = _drafting(drafts_folder="INBOX")
    with pytest.raises(ValueError, match="drafts_folder equals the inbox folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_drafts_folder_that_is_also_a_category_folder_is_rejected():
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True})])
    draft = _drafting(drafts_folder=_SUPPORT.imap_folder)
    with pytest.raises(ValueError, match="is also a category or fallback folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_valid_drafting_configuration_passes():
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True}), _INVOICE])
    EmailClassificationAgent._validate(settings, _drafting(), "INBOX", _counter)


def test_drafting_configuration_is_not_checked_when_drafting_is_off():
    """An admin who never turned drafting on must not be blocked by its defaults."""
    off = DraftEmailSettings(enable_draft=False, drafts_folder="INBOX")
    EmailClassificationAgent._validate(_settings(), off, "INBOX", _counter)


# --- a message that cannot be classified must not cost the batch, or the mailbox ---


@pytest.mark.asyncio
async def test_a_classifier_call_that_raises_costs_only_that_message():
    """Blocking the whole mailbox on one bad message would be a far worse trade than filing it for review.

    Filing is the only dedup this agent has, so a raise here leaves the message unread in the inbox where the next
    run selects it again — forever, with every healthy message queued behind it.
    """
    llm = SimpleNamespace(astructured_predict=AsyncMock(side_effect=RuntimeError("the gateway refused the request")))

    verdict = await MailClassifier.classify(_parsed(), _settings(), llm, _counter)

    assert verdict.outcome is ClassificationOutcome.FAILED
    assert verdict.category is None


@pytest.mark.asyncio
async def test_a_failed_verdict_never_carries_the_exception_text():
    """`reason` is persisted to the audit trail and streamed to the frontend, and an exception can quote the very
    message that broke it — untrusted content."""
    llm = SimpleNamespace(astructured_predict=AsyncMock(side_effect=RuntimeError("secret from the mail body")))

    verdict = await MailClassifier.classify(_parsed(), _settings(), llm, _counter)

    assert "secret from the mail body" not in verdict.reason


def test_a_decline_is_not_a_failure():
    """The regression guard for the whole design: collapsing these two would file mail the model never read into the
    folder reserved for mail it deliberately declined."""
    assert MailClassifier._resolve(_selection(None), _settings()).outcome is ClassificationOutcome.DECLINED
    assert MailClassifier._failed().outcome is ClassificationOutcome.FAILED


def test_a_failed_verdict_routes_to_the_failure_folder_not_the_fallback_folder():
    settings = _settings()

    assert MailClassifier._failed().target_folder(settings) == settings.failure_folder
    assert MailClassifier._resolve(_selection(None), settings).target_folder(settings) == settings.fallback_folder


# --- the classification prompt is bounded, like the drafting prompt ---


@pytest.mark.asyncio
async def test_an_oversized_body_is_trimmed_rather_than_sent_whole():
    """`max_body_bytes` bounds the body in bytes — a megabyte, some 250k tokens — which is far past any context
    window. Without a token budget the model call fails, and a message that always fails never leaves the inbox."""
    predict = AsyncMock(return_value=_selection(0))
    llm = SimpleNamespace(astructured_predict=predict)
    huge = "The reconciliation job stalled again and the operator restarted it. " * 5_000

    await MailClassifier.classify(_parsed(body=huge), _settings(), llm, _counter)

    sent = predict.await_args.kwargs["body"]
    assert len(sent) < len(huge)
    assert sent.startswith("The reconciliation job stalled again")


@pytest.mark.asyncio
async def test_an_enormous_subject_is_capped_before_it_reaches_the_prompt():
    """The subject sits in the part of the prompt no trimming reaches, and it is attacker-controlled."""
    predict = AsyncMock(return_value=_selection(0))
    llm = SimpleNamespace(astructured_predict=predict)

    await MailClassifier.classify(_parsed(subject="A" * 200_000), _settings(), llm, _counter)

    assert len(predict.await_args.kwargs["subject"]) == MAX_SUBJECT_CHARACTERS


# --- the failure folder joins the collision checks, and must never be the inbox ---


def test_an_empty_failure_folder_is_rejected():
    settings = _settings()
    settings.failure_folder = ""
    draft = _no_drafting()
    with pytest.raises(ValueError, match="failure_folder is empty"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_failure_folder_equal_to_the_fallback_folder_is_rejected():
    """An operator could not tell mail the model declined from mail it never read — which is the whole reason the two
    folders are separate."""
    settings = _settings()
    settings.failure_folder = settings.fallback_folder
    draft = _no_drafting()
    with pytest.raises(ValueError, match="equals the fallback folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_failure_folder_that_is_also_a_category_folder_is_rejected():
    settings = _settings()
    settings.failure_folder = _SUPPORT.imap_folder
    draft = _no_drafting()
    with pytest.raises(ValueError, match="is also a category folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_failure_folder_equal_to_the_inbox_is_rejected():
    """The poison loop this whole change exists to kill, reinstated by a typo: mail that failed would be filed back
    into the inbox and re-selected on every run."""
    settings = _settings()
    settings.failure_folder = "INBOX"
    draft = _no_drafting()
    with pytest.raises(ValueError, match="equals the inbox folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_drafts_folder_equal_to_the_failure_folder_is_rejected():
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True})])
    draft = _drafting(drafts_folder=settings.failure_folder)
    with pytest.raises(ValueError, match="is also a category or fallback folder"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


# --- a budget that cannot work is rejected before the run spends anything ---


def test_a_drafting_budget_too_small_for_its_own_prompt_is_rejected_up_front():
    """Discovered at drafting time it would be worthless: the batch is classified and filed by then, so the drafts
    are unrecoverable and the model spend is already gone."""
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True})])
    draft = _drafting()
    draft.number_of_input_tokens = 1
    with pytest.raises(ValueError, match="system prompt alone exhausts"):
        EmailClassificationAgent._validate(settings, draft, "INBOX", _counter)


def test_a_workable_budget_passes_validation():
    settings = _settings(categories=[_SUPPORT.model_copy(update={"draft_reply": True})])

    EmailClassificationAgent._validate(settings, _drafting(), "INBOX", _counter)


# --- grounding validation ---


def _grounded(namespace: str = "support") -> MailCategory:
    return _SUPPORT.model_copy(update={"draft_reply": True, "knowledge_namespace": namespace})


def _delegation() -> KnowledgeDelegationConfig:
    return KnowledgeDelegationConfig(rag_agent=AgentRef(agent_class="RAGAgent", agent_id="rag-support"))


def _grounded_settings() -> EmailClassificationSettings:
    settings = _settings([_grounded(), _INVOICE])
    settings.knowledge_databases = ["support-kb"]
    return settings


def test_a_grounded_setup_that_can_produce_a_draft_passes():
    EmailClassificationAgent._validate(_grounded_settings(), _drafting(), "INBOX", _counter, _delegation())


def test_grounding_without_a_knowledge_agent_is_rejected():
    with pytest.raises(ValueError, match="no knowledge agent is configured"):
        EmailClassificationAgent._validate(_grounded_settings(), _drafting(), "INBOX", _counter, None)


def test_grounding_without_a_knowledge_database_is_rejected():
    """A collection name alone identifies nothing — retrieval would be scoped to no bucket and answer from nothing."""
    settings = _grounded_settings()
    settings.knowledge_databases = []
    with pytest.raises(ValueError, match="no knowledge database is configured"):
        EmailClassificationAgent._validate(settings, _drafting(), "INBOX", _counter, _delegation())


def test_a_grounded_category_that_gets_no_drafted_reply_is_rejected():
    """It would retrieve nothing and leave the admin looking for drafts that were never due.

    Another category *is* opted in, so this has to be caught by the grounding rule specifically — the existing
    "drafting on but nothing opted in" check does not fire here.
    """
    settings = _settings(
        [
            _grounded().model_copy(update={"draft_reply": False}),
            _INVOICE.model_copy(update={"draft_reply": True}),
        ]
    )
    settings.knowledge_databases = ["support-kb"]
    with pytest.raises(ValueError, match="name a knowledge collection but are not set to get a drafted reply"):
        EmailClassificationAgent._validate(settings, _drafting(), "INBOX", _counter, _delegation())


def test_a_blank_fallback_text_is_rejected_up_front():
    """The one message that needs a fallback text is the one nobody is watching for — a blank has to fail here."""
    draft = _drafting()
    draft.no_information_draft = "   "
    with pytest.raises(ValueError, match="both fallback draft texts must be set"):
        EmailClassificationAgent._validate(_grounded_settings(), draft, "INBOX", _counter, _delegation())


def test_grounding_is_not_checked_when_drafting_is_off():
    """Drafting off means grounding cannot execute, so it must not be able to fail the run either.

    The reachable case is an admin who set grounding up and later paused drafting: every classification run would
    otherwise die on a feature that `_drafting_batch` disables anyway.
    """
    settings = _grounded_settings()
    settings.knowledge_databases = []
    EmailClassificationAgent._validate(settings, _no_drafting(), "INBOX", _counter, None)
