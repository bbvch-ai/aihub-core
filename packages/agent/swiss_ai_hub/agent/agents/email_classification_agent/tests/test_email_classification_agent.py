from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pytest_bdd import given, parsers, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import MailBatchClassifiedEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.imap import EmailClassificationSettings, ImapClientConfig, MailCategory
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import CategoryVerdict
from swiss_ai_hub.agent.imap.tests.mail_doubles import infrastructure_patches, make_client, parsed_message, summary
from swiss_ai_hub.agent.runners import AgentTestRunner

scenarios("./features/email_classification_agent.feature")

_CLASSIFY = "swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier.MailClassifier.classify"

_SUPPORT = MailCategory(
    category="support_request", imap_folder="Triage/Support", description="Needs an action from our team."
)
_INVOICE = MailCategory(category="invoice", imap_folder="Triage/Invoices", description="A bill or payment reminder.")
_FALLBACK_FOLDER = "Triage/Uncategorised"


def _config(categories: list[MailCategory] | None = None) -> EmailClassificationAgentConfig:
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
            confidence_threshold=0.6,
        ),
    )


def _verdict(category: MailCategory | None, confidence: float) -> CategoryVerdict:
    return CategoryVerdict(category=category, confidence=confidence, reason="because the body says so")


def _selection(selected_index: int | None, confidence: float) -> SimpleNamespace:
    """What the LLM returns before MailClassifier resolves it — an index, not a folder."""
    return SimpleNamespace(selected_index=selected_index, confidence=confidence, reason="because the body says so")


# --- fixtures ---


@given(
    "an EmailClassificationAgent runner with three unread messages the model is confident about",
    target_fixture="scenario",
)
def _confident_batch() -> dict:
    return {
        "unread": [summary("1"), summary("2"), summary("3")],
        "verdicts": [_verdict(_SUPPORT, 0.9), _verdict(_SUPPORT, 0.8), _verdict(_INVOICE, 0.95)],
    }


@given(
    "an EmailClassificationAgent runner with one unread message classified below the confidence threshold",
    target_fixture="scenario",
)
def _low_confidence() -> dict:
    """Drives the real MailClassifier: stubbing the verdict here would skip the threshold under test."""
    return {"unread": [summary("1")], "selections": [_selection(selected_index=0, confidence=0.2)]}


@given("an EmailClassificationAgent runner with one unread message no category fits", target_fixture="scenario")
def _no_category_fits() -> dict:
    return {"unread": [summary("1")], "selections": [_selection(selected_index=None, confidence=0.9)]}


@given("an EmailClassificationAgent runner with an empty inbox", target_fixture="scenario")
def _empty_inbox() -> dict:
    return {"unread": [], "verdicts": []}


@given("an EmailClassificationAgent runner whose category folder does not exist yet", target_fixture="scenario")
def _missing_folder() -> dict:
    return {"unread": [summary("1")], "verdicts": [_verdict(_SUPPORT, 0.9)], "folder_created": True}


@given("an EmailClassificationAgent runner with no categories configured", target_fixture="scenario")
def _no_categories() -> dict:
    return {"unread": [summary("1")], "verdicts": [], "categories": []}


# --- driving ---


@when("the user triggers classification", target_fixture="agent_runner")
@async_test
async def _(scenario: dict) -> AgentTestRunner:
    agent_runner = AgentTestRunner(
        agent_type=EmailClassificationAgent, agent_config=_config(scenario.get("categories"))
    )
    client = make_client(unread=scenario["unread"], folder_created=scenario.get("folder_created", False))
    client.fetch_message = AsyncMock(side_effect=lambda message_id, **_: parsed_message(message_id=message_id))
    agent_runner.imap_client = client

    # A scenario supplies either raw LLM selections — exercising the real classifier, including the threshold —
    # or ready-made verdicts when only the agent's filing behaviour is under test.
    llm = AsyncMock() if "selections" in scenario else None
    if llm is not None:
        llm.astructured_predict = AsyncMock(side_effect=list(scenario["selections"]))

    with ExitStack() as stack:
        for patcher in infrastructure_patches(client, llm=llm):
            stack.enter_context(patcher)
        if llm is None:
            stack.enter_context(patch(_CLASSIFY, new=AsyncMock(side_effect=list(scenario["verdicts"]))))
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(start_event=ClassifyMailStartEvent(), topic=topic)
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
    assert agent_runner.imap_client.move_message.await_count == 3


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
    assert agent_runner.imap_client.move_message.await_count == 0


@then("the created folder is recorded on the classification")
def _(agent_runner: AgentTestRunner):
    event = _summary_event(agent_runner)
    assert event.classified[0].folder_created is True


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


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event


@then("no ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert not agent_runner.has_exception_event


@then("an ExceptionEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_exception_event
