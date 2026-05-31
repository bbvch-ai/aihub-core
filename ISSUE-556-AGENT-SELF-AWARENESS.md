# Issue #556 — Agent Self-Awareness (Meta-Question Answering)

> **Handoff / context document.** Self-contained so a fresh Claude Code session on any machine can
> understand the feature, why it's built this way, and how to continue. Branch:
> `feat/agent-self-awareness`. Status: **implemented, verified end-to-end with a real LLM, pushed.**

---

## 1. What this feature is

Users naturally ask agents **meta questions about the agent itself**:

- _"What can you do?"_ → identity / capabilities
- _"Why did you do X just now?"_ → reasoning about its own behaviour

Before this change an agent only answered these well if a developer hand-wrote it into the system
prompt; most agents gave confusing/off-topic answers. This feature adds a **built-in, reusable
capability** so any conversational agent detects a meta question and answers it from **its own
configuration + workflow definition**, with no per-agent prompt customization.

### Scope (from the GitHub issue)

**In scope**

- A reusable **detection** step that recognises meta questions (identity / capabilities / behavior).
- A reusable **answer** step that synthesises a reply from the agent's config + workflow.
- Built-in conversational agents (**RAGAgent** "and similar") adopt it out of the box.

**Out of scope** (do NOT build these)

- Per-customer fine-tuning of meta answers.
- The agent reasoning about its own **tool catalogue**.
- Reading **recent run history** — so _"why did you do X?"_ is answered from the **static workflow
  definition** (the steps the agent _can_ run), **not** a live execution trace. This scoping is the
  key reason the issue stays small.

---

## 2. Architecture primer (read this before the diagrams)

This repo has a **custom, decentralized, event-driven workflow engine** (NOT LlamaIndex workflows).
Understanding four facts is essential:

1. **Steps are methods** decorated with `@step()` on an agent class. A step _consumes_ event
   type(s) (from its parameter type annotations) and _returns_ event type(s) (from its return
   annotation).
2. **Events drive routing — there is no explicit "next step".** When a step returns `FooEvent`, the
   dispatcher finds whichever step(s) declare `FooEvent` as input and runs them. Branching = a step
   returning a **union** (`AEvent | BEvent`) with different steps waiting on each.
3. **Preconditions** (`@precondition()` funcs passed to `@step(precondition=...)`) gate whether a
   ready step actually runs, based on config or prior events.
4. **Dependency injection**: step params like `agent_config`, `displayer`, `t` (locale),
   `memory` are auto-injected by type. LLM calls go through
   `async with llm_config.cost_reporting_llm(displayer) as llm:` for automatic cost/stream tracking.

**Two dispatcher facts that shaped the design** (verified by reading
`packages/agent/swiss_ai_hub/agent/dispatchers/agent_dispatcher.py`):

- **DI requires the _exact_ `AgentConfig` subclass.** A step annotated with the base `AgentConfig`
  is **rejected** (`agent_dispatcher.py` ~line 397). → The two new `@step` methods must live on the
  concrete agent (`RAGAgent`, with `RAGAgentConfig`), not in a generic mixin.
- **Step matching is by _exact_ event type** (`get_steps_waiting_for_event(type(event))`, exact `in`
  check). → An `LLMStopEvent` (subclass of `LLMEvent`) does **not** trigger steps waiting on
  `LLMEvent`. So the meta-answer's `LLMStopEvent` terminates cleanly **without** firing RAGAgent's
  `store_user_memory_step` / `stop_step`. No double-termination.

---

## 3. High-level flow (before → after)

A classification **gate** is inserted at the very entrance. It splits the run in two:

