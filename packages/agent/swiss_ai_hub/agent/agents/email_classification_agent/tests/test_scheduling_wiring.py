"""Guards the two couplings that are invisible at the call site and fail silently in production.

Neither is enforceable by the framework: schedulability is derived from a step's type annotation, and the lease is
released by whichever step happens to be terminal. Both keep working right up until someone edits a signature.
"""

import inspect

from swiss_ai_hub.core.agents import CRON_CONFIG_KEY
from swiss_ai_hub.core.events.agent import CronStartEvent, StopEvent
from swiss_ai_hub.core.form import CronInput

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.email_classification_agent import EmailClassificationAgent
from swiss_ai_hub.agent.imap.mailbox_lease_lost_error import MailboxLeaseLostError
from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner


def test_the_blueprint_is_discovered_as_schedulable():
    """`AgentRunner.discovery_handler` derives is_schedulable exactly this way. Dropping CronStartEvent from the
    entry step would silently un-schedule every profile of this blueprint."""
    start_events = EmailClassificationAgent.get_start_events()

    assert any(issubclass(event, CronStartEvent) for event in start_events)


def test_the_blueprint_stays_out_of_the_chat_ui():
    """Schedulable and conversational are independent, and this one must not become the latter by accident."""
    assert not any(event.__name__ == "UserMessageEvent" for event in EmailClassificationAgent.get_start_events())


def test_the_blueprint_declares_no_schedule_of_its_own():
    """`cron` is platform-owned: the runner injects it for schedulable classes. A blueprint that declares its own
    would shadow the base field and take the schedule back out of the scheduler's reach."""
    form = EmailClassificationAgentConfig.as_form()

    assert form.cron is None
    assert CRON_CONFIG_KEY not in form.get_configurable_fields()


def test_the_scheduler_can_read_the_schedule_off_the_published_form():
    """`CronScheduler` reads `config_data["cron"]` by name, at the top level only. Deriving schedulability and
    injecting the element are separate steps in the runner, and only their combination makes a profile fire."""
    runner = AgentRunner(agent_type=EmailClassificationAgent, agent_config=EmailClassificationAgentConfig.as_form())

    assert isinstance(runner.published_config.cron, CronInput)
    assert CRON_CONFIG_KEY in [element.name for element in runner.form]


def test_every_terminal_step_accounts_for_the_lease():
    """A step that can end a run has to have dealt with the mailbox lease one way or the other.

    Two legitimate shapes, which is why this asserts on the lease being *handled* rather than on `release`
    specifically: the entry step ends a run by failing to acquire (releasing there would hand away a lease another
    run holds), while a step that ends a run after the work has to release.

    The invariant belongs to the terminal step, not to a step of a particular name — #1639 appends a drafting pass
    after filing and takes over returning `StopEvent`, so it inherits the release. Forgetting leaves the mailbox
    claimed until the TTL expires, costing the next occurrence its run with nothing but a log line to say why.
    """
    terminal_steps = [
        step for step in EmailClassificationAgent.get_steps() if StopEvent in getattr(step, "_output_events", set())
    ]
    assert terminal_steps, "no step returns StopEvent — the run would never terminate"

    for step in terminal_steps:
        assert MailboxRunLease.__name__ in inspect.getsource(step), (
            f"{step.__name__} can return a StopEvent but never touches the mailbox lease — it must either release "
            f"the lease or be the step that failed to acquire it"
        )


def test_the_step_that_does_the_work_releases_the_lease():
    """The acquire/release pair specifically, so a refactor cannot satisfy the test above by merely naming the class.

    `finish_drafting_step` is the only step that returns `StopEvent` on the working path — every drafting outcome
    now converges on one `MailBatchDraftedEvent`, so there is one terminal step to release from. `list_unread_step`
    is the other `StopEvent` producer and is the run that never acquired.
    """
    assert "acquire" in inspect.getsource(EmailClassificationAgent.list_unread_step)
    assert "release" in inspect.getsource(EmailClassificationAgent.finish_drafting_step)


def test_drafting_runs_under_a_heartbeat_and_checks_the_lease_before_appending():
    """Drafting is the second slow phase and the second one that writes to the mailbox.

    A model call per message means the pass can outlive the TTL exactly as filing can, so it needs the same
    heartbeat; and an append is a mutation, so a lease lost during the model calls has to stop the run before the
    first draft lands rather than after.
    """
    source = inspect.getsource(EmailClassificationAgent._append_all_drafts)

    assert "lease.heartbeat(" in source, "one model call per message can outlive the TTL — renew across the pass"

    lease_check = source.index("lease.lost")
    assert lease_check < source.index("do_draft_replies"), "a lost lease has to be caught before anything is appended"
    assert lease_check > source.index("_compose_all"), "checking before the work makes the heartbeat pointless"
    assert MailboxLeaseLostError.__name__ in source, "a lost lease must stop the run, not only warn"


def test_drafting_takes_the_lease_back_before_appending():
    """The delegation window has no step body to heartbeat from, so the lease is expected to lapse across it.

    A run waits on N RAG agents between requesting and collecting, and nothing renews in between — so treating a
    lapsed lease as fatal here would throw away a whole batch's drafts every time the delegates were slow, and the
    mail is already filed so those drafts would never be retried. Reacquiring is only safe because filing closed the
    window the lease protects; a lease another run actually holds still refuses.
    """
    source = inspect.getsource(EmailClassificationAgent._append_all_drafts)

    reacquire = source.index("reacquire")
    assert reacquire < source.index("lease.heartbeat("), "the lease has to be ours again before the heartbeat renews it"
    assert reacquire < source.index("do_draft_replies"), "nothing may be appended without holding the mailbox"
    assert MailboxLeaseLostError.__name__ in source, "a mailbox held by another run must stop the run, not warn"


def test_the_work_is_done_under_a_heartbeat_that_is_checked_before_filing():
    """The three phases of a run are individually slow and only one of them is safe to do twice.

    Renewing per classified message left the batch fetch and the filing pass either side of the loop unrenewed, so a
    slow mailbox could outlive the TTL in a phase where nothing was renewing — and losing the lease only logged,
    leaving the run to file mail another run already held. The heartbeat covers every phase, and the check before
    `_file_all` is what turns a lost lease into a stopped run rather than a double-filed one.
    """
    source = inspect.getsource(EmailClassificationAgent.classify_and_file_step)

    assert "lease.heartbeat(" in source, "the slow phases must run under a heartbeat, not per-message renewals"

    lease_check = source.index("lease.lost")
    assert lease_check < source.index("_file_all"), "a lost lease has to be caught before anything is filed"
    assert lease_check > source.index("_classify_all"), "checking before the work makes the heartbeat pointless"
    assert MailboxLeaseLostError.__name__ in source, "a lost lease must stop the run, not only warn"
