# Make Agent Self-Awareness a Base-Class Capability Gated by an Opt-In Hook

## Context

Issue #556 added "self-awareness": an agent detects a meta question about itself ("what can you do?", "why did you do
X?") and answers it from its own identity + workflow definition, instead of running its normal pipeline. The original
implementation (`packages/agent/swiss_ai_hub/agent/self_awareness/`) was adopted by exactly one blueprint, `RAGAgent`,
via a `SelfAwarenessMixin` that each agent had to inherit. Adopting it required an agent to (1) inherit the mixin, (2)
implement `self_awareness_llm_config`, (3) hand-write two `@step` methods (`detect_meta_question_step`,
`answer_meta_question_step`), and (4) gate every raw `UserMessageEvent` entry step.

Users testing meta questions against other blueprints (e.g. `ExpertRAGAgent`) saw "the agent cannot detect it" — because
those blueprints simply did not have the feature. We want self-awareness available to all blueprints and on by default
for future ones, with the smallest safe per-agent cost.

Two engine constraints shaped the original mixin design:

1. **The dispatcher rejected steps annotated with the base `AgentConfig`.** `AgentDispatcher._get_parameter_value`
   (`agent_dispatcher.py`) used an identity check (`param.annotation != self.agent_config_type`), so a step on a base
   class annotated `agent_config: AgentConfig` raised at runtime. This forced the two `@step` methods onto the concrete
   agent.
2. **`step.py` imports `Agent`** for its annotation-constant strings, so any base-class module that defines `@step`
   methods (and therefore imports `step.py`) would form an `agent.py → step.py → agent.py` import cycle.

A third problem is intrinsic, not an engine artifact: **entry-step gating cannot be automated**. Each blueprint has a
different set of steps that fire directly on `UserMessageEvent`, and the gate (hold those steps until detection emits
`NotAMetaQuestionEvent`) must be applied to each of them. A dispatcher-level gate would force the engine to understand
`UserMessageEvent` (a protocol concept), and a metaclass/`__init_subclass__` rewrite would mutate `@step` function
objects shared across the MRO — silently corrupting sibling blueprints. Both were rejected.

## Decision Drivers

- **Default-on for future blueprints, zero impact on non-adopters.** A new conversational agent should get
  self-awareness with minimal code; an agent that does not want it (or is non-conversational, e.g. `RetrievalAgent`)
  must be completely unaffected — no dead workflow nodes, no spurious `UserMessageEvent` start event, no extra events.
- **Don't leak protocol knowledge into the engine.** The decentralized event-driven dispatcher
  (`packages/core`) must stay agnostic of specific event types like `UserMessageEvent`.
- **No invisible failure modes.** A half-wired self-aware agent (detection active but entry steps ungated) races its own
  pipeline and produces a double answer. This must fail loudly at test time, not silently in production.
- **Fix the real bug, minimally.** The exact-type config check was over-strict; it should always have been a
  subclass-compatible (Liskov) check.

## Decision

Self-awareness becomes a capability of the base `Agent` class, activated per blueprint by a single opt-in hook.

**1 — Relax the dispatcher config check to a subclass check.** In `agent_dispatcher.py`, replace
`if param.annotation != self.agent_config_type` with `if not issubclass(self.agent_config_type, param.annotation)`. A
step annotated with the base `AgentConfig` now receives the run's concrete config; a step requesting an unrelated
concrete config is still rejected.

**2 — Break the import cycle.** Extract the four agent-specific step annotation keys into a dependency-free module
`packages/agent/swiss_ai_hub/agent/workflow/step_annotations.py`. `step.py` imports the keys from there (and the shared
keys from `DispatchableWorkflow`) instead of from `Agent`, so a base-class module may now define `@step` methods.

**3 — Lift the steps onto the base class.** The two `@step` methods and the detection/answer helpers live on
`SelfAwarenessMixin`, annotated with the base `AgentConfig`. `Agent` inherits `SelfAwarenessMixin`, so every blueprint
has them available.

**4 — Opt-in via `self_awareness_llm_config`.** The base hook raises `NotImplementedError`. A blueprint opts in by
overriding it to return its `LLMConfig`. `Agent._is_self_aware()` detects the override
(`cls.self_awareness_llm_config is not Agent.self_awareness_llm_config`), and `Agent.get_steps()` — the single
chokepoint feeding `get_input_events`/`get_start_events`/dispatch — filters the two self-awareness steps out for
non-adopters. Non-adopting blueprints are therefore byte-for-byte unchanged in their workflow graph and runtime.

**5 — Gating stays manual, enforced by a compliance test.** Each opting-in blueprint must add
`_clear: NotAMetaQuestionEvent | None = None` to its raw `UserMessageEvent` entry steps and combine their preconditions
with `check_passed_meta_question_gate`. A parametrized test
(`self_awareness/tests/test_self_awareness_base_class.py`) introspects every production blueprint and fails if a
self-aware one has a raw chat entry step that is not gated with `NotAMetaQuestionEvent`. This is the guardrail that makes
the feature safe-by-default for future blueprints without engine magic.

`RAGAgent` is migrated to the new model: it drops the mixin from its bases (inherited via `Agent`) and the two duplicate
`@step` methods, keeping only the `self_awareness_llm_config` override and its already-gated entry steps. Adopting the
feature in other blueprints (`ExpertRAGAgent`, `LLMWrappingAgent`, …) is intentionally left to follow-up PRs — they
remain dormant until then.

## Consequences

### Positive

- Any blueprint enables self-awareness with one override; future agents scaffolded with that override get it by default.
- Non-adopting and non-conversational blueprints are completely unaffected — verified: `RetrievalAgent` does not gain
  `UserMessageEvent` as a start event.
- The dispatcher remains protocol-agnostic; no special-casing of `UserMessageEvent`.
- The race condition for half-wired adopters is caught at test time with an actionable message.
- The dispatcher check is now Liskov-correct, removing a latent over-constraint for any future base-class config
  injection.

### Trade-offs

- Entry-step gating is still per-agent boilerplate (~3 lines per entry step). This is irreducible: automating it would
  require the engine to know which steps are conversational entry points. The compliance test converts the risk of
  forgetting from a silent production bug into a loud test failure.
- Opt-in is signalled by overriding a method (`self_awareness_llm_config`) rather than a declarative flag. This is
  implicit, but it is also the exact thing the feature needs (an LLM), so it cannot be forgotten independently.
- `Agent.get_steps()` now overrides the cached `DispatchableWorkflow.get_steps()` to filter. The filter is keyed on the
  override check and applies only to `Agent` subclasses, so processes (`AgenticProcess`) are unaffected.
- Step annotation keys now live in `step_annotations.py`; `Agent` re-exposes them as class attributes for backward
  compatibility with the dispatcher's `Agent.*_ANNOTATION` reads.
