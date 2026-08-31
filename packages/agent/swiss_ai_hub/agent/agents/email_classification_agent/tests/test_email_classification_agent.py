import asyncio
from contextlib import ExitStack
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import CronStartEvent, MailBatchClassifiedEvent, MailBatchDraftedEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import DraftEmailSettings, EmailClassificationSettings, ImapClientConfig, MailCategory
from swiss_ai_hub.core.infrastructure import RedisSettings
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import (
    CategoryVerdict,
    ClassificationOutcome,
)
from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
from swiss_ai_hub.agent.imap.tests.mail_doubles import (
    LOADER_FOR_FILE,
    archived_eml,
    infrastructure_patches,
    make_client,
    parsed_message,
    stored_attachment_refs,
    summary,
)
from swiss_ai_hub.agent.runners import AgentTestRunner

scenarios("./features/email_classification_agent.feature")

_CLASSIFY = "swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier.MailClassifier.classify"
_FOR_FILE = LOADER_FOR_FILE

_SUPPORT = MailCategory(
    category="support_request", imap_folder="Triage/Support", description="Needs an action from our team."
)
_INVOICE = MailCategory(category="invoice", imap_folder="Triage/Invoices", description="A bill or payment reminder.")

# The opt-in pair the drafting scenarios run on: support gets a reply, an invoice does not. Two categories with
# different answers is the whole point of the feature, so a single all-on taxonomy would prove nothing.
_SUPPORT_DRAFTING = _SUPPORT.model_copy(update={"draft_reply": True})
_INVOICE_NOT_DRAFTING = _INVOICE.model_copy(update={"draft_reply": False})

_FALLBACK_FOLDER = "Triage/Uncategorised"
_DRAFTS_FOLDER = "Drafts"
_AGENT_CLASS = EmailClassificationAgent.__name__
_AGENT_ID = "email_classification_agent"
_FOREIGN_RUN = "a-run-that-is-still-filing"


def _config(
    categories: list[MailCategory] | None = None,
    draft: DraftEmailSettings | None = None,
) -> EmailClassificationAgentConfig:
    return EmailClassificationAgentConfig(
        agent_id="email_classification_agent",
        name=LocaleString(en="Email Classification Agent"),
        description=LocaleString(en="Test agent"),
        imap=ImapClientConfig(
            host="imap.test", username="a@test", password="secret", enable_move=True, processed_folder=""
        ),
        llm=LLMConfig(model_name="text-generation/test-model"),
        classification=EmailClassificationSettings(
            categories=[_SUPPORT, _INVOICE] if categories is None else categories,
            fallback_folder=_FALLBACK_FOLDER,
        ),
        draft=draft or DraftEmailSettings(drafts_folder=_DRAFTS_FOLDER),
    )


def _drafting(**overrides) -> DraftEmailSettings:
    return DraftEmailSettings(enable_draft=True, drafts_folder=_DRAFTS_FOLDER, **overrides)


def _fake_llm_event() -> SimpleNamespace:
    return SimpleNamespace(chat_messages=[SimpleNamespace(content="Thanks for writing — we are on it.")])


def _loader_yielding(text: str) -> SimpleNamespace:
    """A document loader double returning one Document with `text`.

    Standing in for MinerU/MarkItDown at the loader boundary keeps these scenarios offline while still driving the
    real extractor: an empty string here is exactly what MinerU hands back for an image holding no words.
    """
    return SimpleNamespace(aload_data_from_bytes=AsyncMock(return_value=[SimpleNamespace(text=text)]))


def _verdict(category: MailCategory | None) -> CategoryVerdict:
    outcome = ClassificationOutcome.CATEGORISED if category else ClassificationOutcome.DECLINED
    return CategoryVerdict(category=category, outcome=outcome, reason="because the body says so")


def _selection(selected_index: int | None) -> SimpleNamespace:
    """What the LLM returns before MailClassifier resolves it — an index, not a folder."""
    return SimpleNamespace(selected_index=selected_index, reason="because the body says so")


