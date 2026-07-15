# Decouple User-Memory Storage via a Dedicated Memory-Writer Agent

## Status

Accepted. Builds on `2026_07_07_disable_graph_store_for_user_memory` (cost reduction) and addresses issue #1179.

## Context

Issue #1179: after a RAG agent answers, `store_user_memory_step` persists user memory **inline** on the run's
critical path, and `check_ready_for_stop` holds the terminal `StopEvent` until storage completes. Since the
chat UI's "thinking" indicator clears only when the run stops, it lingers for the full memory-save duration.

Disabling the graph store for user memory (the companion ADR) cut the save from ~66s to ~17.5s, but ~17.5s
still blocks the run — and the save cost grows with the stored-memory count. The UX symptom (AC#2: indicator
must clear once the agent has answered) requires the save to be **off the critical path**, not merely faster.

Naive fire-and-forget (`asyncio.create_task` in the step) was rejected: the dispatcher deletes all run state
on the `StopEvent` (`agent_dispatcher.py`), so a detached task references a destroyed context; the write has
no durability, no trace attribution, and unbounded concurrency; and it violates the event-driven,
replayable premise of the Swiss AI Agent Protocol.

## Decision Drivers

- AC#2: the "thinking" indicator must clear as soon as the answer is ready.
- Keep the write durable, traced, ordered, and observable — not a detached in-process task.
- Reversible, incremental rollout; no behavior change when disabled.

## Decision

Persist user memory in an **independent run of a dedicated `MemoryWriterAgent`**, triggered by a
fire-and-forget delegation from the RAG/ExpertRAG store step.

- **`StoreUserMemoryRequestedEvent(StartEvent)`** carries everything the writer needs (user, messages,
  origin thread/display/run ids, originating agent identity, locale) so it rebuilds the *same* `AgentMemory`
  — preserving the fact-extraction prompt and `_agent_id` scoping tag.
- **`MemoryStorageRequestedEvent(ControlEvent)`** — a **pure control event** (not a `DisplayEvent`) wrapping
  that start event. A new branch in `AgentDispatcher._handle_step_result_event` publishes the wrapped start
  event to the writer's subject on a **fresh, independent execution context** (own thread/display/run ids),
  with **no response subscription** — the writer runs to its own `StopEvent` and cleans itself up, nothing is
  routed back. Because it is a plain control event it also lands in the caller's event store when published,
  so it doubles as the **stop-gate marker**: `check_ready_for_stop` gates on this millisecond-cheap marker
  (not on storage completion), so the run finalizes as soon as the answer is ready.
- **Why not AgentInTheLoop:** `AgentInTheLoopRequestEvent` is also a `DisplayEvent` (would render a delegation
  step in chat after the answer — the exact #1179 symptom) and opens a response subscription that routes the
  result back into the caller's soon-deleted run stores. The dedicated control event avoids both by
  construction; AITL is untouched.
- **`MemoryWriterAgent` is a system agent with baked-in identity.** `MemoryWriterAgentConfig.as_form()` sets
  `agent_id`/`name`/`description` as non-configurable primitives, so `deep_merge(non_configurable, {})`
  resolves a valid config even though no `agent_configs` profile record exists — **no config seeder needed**,
  no `packages/api` change. (Confirmed: the config validates from an empty RPC response.)
- **Flag-gated:** `UserMemoryConfig.enable_async_memory_storage` (default **False**). Off = current
  inline+blocking behavior (no change); on = decoupled. Enables safe rollout and per-agent opt-out for agents
  needing read-your-writes.

## Consequences

**Positive**
- AC#2 met: the run stops (and the indicator clears) as soon as the answer is ready; the write persists in an
  independent, Langfuse-traced run.
- Durable/replayable trigger (JetStream), bounded concurrency (single consumer), preserved memory scoping.
- Reversible via one flag; no behavior change when off.

**Negative / risks**
- **Does NOT by itself satisfy AC#1** ("memory saving completes within 5s"). Decoupling moves the ~17.5s
  write off the critical path but the write still takes as long; ≤5s requires the cost levers (graph-off +
  bounding the update-decision memory count). If AC#1 is read as "user not blocked," decoupling suffices.
- **Eventual consistency / stale-memory race:** a fast follow-up run may execute memory retrieval before the
  prior write lands. Mitigated by per-user ordering on the writer consumer and the `enable_async_memory_storage`
  opt-out for read-your-writes agents. **Launch-blocking follow-ups** before enabling in production: idempotency
  guard on `origin_run_id`, per-user ordering/debounce, writer-error alerting (no silent memory loss), and a
  claim-check for large chat histories (NATS message-size limits).
- **Narrow pre-publish crash window:** the delegation is triggered in-process on the step result; a crash
  between step completion and the publish to the writer's subject loses that one request (same window as AITL).
- **Operational:** one more long-running agent to deploy, monitor, and scale (a new `memory_writer_agent`
  service in `compose-config.yml` + template).

## Related

- `2026_07_07_disable_graph_store_for_user_memory` — the companion cost-reduction decision.
- Issue #1179.
