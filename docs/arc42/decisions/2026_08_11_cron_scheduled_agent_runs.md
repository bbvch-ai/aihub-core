# Cron-Scheduled Agent Runs

## Context

Agents run only in response to a user- or agent-initiated start event. There is no way to run one unattended on a fixed
schedule, which rules out the whole class of agents whose value is periodic work — inbox triage, recurring reports,
scheduled ingestion checks.

Adding scheduling raises four questions that each have more than one defensible answer:

- **How does an agent opt in?** The platform already distinguishes conversational agents from programmatic ones, and it
  does so by *derivation*: `AgentRunner` reports `is_conversational` by checking whether any declared start event
  subclasses `UserMessageEvent`. A schedulability flag could instead be declared explicitly on the runner.
- **Where does the scheduler run?** A cron scheduler is singleton background work. The API already hosts several such
  jobs (event persistence, endpoint discovery, OpenWebUI provisioning), but
  [#1203](https://github.com/bbvch-ai/aihub-core/issues/1203) plans to extract all of them into a new `aihub-daemon`
  deployed with `replicas: 1`. That extraction has not started.
- **What identity does a scheduled run execute under?** Every existing run carries a `UserIdentity`, which drives access
  checks, usage limits, and thread visibility.
- **How is "exactly once" guaranteed** when N API replicas each host a scheduler?

## Decision Drivers

- **Opt-in must be impossible to get half-right**: a blueprint that handles the event but forgets to register itself, or
  registers itself but handles nothing, should not be representable.
- **The later `aihub-daemon` move must not become a migration**: whatever we build now should relocate by rewiring, not
  by porting logic.
- **No new execution-identity concept**: "run as user" for unattended runs implies credential storage and delegated
  authority, which is a much larger decision than scheduling.
- **Correct under horizontal scaling**, including a replica dying mid-tick — not merely correct when one replica runs.

## Decision

### 1. Schedulability is derived from a new `ScheduledStartEvent`

An agent becomes schedulable by handling `ScheduledStartEvent`, exactly as it becomes conversational by handling
`UserMessageEvent`. `AgentRunner` derives `is_schedulable` during discovery and reports it on
`AgentClassDiscoveryResponseEvent`; it is persisted on `AgentClassEntity` and surfaced through the agent DTOs.

This makes the inconsistent states unrepresentable: the capability *is* the handled event, so there is nothing to keep
in sync. It also means a schedulable agent that handles no `UserMessageEvent` stays out of the chat UI for free.

### 2. The schedule is per-profile configuration, declared by the blueprint

The five cron positions plus an IANA timezone form `AgentSchedule`, a data-mode config model paired with a new
`CronInput` form element — the same duality `MilvusVectorStoreConfig`/`VectorStoreInput` and
`OrgMemoryWriteConfig.tenant_id`/`TenantSelect` already use. A blueprint declares
`schedule: AgentSchedule | CronInput | None`, and the value lands in `config_data` like every other setting, reusing the
existing persistence, validation, and DTO paths.

Positions are stored separately rather than as one `"0 12 * * *"` string so the Admin UI can offer per-position editing
and presets without parsing, and so an invalid position is rejected at the field that caused it. Cron expressions and
timezones are validated at configuration time, not at fire time.

Consequence: nothing in the backend prevents a non-schedulable blueprint from declaring a schedule field, or a
schedulable one from omitting it. A stray schedule is simply never read. The alternative — a platform-injected field on
`AgentConfigEntityDocument` outside `config_data` — would enforce the pairing but needs its own DTO and route surface
and has no precedent in the codebase.

### 3. The scheduler lives in `packages/core`, wired from the API

`swiss_ai_hub.core.scheduling` holds the calculator, the Redis state store, and `ScheduledAgentService`. The API's
`lifetime_manager.py` constructs and starts it alongside the existing discovery services.

Placing the logic in core rather than `packages/api` is what keeps #1203 cheap. `OpenWebuiProvisioner` is the precedent:
it lives in `core/infrastructure/`, is instantiated by the API, and is on #1203's list of things to "move" — a move that
relocates twelve lines of wiring, not 558 lines of logic. The scheduler needs a NATS-backed distributor, Redis, and the
mongoengine connection; unlike `AgentEndpointsDiscoveryService` it takes no `FastAPI` or controller and registers no
routes, so nothing ties it to the API process.

### 4. Scheduled runs are system runs

The run carries `user=None` and fires into a thread with no members. `ExternalAgentEventDistributor.distribute_event`
already accepts `user=None` and skips the thread-membership check in that case, so no new control path is needed and the
agent runner consumes the event unchanged.

This is safe because the agent runtime never reads tenancy from the initiating user — `packages/agent` contains no
reference to `acting_within_tenant`. Where an agent needs a tenant it reads one from its own profile
(`OrgMemoryWriteConfig.tenant_id`), which is admin-set and independent of who starts the run. Tenant *authorization* is
enforced at the HTTP boundary, which a scheduled run never crosses.

### 5. Exactly-once uses a leader lease **and** per-occurrence claims

Both are required and they solve different problems:

- The **leader lease** (`scheduler:leader`, a Redis lock with TTL, non-blocking acquire) stops two replicas ticking
  concurrently. Modelled on `OpenWebuiProvisioner._sync_lock`.
- The **per-occurrence claim** (`SET NX EX` on `scheduler:fired:{class}:{id}:{occurrence}`) stops the same occurrence
  firing twice when a leader dies mid-tick, before its watermark advanced, and another replica takes over.

A leader lease alone would satisfy "only one replica fires" while still permitting a duplicate run on failover.

All scheduler state — leadership, the tick watermark, and the claims — lives in Redis and nowhere else, which is the
property that makes the daemon lift a rewiring.

### 6. Ticks work in windows, with a bounded catch-up

Ticks are periodic, so an occurrence between two ticks would be missed if the scheduler asked "is it due now?". Each
tick fires every occurrence in `(watermark, now]`. Occurrences are enumerated in the schedule's own timezone and
returned in UTC, so "every day at 12:00" survives DST shifts as a wall-clock time.

The window start is clamped to `now - 15 minutes`. Without a bound, a scheduler down for three days would come back and
fire seventy-odd stale hourly runs at once. Occurrences dropped by the clamp are logged, not silently discarded. A cold
start adopts the current time and fires nothing.

### 7. `croniter` for cron parsing

Nothing in the tree parsed cron. `croniter` is a small, widely used library with timezone-aware iteration; the
alternative is hand-rolling field parsing, ranges, steps, and DST handling.

## Consequences

**Positive**

- Opt-in is a single handled event; the capability cannot drift from the implementation.
- The #1203 lift is a wiring change — no agent- or runner-side code is involved.
- Correct across N replicas today, including failover, without waiting on the daemon extraction.
- No new execution-identity concept, and no new tenancy plumbing.

**Negative**

- **Scheduled runs bypass usage limits.** `UsageLimits.check_and_increment` derives its tenant from
  `user.acting_within_tenant` and is only wired as a FastAPI `Depends` on HTTP endpoints. A scheduled run has neither a
  user nor an HTTP request, so nothing meters it: a misconfigured cron can consume LLM budget unchecked. Accepted for v1
  and tracked separately.
- **Scheduled runs are invisible in the UI.** A thread with no members appears in nobody's thread list. This is the
  documented v1 behaviour; configurable membership is [#1582](https://github.com/bbvch-ai/aihub-core/issues/1582).
- **The leader lease becomes dead code** once the scheduler moves into the single-replica daemon.
- **Occurrences missed beyond the catch-up window never run.** Deliberate, but it means extended downtime silently skips
  work beyond a warning in the logs.
- **A run that fails to start is not retried.** The claim is taken *before* the run is published, so if publishing
  raises, the tick aborts without advancing the watermark and the next tick finds the occurrence already claimed. This
  makes the failure at-most-once rather than at-least-once, which is the right way round given the acceptance criterion
  is "no duplicate runs" — but it does mean a transient publish failure silently drops that occurrence. It also stops
  one failing profile from starving the others, which would otherwise repeat on every tick.
- Discovery auto-registers a REST endpoint per start event, so schedulable agents also gain a
  `POST .../ScheduledStartEvent` route — an unplanned but useful manual trigger, which does carry a real user because it
  arrives over HTTP.

## Related

- Issue [#1580](https://github.com/bbvch-ai/aihub-core/issues/1580) — this change
- Issue [#1581](https://github.com/bbvch-ai/aihub-core/issues/1581) — the cron schedule editing UI
- Issue [#1582](https://github.com/bbvch-ai/aihub-core/issues/1582) — configurable thread membership
- Issue [#1203](https://github.com/bbvch-ai/aihub-core/issues/1203) — `aihub-daemon` extraction. Its out-of-scope list
  currently excludes hosting scheduled jobs, which contradicts the lift path assumed here; the two need reconciling.
- [Dynamic Agent Configuration](2026_01_07_enable_dynamic_agent_configuration_ui.md) — the blueprint/profile split the
  schedule field builds on