```
                          ┌─────────────────────────────────────────────┐
   UserMessageEvent  ──▶  │  detect_meta_question_step  (NEW — the gate)  │
                          └───────────────┬─────────────────┬─────────────┘
                                          │                 │
                      MetaQuestionDetectedEvent      NotAMetaQuestionEvent
                       (visible, control+display)    (invisible, control-only)
                                          │                 │
                                          ▼                 ▼
                       ┌──────────────────────────┐   ┌────────────────────────────┐
                       │ answer_meta_question_step │   │  existing RAG pipeline      │
                       │  → LLMStopEvent → STOP     │   │  (memory→retrieve→…→stop)  │
                       │  (NO retrieval)            │   │  (unchanged behaviour)     │
                       └──────────────────────────┘   └────────────────────────────┘
```

- **Left branch (meta):** answer from the agent's own identity + workflow, then stop. No retrieval,
  no memory, no reranking.
- **Right branch (normal):** exactly the previous behaviour.

---

## 4. The critical mechanism: the gate (why it's not a one-liner)

RAGAgent has **no single start step**. Four entry steps fire **directly** on the incoming message:
`retrieve_user_memory_step`, `retrieve_organization_memory_step`, `add_memory_to_chat_history_step`,
`limit_chat_history_step`. If detection merely ran "alongside" them, retrieval would already have
started by the time the LLM classifier returned — the branch would be cosmetic (a race condition).

**The fix** (this is the heart of the change):

1. `detect_meta_question_step` consumes **only** `UserMessageEvent` and is the sole step that fires
   on a raw chat message.
2. Each of the 4 entry steps gains an **optional** input `_clear: NotAMetaQuestionEvent | None`.
   _Optional input is what makes the dispatcher re-evaluate the step when the clear arrives_ — a
   precondition alone wouldn't, because the step must be "waiting for" that event type.
3. Each entry step's precondition is **combined** with the gate predicate
   `check_passed_meta_question_gate(start_event, clear)`:

   ```python
   clear is not None or not isinstance(start_event, UserMessageEvent)
   ```

   - Chat (`UserMessageEvent`) entry → blocked until detection emits `NotAMetaQuestionEvent`.
   - Programmatic start (`RAGStartEvent`) → bypasses detection entirely, runs immediately.

**Runtime behaviour**

| Start event | detect runs? | meta? | what happens |
|---|---|---|---|
| `UserMessageEvent` | yes | yes | `MetaQuestionDetectedEvent` → answer → stop. Entry steps never get `clear` → **never run** (no retrieval). |
| `UserMessageEvent` | yes | no | `NotAMetaQuestionEvent` → gate opens → normal pipeline runs as before. |
| `RAGStartEvent` | no | — | gate predicate true immediately → normal pipeline (detection skipped). |

The answer step emits `LLMStopEvent` (a generic terminal `StopEvent`), so the mixin needs **no
agent-specific stop event**.

---

## 5. Full RAGAgent event graph (16 steps; new bits marked ★)

```
   UserMessageEvent | RAGStartEvent
            │
            ▼
   ★ detect_meta_question_step        (consumes UserMessageEvent only)
       │                   │
  ★ MetaQuestionDetected   ★ NotAMetaQuestionEvent ───────────────┐ (the "clear" gate signal)
       │                                                          │
       ▼                                                          ▼  (optional _clear input +
   ★ answer_meta_question_step                      ┌─ retrieve_user_memory_step        combined precondition
       → LLMStopEvent → STOP                         ├─ retrieve_organization_memory_step  on all 4 entry steps)
       (no retrieval)                                ├─ add_memory_to_chat_history_step
                                                     └─ limit_chat_history_step
                                                             │
                                                  condense_standalone_question_step
                                                             │
                                                  few_shot_guard_step ──(reject)──┐
                                                             │(accept)            │
                                                       retrieve_step              │
                                                             │                    │
                                            rerank_nodes_step (if enabled)        │
                                                             │                    │
                                            order_nodes_by_documents_step         │
                                                             │                    │
                                            context_sufficient_guard_step         │
                                              │        │            │             │
                                          (accept) (reject)  (insufficient+query) │
                                              │        │            └─loops to retrieve_step
                                  limit_chat_history_with_context_step            │
                                              │                                   │
                                              ▼          ◀──────────────────────--┘
                                      respond_with_llm_step → LLMEvent
                                              │
                                      store_user_memory_step (if enabled)
                                              │
                                      stop_step → RAGSuccessStopEvent | RAGFailureStopEvent
```

