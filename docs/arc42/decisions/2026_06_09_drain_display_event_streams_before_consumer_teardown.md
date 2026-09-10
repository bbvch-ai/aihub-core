# Drain Display-Event Streams Before Consumer Teardown

## Context

The API streams an agent's output to chat clients as `DisplayEvent`s (`ChunkEvent`, `ThoughtEvent`, …) over NATS,
terminated by a `StopEvent`. Four consumption sites subscribe to a thread's display events and finish on the stop: the
OpenAI-compatible SSE generator, the OpenAI JSON aggregate, the agent `_send_event` aggregate, and the native "yield all
events raw" stream used by the OpenWebUI aihub pipe.

`NCSubscriber` dispatches one `asyncio` task per message. Messages are delivered to the handler in order, but their
handler tasks run concurrently, so the stop event's task can set the stop signal before a preceding chunk's task has
enqueued it. Each consumer ended the instant the stop signal was set and the queue looked empty, dropping the in-flight
chunk(s). Short answers therefore rendered blank intermittently, and the empty assistant turn poisoned follow-up
requests (some providers reject an empty assistant message with a 400). This is a task-scheduling race in the consumer,
not NATS message reordering.

## Decision Drivers

- The fix must cover every consumer. The OpenWebUI pipe uses the native stream, not the OpenAI endpoint.
- The fix must cover all display events, not only the answer. The native stream forwards thoughts and intermediate
  events.
- No new infrastructure and no per-agent workarounds.
- A hard guarantee for the answer (whose loss blanks the turn and breaks the next request), best-effort for the rest.

## Alternatives Considered

1. **Reconcile the answer from the stop event only.** Recovers the answer text on the OpenAI endpoint, but not on the
   native stream (which has no single "answer" payload) nor for non-answer display events.

2. **Unify the producer transport.** Chunks are published to JetStream (`JSPublisher` in the displayer); the dispatcher
   publishes the terminal event's display copy over NATS core (`NCPublisher`). Display events are already
   stream-persisted (the per-class stream subject wildcards `event_type`), and the race is consumer-side task
   scheduling, so changing the publish transport does not address it.

3. **Durable-consume.** Read the run's events from the JetStream stream in sequence order up to the stop — ordered and
   lossless for a single stream. Streams are per-agent-class and JetStream forbids overlapping stream subjects, so a
   thread spanning classes via AITL delegation has events across several streams with no global order, and one consumer
   cannot span them. A per-thread stream would replace the per-class streams the dispatcher uses for load-balanced
   execution.

## Decision

Drain before teardown, with a durable backstop for the answer.

1. Shared helpers on `ChatService` (`packages/core/.../routes/chat/chat_service.py`), used by all four sites:

   - `iter_streamed_display_events()` — yields queued display events until the run has stopped and no event has surfaced
     for a grace window, so trailing handler tasks complete before the consumer ends.
   - `wait_for_stop_then_drain()` — for the collect-then-build paths: wait for the stop, drain the grace, then tear the
     subscription down.

2. `DISPLAY_STREAM_DRAIN_GRACE_SECONDS = 0.25`.

3. Backstop: the answer is recovered from the stop event's durable `output_messages` via delta reconciliation (emit only
   the un-streamed remainder) in `_resolve_final_content` (SSE) and `build_json_response_content` (JSON).

Display events are best-effort observability that must never drive workflow, so a bounded drain is acceptable for them;
the answer is the one payload that must not be lost and is guaranteed by the durable stop event.

## Consequences

### Positive

- All streaming consumers are fixed in one place, covering all display-event types and all agents, including delegated
  sub-agents whose events arrive on a different per-class stream.
- The answer cannot blank: the backstop is independent of the drain.
- No new infrastructure and no stream re-topology. The self-awareness `stop_after_meta_answer_step` /
  `MetaAnswerReadyEvent` indirection, which worked around this race, can be removed.

### Trade-offs

- Up to the grace window (0.25s) of added latency after the last token before the terminal frame.
- The drain is heuristic: a straggler slower than the grace can still drop. Acceptable for best-effort display events;
  anything that must not be lost should be a control event, not a display event.
- The producer transport inconsistency (chunks → JetStream, terminal display copy → NATS core) and the inaccurate
  "display events are ephemeral" framing in scope docs are left as a separate follow-up; display events are
  stream-persisted.
