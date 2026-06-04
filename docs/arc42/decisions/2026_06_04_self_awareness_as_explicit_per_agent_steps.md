# Implement Agent Self-Awareness as Explicit Per-Agent Steps

## Context

Issue #556 added "self-awareness": an agent detects a meta question about itself ("what can you do?", "why did you do
X?") and answers it from its own identity + workflow definition, instead of running its normal pipeline. We want this
available to every conversational blueprint (`RAGAgent`, `ExpertRAGAgent`, `LLMWrappingAgent`, `FewShotAgent`,
`McpReactAgent`, `NamespaceSelectionAgent`), while non-conversational ones (e.g. `RetrievalAgent`) stay unaffected.

The detection/answer logic is shared and lives as free functions: `do_detect_meta_question` and
`do_answer_meta_question` (`packages/agent/swiss_ai_hub/agent/self_awareness/`), with the meta-answer grounding text
built by `summarize_workflow_for_meta_answer`. These are agent-agnostic and reused as-is.

The open question was **how the two workflow steps that call those functions get onto each agent**. An earlier iteration
made self-awareness a base-class capability: a `SelfAwarenessMixin` was inherited by the base `Agent`, the two `@step`
methods were carried on every blueprint and filtered out of `Agent.get_steps()` for agents that did not opt in, and an
opt-in hook (`self_awareness_llm_config`) flipped the filter. Making that work required reaching into shared machinery:
the `Agent` base class, the `@step` decorator (a new `step_annotations.py` module to break an
`agent.py → step.py → agent.py` import cycle), and a relaxed `AgentDispatcher` config check so base-class steps
annotated with the base `AgentConfig` could receive the concrete config.

That approach was rejected in review for three reasons:

1. **Too invasive.** A single feature changed low-level components every agent depends on (base class, step decorator,
   dispatcher).
2. **Too implicit.** Steps stopped being visible in the agent that runs them — they were inherited and then
   conditionally filtered, against the codebase convention of keeping steps explicit.
3. **It did not save the per-agent work it was meant to.** Each adopting agent still had to override the opt-in hook and
   gate every raw `UserMessageEvent` entry step. Since every agent was touched anyway, the auto-inheritance machinery
   added complexity without removing boilerplate.

## Decision Drivers

- **Steps stay explicit and visible** in the agent that runs them, consistent with the rest of the codebase.
- **No bespoke changes to shared machinery** (base `Agent`, `@step` decorator, dispatcher) for a single feature.
- **Share the genuinely reusable logic** (detection, answer, workflow summary) as free functions — not the step wiring.
- **No invisible failure modes.** A half-wired self-aware agent (detection active but entry steps ungated) races its own
  pipeline and produces a double answer. This must fail loudly at test time.

## Decision

Self-awareness is wired **explicitly in each conversational blueprint**, not on the base class.

**1 — Each self-aware agent defines the three `@step` methods itself**: `detect_meta_question_step`,
`answer_meta_question_step`, and `stop_after_meta_answer_step`. The bodies are thin and delegate to the shared free
functions `do_detect_meta_question` / `do_answer_meta_question`, passing `agent_config.llm`. The meta answer is grounded
with `summarize_workflow_for_meta_answer(self.get_steps(), t)`.

**2 — No base-class machinery.** `Agent`, the `@step` decorator, and the `AgentDispatcher` config check are unchanged
from their pre-feature state. There is no `SelfAwarenessMixin`, no `get_steps()` filtering, no opt-in hook, and no
`step_annotations.py`. An agent is self-aware iff it defines the steps — opting in and visibility are the same thing.

**3 — The gate falls out of event dependencies.** `detect_meta_question_step` is the only step that depends on
`UserMessageEvent` alone; it emits `MetaQuestionDetectedEvent` (→ answer → stop) or `NotAMetaQuestionEvent`. Each raw
`UserMessageEvent` entry step takes `_clear: NotAMetaQuestionEvent | None = None` and combines its precondition with
`check_passed_meta_question_gate`, so the dispatcher cannot fire it until detection has cleared the message.
Programmatic starts (e.g. `RAGStartEvent`) are not `UserMessageEvent`, so the gate lets them through immediately and
detection is skipped.

**4 — Gating stays manual, enforced by a compliance test.** `self_awareness/tests/test_self_awareness_wiring.py`
introspects every production blueprint and fails if (a) a blueprint defines a partial self-awareness step set, or (b) a
self-aware blueprint has a raw chat entry step not gated with `NotAMetaQuestionEvent`. This is the guardrail that keeps
the feature safe for present and future blueprints without engine magic.

The duplicated step stubs (~25 lines per agent) are accepted as the cost of keeping steps explicit. A general
step-sharing mechanism — which would also serve genuinely repeated steps like history limiting and question condensation
— is deliberately **out of scope** and tracked as a separate issue, to be designed as its own broad concept rather than
solved ad hoc for this feature.

## Consequences

### Positive

- Steps are explicit and visible in each agent; the workflow graph reads directly from the class.
- No shared machinery (base `Agent`, `@step` decorator, dispatcher) is changed for this feature — zero blast radius for
  non-conversational blueprints.
- The reusable logic still lives in one place (the free functions); only the thin wiring is per-agent.
- The race condition for half-wired adopters is caught at test time with an actionable message.

### Trade-offs

- The three step stubs are duplicated across the six conversational blueprints. This is intentional and bounded; a
  general step-sharing mechanism is deferred to a dedicated follow-up rather than introduced bespoke here.
- Entry-step gating remains ~3 lines of per-agent boilerplate. This is irreducible without teaching the engine which
  steps are conversational entry points; the compliance test converts the risk of forgetting into a loud test failure.