The meta branch (top-left) is fully independent of the existing RAG pipeline (everything below the
gate).

---

## 6. Where everything lives (file map)

### `packages/core` — the protocol contract (events)

| File | Purpose |
|---|---|
| `swiss_ai_hub/core/events/agent/self_awareness/meta_question_detected_event.py` | `MetaQuestionDetectedEvent(ControlAndDisplayEvent)` — fields `user_query`, `category` (`identity`/`capabilities`/`behavior`), `reasoning`. **Visible** in the UI timeline. |
| `swiss_ai_hub/core/events/agent/self_awareness/not_a_meta_question_event.py` | `NotAMetaQuestionEvent(ControlEvent)` — the **invisible** internal "all-clear" gate signal (control-only, not a display event). |
| `swiss_ai_hub/core/events/agent/__init__.py` | Exports both events (3 sections: TYPE_CHECKING import, `__all__`, lazy `__getattr__` map — keep alphabetical). |
| `swiss_ai_hub/core/i18n/translations/lib/events.{en,de,fr,it}.yml` | `meta_question_detected_event.name/description` display strings. |

### `packages/agent` — all the logic

| File | Purpose |
|---|---|
| `swiss_ai_hub/agent/self_awareness/meta_question_classification.py` | `MetaQuestionClassification` result model (`is_meta_question`, `category`, `reasoning`). |
| `swiss_ai_hub/agent/self_awareness/meta_question_detector.py` | `detect_meta_question(llm, t, user_query)` — LLM classifier via `astructured_predict` with a locale-aware result factory (mirrors `context_sufficient_guard`). |
| `swiss_ai_hub/agent/self_awareness/self_awareness_step_functions.py` | `do_detect_meta_question(...) -> MetaQuestionDetectedEvent \| NotAMetaQuestionEvent`; `do_answer_meta_question(...) -> LLMStopEvent` (streams via `display_llm_stream(as_stop_step=True)`). |
| `swiss_ai_hub/agent/self_awareness/self_awareness_mixin.py` | `SelfAwarenessMixin` — shared `run_meta_question_detection`, `run_meta_question_answer`, `meta_question_workflow_summary` (introspects `self.get_steps()`, excludes the 2 self-awareness steps), and the **abstract** `self_awareness_llm_config(agent_config)` hook. |
| `swiss_ai_hub/agent/rag/preconditions.py` | `check_passed_meta_question_gate(start_event, clear)` — the gate predicate. |
| `swiss_ai_hub/agent/agents/rag_agent/rag_agent.py` | RAGAgent now `class RAGAgent(SelfAwarenessMixin, Agent)`: implements `self_awareness_llm_config` (returns `agent_config.llm`), adds `detect_meta_question_step` + `answer_meta_question_step`, and the 4 entry steps got the `_clear` input + combined gate precondition. |
| `swiss_ai_hub/agent/i18n/translations/agent/self_awareness.{en,de,fr,it}.yml` | Step names/descriptions, thoughts, and the detect + answer **prompts**. |

### `packages/api` — make the event reach the frontend

