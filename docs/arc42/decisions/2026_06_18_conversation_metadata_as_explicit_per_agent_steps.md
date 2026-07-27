# Conversation Metadata (Title + Follow-up Questions) as Explicit Per-Agent Steps

::: warning Update (2026-07-24, issue #87)
For the split agents (`RAGAgent`, `ExpertRAGAgent`) the two metadata events are **no longer both fan-out `@step`s on the
terminal `LLMEvent`**. Hanging both off the answer event made them run concurrently with the stop step, so their display
events could be emitted after the StopEvent teardown (dropped/reordered title, ERROR-logged failures) — the production
regression tracked in issue #87. They are now wired by dependency:

- **Title** — an early fan-out `@step` anchored on a **pre-answer** event (`LimitChatHistoryEvent`). The title only
  needs the conversation topic, not the answer, so it runs in parallel with retrieval/answer and emits before the stop
  event. This realises the "Inline ordering is stronger than fan-out" follow-up flagged in Consequences below, without
  serialising the title behind the answer.
- **Follow-ups** — generated **inline** in the terminal step before the stop event, exactly like the inline agents. They
  are grounded on the latest answer, so they cannot start earlier.

The shared generators are unchanged; only the per-agent wiring and the best-effort wrappers (now WARNING, not ERROR)
were touched. The rest of this ADR stands.
:::

## Context

Issue #1073 makes agents produce conversation metadata — a chat **title** and suggested **follow-up questions** — as a
first-class part of their workflow, instead of leaving it to the surrounding chat UI (OpenWebUI's task model). The agent
has the most context about what just happened in the conversation, so it should generate this and emit it as protocol
events. The OpenWebUI integration that consumes the events (and produces deterministic tags from the agent name/class)
is the companion issue #1047.

Two metadata outputs are LLM-generated here: the title and the follow-up questions. Tags are explicitly **out of scope**
— they are deterministic and owned by the pipeline in #1047, so the SDK generates no tags.

The generation logic is shared and lives as free functions: `do_generate_title` and `do_generate_follow_up_questions`
(`packages/agent/swiss_ai_hub/agent/conversation_metadata/`). They drive an LLM over the conversation via
`astructured_predict`, reuse the run's `agent_config.llm`, and emit `ConversationTitleEvent` / `FollowUpQuestionsEvent`
through the injected `EventDisplayer`. The open question was **how the steps that call those functions get onto each
agent**.

## Decision Drivers

- **Consistency with self-awareness.** This is the same shape of problem already solved by ADR
  `2026_06_04_self_awareness_as_explicit_per_agent_steps`: shared free functions, per-agent thin `@step` wrappers, no
  base-class mixin.
- **Steps stay explicit and visible** in the agent that runs them.
- **No bespoke changes to shared machinery** (base `Agent`, `@step` decorator, dispatcher) for a single feature.
- **A stable, single title per conversation** that does not churn each turn, and that survives across runs.
- **No invisible failure modes.** A conversational agent that should produce metadata but silently does not (or an
  excluded agent that silently gains it) must fail at test time.

## Decision

Conversation metadata is wired **explicitly in each adopting blueprint**, mirroring self-awareness exactly.

**1 — Each adopting agent invokes the two shared generators, in one of two shapes depending on its answer event.**

- **Fan-out `@step` wrappers** — for agents whose final answer is a *non-terminal* `LLMEvent`, two thin `@step` methods
  (`generate_conversation_title_step`, `generate_follow_up_questions_step`) hook on it and delegate to the shared
  functions. Used by `RAGAgent` and `ExpertRAGAgent`.
- **Inline in the terminal step** — for agents whose answer *is* a stop event (`LLMStopEvent` / `StopEvent`), the
  generators are `await`ed (via `asyncio.gather`) **inside the terminal step, before returning the stop event**. Used by
  `LLMWrappingAgent`, `FewShotAgent`, `McpReactAgent`. This is necessary because the dispatcher returns on stop events
  before dispatching steps waiting on them (see Consequences), so a separate `@step` could never run.

**2 — Display events, not control events.** Both metadata events subclass `DisplayEvent` and are emitted via
`EventDisplayer.display_event`. They never gate the workflow. Each is registered in the WebSocket `DisplayEvents`
discriminated union so it is not silently downcast on serialization.

**3 — Title is generated once per thread; follow-ups regenerate every turn.** `do_generate_title` gates on a
`ThreadContext` flag (`title_generated`, no TTL, persists across runs): the first turn that yields a determinable title
sets the flag and emits the event; later turns short-circuit without an LLM call. A turn with no identifiable topic
(greetings, small talk) returns `null` and leaves the flag unset so a later turn retries. Follow-up questions are not
gated. Cross-agent locking for parallel runs in one thread is out of scope (last-writer-wins on the title).

**4 — The title is persisted onto the thread.** `ThreadEntity.update_thread_name` is called from the API streaming
bridge (`AgentService.send_agent_input_event_stream`) and the non-streaming JSON path (`ChatService`) when a
`ConversationTitleEvent` is observed on the thread's display events, replacing the hardcoded `"chat"` name. The admin
thread list then shows the generated title.

**5 — No base-class machinery.** An agent produces conversation metadata iff it wires in the generators (fan-out or
inline). A wiring test (`conversation_metadata/tests/test_conversation_metadata_wiring.py`) pins the adoption set: the
five adopting agents reference both generators, the two fan-out agents additionally define the `@step` wrappers, and the
excluded agents reference neither.

## Consequences

- **Dispatcher stop-event constraint** is the reason for the two shapes. `AgentDispatcher.handle_event` cleans up and
  returns on stop/exception events **before** dispatching steps waiting for that event, so no `@step` can consume a stop
  event. Agents whose answer is a non-terminal `LLMEvent` (`RAGAgent`, `ExpertRAGAgent`) use fan-out steps; agents whose
  answer is a stop event (`LLMWrappingAgent`, `FewShotAgent`, `McpReactAgent`) generate inline before returning it.
- **Inline ordering is stronger than fan-out.** Inline emits the metadata display events *during* the step body, so they
  are on the wire **before** the stop event is published and before teardown — no dependence on the
  drain-before-teardown ADR. The fan-out path runs the metadata steps concurrently with the stop step, so a metadata
  event can be emitted *after* the `StopEvent`; for the title this is a race with the API observer that updates the
  thread name (mitigated, not eliminated, by the drain grace). Unifying the two fan-out agents onto inline would remove
  that race at the cost of serializing the metadata calls ahead of the stop (post-answer latency, since the answer has
  already streamed); deferred as a follow-up.
- **Metadata generation is best-effort in both shapes**, because it is a non-essential post-answer enhancement that must
  never fail the user's answer. Inline agents call the shared `generate_conversation_metadata` helper, which runs the
  two generators with `asyncio.gather(return_exceptions=True)` and logs (not raises) any failure. Fan-out steps set
  `stop_on_error=False`, so a generator failure is logged and produces no event instead of an `ExceptionEvent`. Either
  way a title/follow-up failure degrades to "no metadata this turn"; the answer and its terminal stop event are
  untouched.
- Excluded by design: non-conversational blueprints (`RetrievalAgent`) and routing/escalation front-ends that do not own
  the final answer (`NamespaceSelectionAgent`, `ExpertAskingAgent`).
- The self-awareness meta-answer branch (`answer_meta_question_step` → `LLMStopEvent`) also produces no metadata, for
  the same stop-event reason; left as-is so meta-only conversations keep the default thread name.
- Reusing the run's LLM (rather than a dedicated cheaper task model) keeps configuration simple; a task model can be
  added later as a non-breaking option.
