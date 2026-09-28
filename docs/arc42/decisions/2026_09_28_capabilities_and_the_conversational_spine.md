# Share Chat Blueprint Steps Through Capabilities and a Conversational Spine

Supersedes `2026_06_04_self_awareness_as_explicit_per_agent_steps` and
`2026_06_18_conversation_metadata_as_explicit_per_agent_steps`.

## Context

Every conversational blueprint repeats the same steps around its own core: the meta-question gate and answer, user
and organization memory, the join that puts retrieved context into the chat history, the conversation title and
follow-up questions, and the stop. ADR `2026_06_04` chose to copy the thin `@step` wrappers into each blueprint and
share only the free functions behind them, deliberately deferring a general step-sharing mechanism. ADR `2026_06_18`
did the same for conversation metadata, in two forms depending on whether a blueprint's answer was terminal.

That cost grew with every capability times every blueprint. `ExpertRAGAgent` copied `RAGAgent`'s entire pipeline
(963 lines) rather than extend it. Issue #1577 asked for the memory steps in three more blueprints, and #1568, #1569
and #1935 each planned "shared step functions, packaged like the RAG steps, adopted by every conversational
blueprint". Each adoption also grew a hand-maintained wiring test with per-blueprint exception lists.

Two engine facts bounded the options. Steps are matched to events by exact event class. The dispatcher only injected
a config parameter annotated with the blueprint's exact config class, so nothing but free functions could be shared.

## Decision Drivers

- Adding a capability to a blueprint must be one visible declaration, not a copy of steps, preconditions, config
  fields, form wiring and tests.
- The gate before the pipeline and the join of retrieved context are the boilerplate that grows with every
  capability; they must be written once.
- Steps stay visible: the workflow graph, discovery and the meta-question summary must read one flat step set from
  the class, with no hidden inheritance or filtering.
- A capability must be consumable both as fixed workflow steps (the specialised blueprints) and, later, as a tool
  in an agentic loop (#1950, #1937), so its logic stays in narrow functions.
- No stored-profile migration.

## Decision

**1 — Capabilities.** A capability is a class bundling `@staticmethod` steps decorated with `@step`, which take the
blueprint instance as their first parameter so the dispatcher invokes them exactly like methods. A blueprint installs
capabilities by listing them: `capabilities = (ConversationCapability, SelfAwarenessCapability, MemoryCapability)`.
`Agent.get_steps()` returns the class's own steps plus every step the installed capabilities contribute, as one flat
set, and refuses duplicate step names. A capability may adapt to the blueprint it is installed on (`steps_for`),
which is how the spine withholds a default the blueprint already provides.

**2 — The conversational spine** (`ConversationCapability`) owns everything between the blueprint's entry step and
its answer pipeline, and after the answer:

- `derive_query_step` is the first step past the entry point and **the meta-question gate**: it depends on
  `NotAMetaQuestionEvent`, so gating one step gates every enricher and the whole pipeline. It emits
  `ConversationQueryEvent`, the last user message or the condensed question when the profile's `condense_question`
  is on, plus the display-facing `StandaloneQuestionCondenserEvent` in that case.
- `assemble_context_step` is **the enrichment join**. Every enricher a blueprint installs emits exactly one
  `ContextBlockEvent` per turn, empty when it has nothing, so the join waits for as many blocks as the blueprint has
  enrichers without knowing which are switched on. It merges the blocks behind the leading system messages within
  the input budget and emits `EnrichedChatHistoryEvent`, which the blueprint's answer pipeline consumes and which is
  displayed, since it is exactly what the model saw.
- `stop_step` is the default stop: it waits for one `AnswerPostProcessedEvent` per installed post-answer hook, then
  turns the non-terminal `LLMEvent` into `LLMStopEvent` with the follow-up questions generated inline. A blueprint
  whose stop event carries more than the answer (`RAGAgent` and its outcome events) keeps its own stop step and
  reuses the spine's barrier precondition; the spine withholds the default then.
- `open_gate_step` is withheld when `SelfAwarenessCapability` is installed, whose detection is the gate.
- The title is generated on the query event, past the gate and before the answer.

Preconditions on the spine take `blueprint: type[Agent]`, which the dispatcher injects, to count the installed
enrichers and hooks.

**3 — Capability config as form mixins.** Each capability ships its fields as a plain `Form` mixin
(`ConversationFields`, `MemoryFields`) and names it as `required_config`. A blueprint's config lists the mixins of
the capabilities it installs as bases before `AgentConfig`, so any combination composes and stored profiles keep
their shape. The dispatcher injects the run's concrete config into any parameter annotated with one of its bases;
a step asks for `AgentConfig` when it needs the identity and for the mixin when it needs the capability's fields.
`AgentRunner` refuses to start a blueprint whose config lacks a required mixin. Nested `StepConfig` fields were
considered and rejected for now because they change the stored profile shape and need a union-aware lookup.

**4 — One refusal type.** An input the turn cannot be answered for, too large for the model or a blank
condensation, ends in a core `RefusalStopEvent` with a `RefusalReason`, shared by every conversational blueprint.
`RAGFailureStopEvent` keeps the retrieval outcomes only.

**5 — Every conversational blueprint runs on the spine.** `RAGAgent`, `ExpertRAGAgent` (now a `RAGAgent`
subclass adding six expert steps and overriding three), `LLMWrappingAgent`, `FewShotAgent` and `McpReactAgent`
(whose ReAct loop ends in a non-terminal `LLMEvent`). Their entry step turns the start event into a
`LimitChatHistoryEvent`; their core turns the `EnrichedChatHistoryEvent` into an `LLMEvent`. The explicit
per-blueprint wiring of the two superseded ADRs is gone, as are the copied memory preconditions.

**6 — Two engine changes were needed.** The dispatcher hands an optional list parameter (`list[Event] | None`)
every matching event, which it silently did not before; and it injects the blueprint class. Both are general
fixes, not capability-specific hooks.

## Consequences

### Positive

- Installing a capability is one line on the class and one mixin on the config. `LLMWrappingAgent` gained memory
  and `McpReactAgent` gained self-awareness and memory by listing them.
- `RAGAgent` went from 774 to 347 lines and nine preconditions to two; `ExpertRAGAgent` from 963 to 368;
  `LLMWrappingAgent` from 261 to 164. The wiring tests lost their per-blueprint exception lists.
- Web fetch (#1569), attached files (#1935) and web search (#1568) arrive as enrichers emitting `ContextBlockEvent`
  plus their own display event; the join and the blueprints do not change.
- The workflow graph still derives from the class, and the composition contract is pinned by
  `capabilities/tests/test_capability_composition.py` and an end-to-end run of every blueprint through the real
  dispatcher.

### Trade-offs

- A disabled enricher still runs a trivial step and emits an empty block, one dispatch per turn.
- The spine's defaults are a rule ("contributed unless the blueprint provides it") rather than a declaration. It is
  bounded to two steps and visible in the graph; a third default should become an explicit declaration.
- The entry step runs ungated, concurrently with meta-question detection. It is cheap and side-effect free, and
  the gate on the query step holds everything after it.
- A programmatic start that narrows a capability's scope (the organization-memory namespaces on `RAGStartEvent`)
  hands it over through a documented run-context key, since a capability cannot import a blueprint's start event.
  A second such case should become a typed scope on the entry event.
- `FewShotAgent` now condenses before its suitability guard rather than after, one extra task-model call on the
  reject path, because the enrichers need the query first.
- New LLM wrapping, few-shot and MCP profiles get memory on by default; `number_of_input_tokens` defaults to
  128000 on all of them.