| File | Purpose |
|---|---|
| `swiss_ai_hub/api/sockets/events/server_to_user/contextualized_agent_event.py` | `MetaQuestionDetectedEvent` added to the `DisplayEvents` discriminated union. **Required** — otherwise the WebSocket silently downcasts it to `DisplayEvent` and the frontend renders the wrong type (the PR #1031 bug class). `NotAMetaQuestionEvent` is control-only and correctly NOT here. |

### `packages/web` — UI rendering

| File | Purpose |
|---|---|
| `components/Event/Display/MetaQuestionDetectedEvent.vue` | Timeline card (category `Tag` + reasoning), wraps `EventDisplayBase`. |
| `composables/event/useEventComponent.ts` | Registers `MetaQuestionDetectedEvent → EventDisplayMetaQuestionDetectedEvent`. |
| `i18n/locales/{en,de,fr,it}.yaml` | `event.metaQuestionDetected.category.{identity,capabilities,behavior}` labels. |
| `sdk/client/*.gen.ts` | **Generated** — `MetaQuestionDetectedEvent` type (from `pnpm generate-sdk`). Never hand-edit. |

---

## 7. Testing (3 tiers + the key principle)

**Principle: separate ROUTING correctness from CLASSIFICATION accuracy** — they fail for different
reasons. Routing/gating tests force the branch (never depend on a real LLM verdict); accuracy is
proven separately with the real LLM.

| Tier | Location | Infra | What it proves |
|---|---|---|---|
| 1 — unit | `packages/agent/.../self_awareness/tests/test_do_{detect,answer}_meta_question.py` | none (mocked LLM) | detect routes to the right event (incl. lookalike "what can I do with this document?" → non-meta); answer prompt is grounded in the agent's name/description/workflow. |
| 2a — gate/wiring | `.../self_awareness/tests/test_meta_question_gate.py` | none | the 4 entry steps wait on `NotAMetaQuestionEvent`; detect ignores `RAGStartEvent`; answer produces no retrieval events. |
| 2b — integration | `.../self_awareness/tests/test_rag_agent_meta_routing.py` (`@pytest.mark.self_hosted`) | **NATS + Valkey** | through the **real dispatcher**: meta Q → detected + stop + **NO `RetrieverEvent`**; normal Q → gate opens. Detection/answer are monkeypatched (no LLM/Milvus needed). |
| 3 — e2e | scenario in `.../rag_agent/tests/features/rag_agent.feature` + step defs in `test_rag_agent.py` (`self_hosted`) | full stack + **real LLM** + Milvus | real model classifies "What can you do?" as meta, answers, no retrieval. |

**Run them**

```bash
# Fast, deterministic (Tier 1 + 2a) — needs nothing extra:
cd packages/agent && uv run pytest swiss_ai_hub/agent/self_awareness/tests/test_do_detect_meta_question.py \
  swiss_ai_hub/agent/self_awareness/tests/test_do_answer_meta_question.py \
  swiss_ai_hub/agent/self_awareness/tests/test_meta_question_gate.py -q

# Integration (Tier 2b) — needs NATS + Valkey up (make up-dev):
cd packages/agent && uv run pytest swiss_ai_hub/agent/self_awareness/tests/test_rag_agent_meta_routing.py -q

# E2E (Tier 3) — needs full stack + real LLM:
cd packages/agent && uv run pytest \
  "swiss_ai_hub/agent/agents/rag_agent/tests/test_rag_agent.py::test_test_ragagent_answers_a_meta_question_about_itself_without_retrieval" -q
```

> ⚠️ **Side effect:** the existing RAGAgent `self_hosted` tests now route through detection first, so
> the real LLM must classify e.g. "What is AI?" as **non-meta**. Verified passing. It adds one extra
> LLM classification call per message (consider a fast model for the classifier).

**Last verified run (2026-05-31, this repo):** Tier 1+2 = 13 passing; Tier 3 meta scenario passed
with the real LLM; existing RAG full-pipeline scenario passed (no regression). `ruff check` clean.

---

## 8. How to run / test it in the UI (on a new machine)

Three UI surfaces show different things; the **event timeline** is the real proof.

```bash
make up-dev                                   # docker stack: NATS, Valkey, Milvus, API, LiteLLM, OpenWebUI…
cd packages/web && pnpm dev                    # Admin UI :3333
cd packages/agent && uv run python -m app.rag_agent.main   # the RAGAgent runner (long-running NATS subscriber)
```

> **Gotcha:** the agent runner is **not** hot-reloaded — restart it after every code change.

Then:

1. Admin UI (:3333) → **Agents** → create a RAGAgent profile with a knowledge base and a clear
   `name`/`description` (the meta answer is synthesised from these).
2. Chat and ask a **normal** question → full pipeline runs (control).
3. Ask **"What can you do?"** and (after a turn) **"Why did you do that?"**.
4. Lookalike negative: **"What can I do with this document?"** → must be treated as a normal task.

| Surface | Where | Pass criteria |
|---|---|---|
| Chat answer | OpenWebUI :8080 / Admin UI chat | coherent answer grounded in this profile's identity + workflow. |
| **Event timeline** ⭐ | Admin UI :3333 → Threads → the run | meta Q shows: detect thought → `MetaQuestionDetectedEvent` → `LLMStopEvent` → stop, with **NO `RetrieverEvent`**. |
| Workflow graph | Admin UI → agent detail | shows the detection branch (2 new nodes). |

**Auth gotcha on a new machine:** the chat UI needs Keycloak. The repo's `.env` requires
`OAUTH_AUTHORITY_URL='http://localhost:8180/realms/aihub'` (a fix that is **not** committed — see
§10). Without it the "Login with Keycloak" button does nothing.

---

## 9. New-machine setup (Claude Code: do these first)

```bash
git fetch && git checkout feat/agent-self-awareness
# SessionStart hook normally runs these; if not:
uv sync --all-packages
pnpm install
```

- The regenerated SDK is **committed**, so no need to re-run `pnpm generate-sdk` unless the API
  contract changes (it requires the API running at :8000).
- Per-scope guides exist: root `CLAUDE.md`, plus `packages/{core,agent,api,web}/CLAUDE.md`. Read the
  relevant one before editing that scope.

---

## 10. Known leftovers / gotchas

- **Keycloak `.env` fix is NOT in this branch.** `.env.dev` was intentionally not pushed. On a new
  machine, add `OAUTH_AUTHORITY_URL='http://localhost:8180/realms/aihub'` to `.env` or the UI login
  won't work. This deserves its **own** small PR (`fix(...)`), separate from #556.
- **Classifier cost:** one extra LLM call per chat message. Consider a cheap/fast model.
- **Milvus in WSL** occasionally restarts with `resource insufficient / streamingnode` — transient,
  not a code issue; re-run after it recovers.
- A background **API server** may be left running from a prior session (`fuser -k 8000/tcp` to stop).

---

## 11. How to extend (adopt in another agent)

Because the engine rejects base-`AgentConfig` injection, each adopting agent writes ~10 lines:

```python
class MyAgent(SelfAwarenessMixin, Agent):
    def self_awareness_llm_config(self, agent_config: MyAgentConfig) -> LLMConfig:
        return agent_config.llm  # point at this agent's LLM

    @step(name=..., description=..., icon="mdi:help-circle-outline")
    async def detect_meta_question_step(
        self, event: UserMessageEvent, agent_config: MyAgentConfig,
        displayer: EventDisplayer, t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        return await self.run_meta_question_detection(event.user_query, agent_config, displayer, t)

    @step(name=..., description=..., icon="mdi:account-voice")
    async def answer_meta_question_step(
        self, event: MetaQuestionDetectedEvent, user_message_event: UserMessageEvent,
        agent_config: MyAgentConfig, displayer: EventDisplayer, t: LocaleHandler,
    ) -> LLMStopEvent:
        return await self.run_meta_question_answer(event, user_message_event.messages, agent_config, displayer, t)
```

Then **gate that agent's entry steps**: add `_clear: NotAMetaQuestionEvent | None = None` to each
step that fires on the raw `UserMessageEvent`, and combine its precondition with
`check_passed_meta_question_gate(start_event, clear)`. Add a Tier-2 test asserting the agent's
retrieval/first-real-step does **not** run for a meta question.

---

## 12. Quick reference

- **Branch:** `feat/agent-self-awareness` (pushed to origin) · **Commit:** `feat(workflows): Add
  built-in agent self-awareness for meta questions` · **Issue:** #556 (bbvch-ai/aihub-core).
- **PR scope/type:** `feat(workflows)` · version label `minor`.
- **Open the PR:** https://github.com/bbvch-ai/aihub-core/pull/new/feat/agent-self-awareness