@pytest.fixture(autouse=True)
def clear_mailbox_lease():
    """Every scenario drives the same profile, and a scenario that ends in an ExceptionEvent deliberately leaves the
    lease held until it expires — so without this, one failing run would make every later scenario skip its own."""

    async def clear() -> None:
        redis = RedisSettings.create_client()
        await redis.delete(f"mailbox:run_lease:{_AGENT_CLASS}:{_AGENT_ID}")
        await redis.aclose()

    asyncio.run(clear())


# --- fixtures ---


@given(
    "an EmailClassificationAgent runner with three unread messages the model classifies into categories",
    target_fixture="scenario",
)
def _classified_batch() -> dict:
    return {
        "unread": [summary("1"), summary("2"), summary("3")],
        "verdicts": [_verdict(_SUPPORT), _verdict(_SUPPORT), _verdict(_INVOICE)],
    }


@given("an EmailClassificationAgent runner with one unread message no category fits", target_fixture="scenario")
def _no_category_fits() -> dict:
    """Drives the real MailClassifier: stubbing the verdict here would skip the decline route under test."""
    return {"unread": [summary("1")], "selections": [_selection(selected_index=None)]}


@given("an EmailClassificationAgent runner with an empty inbox", target_fixture="scenario")
def _empty_inbox() -> dict:
    return {"unread": [], "verdicts": []}


@given("an EmailClassificationAgent runner whose category folder does not exist yet", target_fixture="scenario")
def _missing_folder() -> dict:
    return {"unread": [summary("1")], "verdicts": [_verdict(_SUPPORT)], "folder_created": True}


@given("an EmailClassificationAgent runner with no categories configured", target_fixture="scenario")
def _no_categories() -> dict:
    return {"unread": [summary("1")], "verdicts": [], "categories": []}


@given(
    "an EmailClassificationAgent runner where support_request is set to get a drafted reply",
    target_fixture="scenario",
)
def _drafting_support() -> dict:
    """Two support mails and one invoice, with only support opted in — so the same run must draft and not draft."""
    return {
        "unread": [summary("1"), summary("2"), summary("3")],
        "verdicts": [_verdict(_SUPPORT_DRAFTING), _verdict(_SUPPORT_DRAFTING), _verdict(_INVOICE_NOT_DRAFTING)],
        "categories": [_SUPPORT_DRAFTING, _INVOICE_NOT_DRAFTING],
        "draft": _drafting(),
    }


@given(
    "an EmailClassificationAgent runner where drafting is on but the mail fits no category",
    target_fixture="scenario",
)
def _drafting_fallback_only() -> dict:
    return {
        "unread": [summary("1")],
        "selections": [_selection(selected_index=None)],
        "categories": [_SUPPORT_DRAFTING, _INVOICE_NOT_DRAFTING],
        "draft": _drafting(),
    }


@given("an EmailClassificationAgent runner with reply drafting turned off", target_fixture="scenario")
def _drafting_disabled() -> dict:
    return {
        "unread": [summary("1")],
        "verdicts": [_verdict(_SUPPORT_DRAFTING)],
        "categories": [_SUPPORT_DRAFTING, _INVOICE_NOT_DRAFTING],
        "draft": DraftEmailSettings(enable_draft=False, drafts_folder=_DRAFTS_FOLDER),
    }


@given("an EmailClassificationAgent runner drafting with attachment reading on", target_fixture="scenario")
def _drafting_with_attachments() -> dict:
    """A Word attachment, large enough to clear the size floor, whose text only exists inside the file."""
    return {
        "unread": [summary("1")],
        "verdicts": [_verdict(_SUPPORT_DRAFTING)],
        "categories": [_SUPPORT_DRAFTING],
        "draft": _drafting(include_attachments=True),
        "attachment_refs": stored_attachment_refs(
            filename="order.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size_bytes=40_000,
        ),
        "extracted": "Order 4711 was delivered to the wrong depot.",
    }


@given(
    "an EmailClassificationAgent runner drafting a message whose attachment holds no text", target_fixture="scenario"
)
def _drafting_textless_attachment() -> dict:
    """The cat photo: MinerU answers with empty markdown, which is not an error and must not read as one."""
    return {
        "unread": [summary("1")],
        "verdicts": [_verdict(_SUPPORT_DRAFTING)],
        "categories": [_SUPPORT_DRAFTING],
        "draft": _drafting(include_attachments=True),
        "attachment_refs": stored_attachment_refs(filename="cat.jpg", content_type="image/jpeg", size_bytes=84_000),
        "extracted": "",
    }


