# Chat History Reconstruction Projects Client-Visible Displays

## Context

A client of the OpenAI-compatible endpoint sent follow-up requests with `metadata.reconstruct_history=true` and received
HTTP 500. The thread contained a delegated retrieval agent whose response event (`RetrievalAgentInTheLoopResponseEvent`)
is a custom class the API process does not import. Reconstruction deserialized every persisted display event through
`ContextualizedAgentEvent`, whose discriminated union is designed for the UI event timeline: an unknown nested event
fell back to its closest known parent (`RetrieverEvent`), the enclosing AITL envelope then failed its required
`StopEvent` field, and the `ValidationError` escaped as a 500 before the target agent was ever dispatched.

The same coupling caused silent correctness defects even when it did not crash:

- History was scoped only by `thread_id`. AITL delegation defaults to sharing the thread while `share_display_id`
  independently controls whether delegated output shares the client-visible surface, so chunks from hidden nested runs
  were concatenated into reconstructed transcripts.
- HITL questions and answers were each duplicated into both user and assistant roles.
- Every API replica runs an `AgentEventPersister` on a fan-out NATS Core subscription, so duplicate deliveries
  duplicated reconstructed turns.
- Trailing chunk loss from the stop-vs-chunk delivery race was unrecoverable: history ignored stop events, unlike the
  live response path, which falls back to `StopEvent.output_messages`.

## Decision Drivers

- **Reconstruction must survive arbitrary agent-specific events**\
  Any deployed agent may define custom event classes; the API cannot be required to import them to read conversation
  history. Unknown events must be excluded before deserialization, not interpreted.
- **The visibility boundary is the display surface, not agent identity**\
  The live OpenAI subscription listens to all agents within one `thread_id` + `display_id`. Issue #1283 explicitly
  rejected filtering chunks to the selected agent because it suppresses intentionally visible delegated output. History
  must mirror the live boundary.
- **Chat projection must not depend on the UI event union**\
  `ContextualizedAgentEvent` requires every displayable event type known to the API package; chat history needs only a
  small, stable set of fields (`messages`, `content`, `question`, `response`, `output_messages`).
- **Reads must be correct under duplicate writes**\
  Event-persistence duplication is owned by #1203 (single-instance `aihub-daemon`); until then, reconstruction must
  deduplicate on read.
- **No migration weight without measured need**\
  Existing persisted events and indexes must serve the new query; no new collection, index, or backfill.

## Decision

Chat history reconstruction is a two-stage projection of persisted display events:

- `PersistedAgentEventEntity.conversation_events_for_thread` first resolves client-visible displays from persisted
  `UserAgent` user/HITL marker events (exact `$in` array membership on `event_parents`, not regex `__contains`), then
  returns only the projectable event families (`UserMessageEvent`, `HumanInTheLoopResponseEvent`, `ChunkEvent`,
  `HumanInTheLoopRequestEvent`, `StopEvent`) on those displays. Threads without a visible marker fail closed to empty
  history with a warning.
- A pure projector (`conversation_history_projector.py`) maps raw persisted fields directly — validating only the last
  `ChatMessage` of a user event (normalizing legacy byte-list audio/image payloads) and the documented scalar fields of
  the other families — without deserializing event classes. HITL questions project as assistant messages, answers as
  user messages, once. Consecutive same-role text on one display merges. Malformed relevant events are skipped with
  metadata-only warnings; unrelated events are never deserialized.
- Terminal recovery mirrors the live prefix rule and is gated on the request's primary agent identity (`agent_class` +
  `agent_id` passed by both assistant paths), so a nested agent's stop can never supply the top-level answer suffix.
  `ThreadService.thread_as_message_history` accepts the identity as optional keyword arguments, preserving its
  one-argument contract.
- Deliveries are deduplicated by full topic identity (agent, thread, display, run, event type/name/id) and ordered by
  `created_at` with `event_id` as tie-breaker; ordering metadata that is missing or malformed skips the event rather
  than corrupting the sort.

## Consequences

### Positive

- Unknown custom nested events can no longer break history reconstruction; they remain untouched in the audit store.
- Reconstructed transcripts match what the client actually saw: hidden nested output is excluded at any delegation
  depth, shared-display delegation is retained (#1283 behavior preserved), and recursive same-agent delegation needs no
  depth inference.
- Both query stages use the existing `thread_id_1_event_type_1_event_parents_1` index (verified via explain); no schema,
  index, or configuration change.
- Any API replica produces identical history from the shared event store, so reads are replica-safe.

### Trade-offs

- Threads whose persisted events predate `UserAgent` markers reconstruct as empty (fail closed). Deploys onto long-lived
  stores should verify legacy threads carry markers.
- Eventual consistency remains: a request arriving before the previous run's display events are persisted reads
  incomplete history. Strict read-after-write would require a persistence barrier and is out of scope.
- Primary terminal recovery is unavailable through the unmounted thread-history endpoint, which has no selected agent
  identity.
- Read-side deduplication neutralizes duplicate rows but does not reduce them; write-side duplication remains owned by
  #1203, and overall horizontal API scaling stays gated on that issue.
