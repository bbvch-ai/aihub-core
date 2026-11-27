# In-the-Loop Deadlines and Delegation Answers Through JetStream

## Context

A run that asks a person (`HumanInTheLoop`), a Slack or Teams channel (`BotInTheLoop`) or another agent
(`AgentInTheLoop`) waits for an answer that may never come (#555). Only agent delegations could set a deadline, and it
was an `asyncio` timer in the asking dispatcher process. The answer of a delegated agent reached the caller the same
way: a NATS Core subscription opened by the caller's process on the delegate's run. Either process restarting left the
caller's run waiting forever, and the timeout arrived as an `AgentInTheLoopExceptionEvent`, indistinguishable from the
delegate failing.

Agents will soon call other agents from the tool loop (#2299), where an unanswered call blocks the whole answer, so both
the deadline and the answer have to survive restarts and the timeout has to be its own outcome.

NATS added scheduled messages in 2.12 (ADR-51 of nats-architecture-and-design); 2.12 is end of life, 2.14 is the oldest
supported line.

## Decision Drivers

- *Survives restarts* of the asking and the answering dispatcher, and replicas of either.
- *No new component*: no extra scheduler loop, lease or store.
- *A timeout is a workflow input*: a step names it next to the response and takes the fallback path.
- *First outcome wins*: an answer racing its deadline resumes the run once.
- *Requests without a deadline behave as before*.

## Decision

- **NATS 2.14.10**, and every agent class's stream allows message schedules. `StreamManager` now updates an existing
  stream with missing subjects and the schedule flag (it only created streams before), and `AgentDispatcher.start` asks
  for both. Enabling schedules cannot be undone on the server.
- **Timeout events.** `HumanInTheLoopTimeoutEvent`, `AgentInTheLoopTimeoutEvent` and `BotInTheLoopTimeoutEvent`, all
  `InTheLoopTimeoutEvent(ControlAndDisplayEvent)` naming the request, exposed as `X.timeout` next to `X.response`. Every
  request has `timeout_seconds` (default `None`, wait for as long as the run lives) and builds its own timeout event
  (`timed_out()`). One class per kind, because steps match their inputs by exact class.
- **The deadline is a scheduled message.** Before a request with a deadline is published, `InTheLoopDeadlines.arm`
  publishes its timeout event to `agent_deadline.{class}.{request_event_id}` with `Nats-Schedule: @at <deadline>` and
  `Nats-Schedule-Target` set to the asking run's control subject. The schedule subject is outside `agent.>` because the
  API and the bot read every `agent.` subject with NATS Core and would take the pending event as fired.
- **First outcome wins.** `InTheLoopDeadlines.settles` runs before any step is triggered: for a request that has a
  deadline, the first of answer and timeout sets a run-context key with `SET NX`; the other triggers nothing. An answer
  that wins purges the schedule. Requests without a deadline are not tracked.
- **The fired timeout is displayed by the dispatcher.** A scheduled message reaches JetStream consumers only, not Core
  subscribers, so the dispatcher publishes the display copy itself when it handles one.
- **The delegate answers.** `StartEvent.delegated_by` (`AgentDelegation`: caller run, request id, depth) is set by
  `trigger_agent_in_the_loop`. The delegated run's dispatcher publishes `AgentInTheLoopResponseEvent` or
  `AgentInTheLoopExceptionEvent` into the caller's run through JetStream when it tears down. It records the delegation
  before fetching its config, so a delegate failing on its config still answers. The caller holds no subscription and no
  timer. An API caller cannot set `delegated_by` (`_api_server_fields`, overridden in `_api_server_data`).
- **`share_run_id` is removed.** Two runs sharing one run context cannot both answer and tear down; nothing used it.
- **Statistics** count timeouts per kind, `has_timeouts` on runs, displays and threads, and a request answered by a
  timeout, or a delegation answered by a failure, is no longer open.

## Consequences

- Downgrading NATS below 2.12 takes the agent streams offline; snapshot the NATS volume before rolling out.
- After a backup restore, overdue schedules fire at once; the requests they belong to are settled or gone, so they are
  dropped.
- Single-node NATS syncs to disk every two minutes (`sync_interval`), so a host crash can lose a schedule armed in that
  window, as it can lose any other message.
- A delegation's tracing span now covers the dispatch only; the delegate's steps still nest under it.
- Not done here, from the NATS review of this change: online status from keys with a per-key TTL instead of discovery
  rounds (#1970); loading a run's events lazily instead of replaying the class's 30 days at every dispatcher start,
  which also leaks a durable consumer per process (relevant before NATS 2.15, which limits consumers per stream to
  1000); acknowledging after processing in `JSSubscriber`; a durable consumer for the API's event persister; keeping
  display events, token chunks included, out of the 30-day agent streams; the bot's in-memory BITL mapping; a random
  `Nats-Msg-Id` per publish, which defeats deduplication. Considered and not pursued: cron schedules on NATS instead of
  the Valkey-led `CronScheduler`, Valkey leases as KV compare-and-set, atomic batch publishing of step results, and
  priority-group consumers.