@given(
    "an EmailClassificationAgent runner drafting a message carrying only a signature logo", target_fixture="scenario"
)
def _drafting_signature_logo() -> dict:
    """A 3 KB inline PNG — the routine business mail that must not cost a parser round trip."""
    return {
        "unread": [summary("1")],
        "verdicts": [_verdict(_SUPPORT_DRAFTING)],
        "categories": [_SUPPORT_DRAFTING],
        "draft": _drafting(include_attachments=True),
        "attachment_refs": stored_attachment_refs(filename="logo.png", content_type="image/png", size_bytes=3_000),
    }


@given(
    "an EmailClassificationAgent runner whose mailbox is already held by a running classification",
    target_fixture="scenario",
)
@async_test
async def _mailbox_already_held() -> dict:
    """Stands in for the previous cron occurrence still working through a slow mailbox.

    The lease is taken against the real Valkey the runner itself uses, so this exercises the same `SET NX` the
    overlapping run will lose against — not a patched-out stub of it.
    """
    redis = RedisSettings.create_client()
    await MailboxRunLease(redis).acquire(_AGENT_CLASS, _AGENT_ID, _FOREIGN_RUN)
    await redis.aclose()
    return {"unread": [summary("1"), summary("2")], "verdicts": [], "release_foreign_lease": True}


# --- driving ---


@when("the user triggers classification", target_fixture="agent_runner")
@async_test
async def _(scenario: dict) -> AgentTestRunner:
    return await _drive(scenario, ClassifyMailStartEvent())


@when("the scheduler triggers classification", target_fixture="agent_runner")
@async_test
async def _(scenario: dict) -> AgentTestRunner:
    """The unattended entry point. Everything downstream is shared with the manual one, which is the point —
    a scheduled run must not be a second code path."""
    return await _drive(scenario, CronStartEvent(scheduled_for=datetime.now(UTC)))


async def _drive(scenario: dict, start_event: BaseEvent) -> AgentTestRunner:
    agent_runner = AgentTestRunner(
        agent_type=EmailClassificationAgent,
        agent_config=_config(scenario.get("categories"), scenario.get("draft")),
    )
    client = make_client(unread=scenario["unread"], folder_created=scenario.get("folder_created", False))
    client.fetch_message = AsyncMock(side_effect=lambda message_id, **_: parsed_message(message_id=message_id))
    agent_runner.imap_client = client
    load_attachment = AsyncMock(return_value=b"%PDF-1.4 invoice total 42.00")
    agent_runner.load_attachment = load_attachment
    # Owned here, not inside infrastructure_patches, so an assertion can still read the prompt off it once the
    # patches have been torn down at the end of this function.
    llm_stream = AsyncMock(return_value=_fake_llm_event())
    agent_runner.llm_stream = llm_stream

    # A scenario supplies either raw LLM selections — exercising the real classifier, including how it resolves
    # a decline — or ready-made verdicts when only the agent's filing behaviour is under test.
    llm = AsyncMock() if "selections" in scenario else None
    if llm is not None:
        llm.astructured_predict = AsyncMock(side_effect=list(scenario["selections"]))

    with ExitStack() as stack:
        for patcher in infrastructure_patches(
            client,
            llm_stream=llm_stream,
            llm=llm,
            archived=scenario.get("archived", archived_eml()),
            load_attachment=load_attachment,
            attachment_refs=scenario.get("attachment_refs"),
        ):
            stack.enter_context(patcher)
        if llm is None:
            stack.enter_context(patch(_CLASSIFY, new=AsyncMock(side_effect=list(scenario["verdicts"]))))
        if "extracted" in scenario:
            stack.enter_context(patch(_FOR_FILE, return_value=_loader_yielding(scenario["extracted"])))
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(start_event=start_event, topic=topic)

    if scenario.get("release_foreign_lease"):
        redis = RedisSettings.create_client()
        await MailboxRunLease(redis).release(_AGENT_CLASS, _AGENT_ID, _FOREIGN_RUN)
        await redis.aclose()
    return agent_runner


