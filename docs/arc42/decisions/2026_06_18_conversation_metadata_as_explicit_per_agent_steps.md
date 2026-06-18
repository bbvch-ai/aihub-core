# Conversation Metadata (Title + Follow-up Questions) as Explicit Per-Agent Steps

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

**1 — Each adopting agent defines two thin `@step` methods**: `generate_conversation_title_step` and
`generate_follow_up_questions_step`. The bodies delegate to the shared free functions, passing `agent_config.llm`.

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

**5 — No base-class machinery.** An agent produces conversation metadata iff it defines the steps. A wiring test
(`conversation_metadata/tests/test_conversation_metadata_wiring.py`) pins the adoption set.

## Consequences

- Adoption is a few lines per agent for blueprints whose final answer is a **non-terminal** event the steps can hook on
  (`LLMEvent`). `RAGAgent` and `ExpertRAGAgent` adopt the steps this way.
- **Dispatcher stop-event constraint.** `AgentDispatcher.handle_event` cleans up and returns on stop/exception events
  **before** dispatching steps waiting for that event, so no step can consume a stop event. Blueprints whose answer is a
  stop event (`LLMWrappingAgent`, `FewShotAgent` → `LLMStopEvent`; `McpReactAgent` → `StopEvent`) therefore cannot adopt
  the steps as thin wrappers without first restructuring their terminal step to emit a non-terminal answer event plus a
  separate stop step (as `RAGAgent` already does). That restructuring changes their emitted event stream (consumed by
  bot / OpenWebUI integrations) and is deferred pending a decision with the issue owner. The wiring test asserts these
  agents do **not** define half-working metadata steps in the meantime.
- Excluded by design: non-conversational blueprints (`RetrievalAgent`) and routing/escalation front-ends that do not own
  the final answer (`NamespaceSelectionAgent`, `ExpertAskingAgent`).
- Reusing the run's LLM (rather than a dedicated cheaper task model) keeps configuration simple; a task model can be
  added later as a non-breaking option.