def _dedupe(events: list[BaseEvent]) -> list[BaseEvent]:
    """ControlAndDisplayEvents are observed twice (JetStream + NATS Core) — deduplicate by event_id."""
    return list({e.event_id: e for e in events}.values())


def _summary_event(agent_runner: AgentTestRunner) -> MailBatchClassifiedEvent:
    events = _dedupe(agent_runner.get_events_of_class(MailBatchClassifiedEvent))
    assert len(events) == 1
    return events[0]


# --- assertions ---


@then(parsers.parse("a MailBatchClassifiedEvent with {count:d} classified messages was emitted"))
def _(agent_runner: AgentTestRunner, count: int):
    event = _summary_event(agent_runner)
    assert event.count == count
    assert len(event.classified) == count


@then("each message was filed into its category folder")
def _(agent_runner: AgentTestRunner):
    event = _summary_event(agent_runner)
    filed = {ref.message_id: ref.target_folder for ref in event.classified}
    assert filed == {"1": "Triage/Support", "2": "Triage/Support", "3": "Triage/Invoices"}
    assert agent_runner.imap_client.relocate_message.await_count == 3


@then(parsers.parse("the summary counts {support:d} support_request and {invoice:d} invoice"))
def _(agent_runner: AgentTestRunner, support: int, invoice: int):
    event = _summary_event(agent_runner)
    assert event.per_category == {"support_request": support, "invoice": invoice}
    assert event.fallback_count == 0


@then("the message was filed into the fallback folder")
def _(agent_runner: AgentTestRunner):
    event = _summary_event(agent_runner)
    assert [ref.target_folder for ref in event.classified] == [_FALLBACK_FOLDER]
    assert event.classified[0].category is None


@then(parsers.parse("the summary counts {count:d} message in the fallback folder"))
def _(agent_runner: AgentTestRunner, count: int):
    event = _summary_event(agent_runner)
    assert event.fallback_count == count
    assert event.per_category == {}


@then("no message was filed")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.imap_client.relocate_message.await_count == 0


@then("the created folder is recorded on the classification")
def _(agent_runner: AgentTestRunner):
    event = _summary_event(agent_runner)
    assert event.classified[0].folder_created is True


@then("the whole batch shares one folder check")
def _(agent_runner: AgentTestRunner):
    """One ensure_folders for the run, not one per message — the reason filing is batched at all."""
    assert agent_runner.imap_client.ensure_folders.await_count == 1
    assert agent_runner.imap_client.ensure_folders.await_args.args[0] == ["Triage/Invoices", "Triage/Support"]


@then("every classified message references its archived original and attachments")
def _(agent_runner: AgentTestRunner):
    event = _summary_event(agent_runner)
    for ref in event.classified:
        assert ref.original_message is not None
        assert ref.original_message.content_type == "message/rfc822"
        assert ref.attachments[0].filename == "report.pdf"


@then("no draft was appended and nothing was sent")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.imap_client.append_draft.await_count == 0
    assert agent_runner.imap_client.mark_drafted.await_count == 0


def _drafted_event(agent_runner: AgentTestRunner) -> MailBatchDraftedEvent:
    events = _dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))
    assert len(events) == 1
    return events[0]


@then(parsers.parse("a MailBatchDraftedEvent with {count:d} drafts was emitted"))
def _(agent_runner: AgentTestRunner, count: int):
    event = _drafted_event(agent_runner)
    assert event.count == count
    assert len(event.drafted) == count
    assert agent_runner.imap_client.append_draft.await_count == count


@then("only the support_request mail was drafted")
def _(agent_runner: AgentTestRunner):
    """The opt-in is the whole feature: an unticked category in the same batch must produce nothing."""
    event = _drafted_event(agent_runner)
    assert event.per_category == {"support_request": 2}
    assert {ref.source_uid for ref in event.drafted} == {"1", "2"}
    assert event.skipped_count == 1


@then("each draft is threaded to the message it replies to")
def _(agent_runner: AgentTestRunner):
    event = _drafted_event(agent_runner)
    for ref in event.drafted:
        assert ref.subject == "Re: Quarterly report"
        assert ref.in_reply_to == "<orig-1@test>"
        assert ref.recipient == "alice@test"
        assert ref.drafts_folder == "[Gmail]/Drafts"


@then("every appended draft carries the Draft flag and no message was sent")
def _(agent_runner: AgentTestRunner):
    """`append_draft` is the only mail-writing call in the whole agent, and it flags `\\Draft` — there is no SMTP
    client anywhere to assert against, which is the actual guarantee."""
    for call in agent_runner.imap_client.append_draft.await_args_list:
        folder, raw = call.args
        assert folder == _DRAFTS_FOLDER
        assert b"Subject: Re: Quarterly report" in raw
        assert b"In-Reply-To: <orig-1@test>" in raw
    assert agent_runner.imap_client.mark_drafted.await_count == 0


@then("no draft was appended")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.imap_client.append_draft.await_count == 0


@then(parsers.parse("a MailBatchDraftedEvent reporting {count:d} drafts and {skipped:d} skipped was emitted"))
def _drafted_summary_counts(agent_runner: AgentTestRunner, count: int, skipped: int):
    """A zero-count event rather than silence: `skipped_count` is the only record of mail the agent declined to draft
    for, so emitting nothing would make exactly the all-skipped batches invisible to anything counting it."""
    events = _dedupe(agent_runner.get_events_of_class(MailBatchDraftedEvent))
    assert len(events) == 1, f"expected exactly one MailBatchDraftedEvent, got {len(events)}"
    assert events[0].count == count
    assert events[0].skipped_count == skipped


@then("the attachment text reached the drafting prompt")
def _(agent_runner: AgentTestRunner):
    prompt = _drafting_prompt(agent_runner)
    assert "Order 4711 was delivered to the wrong depot." in prompt
    assert "order.docx" in prompt
    assert agent_runner.load_attachment.await_count == 1


@then("the attachment is named as holding no text and no empty text block was sent")
def _(agent_runner: AgentTestRunner):
    """The cat photo has to be *mentioned* — a reply that ignores 'see attached' is the failure — but with an
    explicit 'no text', so the model has nothing to invent contents from."""
    prompt = _drafting_prompt(agent_runner)
    assert "cat.jpg (image/jpeg, 82 KB) — no text could be extracted" in prompt
    assert "Content of the attachment" not in prompt


@then("the signature logo was never fetched")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.load_attachment.await_count == 0
    prompt = _drafting_prompt(agent_runner)
    assert "logo.png" not in prompt


def _drafting_prompt(agent_runner: AgentTestRunner) -> str:
    """The user message the drafting step handed the model, read off the display_llm_stream double."""
    calls = agent_runner.llm_stream.await_args_list
    assert calls, "the drafting step never called the LLM"
    messages = calls[-1].args[2]
    return messages[-1].content


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event


@then("no ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_exception_event


@then("an ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_exception_event


@then("no message was listed, fetched or filed")
def _(agent_runner: AgentTestRunner):
    """The skip has to happen before the listing, not after: everything from here on is slow, and the mail is
    still unread, so a second run reaching any of it would redo the whole batch."""
    assert agent_runner.imap_client.list_unread.await_count == 0
    assert agent_runner.imap_client.fetch_message.await_count == 0
    assert agent_runner.imap_client.relocate_message.await_count == 0


@then("no MailBatchClassifiedEvent was emitted")
def _(agent_runner: AgentTestRunner):
    assert _dedupe(agent_runner.get_events_of_class(MailBatchClassifiedEvent)) == []


@then("the mailbox is no longer held")
@async_test
async def _(agent_runner: AgentTestRunner):
    """A lease left behind would silently cost the next occurrence its run, until the TTL expired."""
    redis = RedisSettings.create_client()
    try:
        assert await MailboxRunLease(redis).acquire(_AGENT_CLASS, _AGENT_ID, "a-later-run") is True
        await MailboxRunLease(redis).release(_AGENT_CLASS, _AGENT_ID, "a-later-run")
    finally:
        await redis.aclose()
