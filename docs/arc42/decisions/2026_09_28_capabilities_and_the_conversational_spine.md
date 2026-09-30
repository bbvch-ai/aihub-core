# Share Chat Blueprint Steps Through Capabilities Called With Events

Supersedes `2026_06_04_self_awareness_as_explicit_per_agent_steps` and
`2026_06_18_conversation_metadata_as_explicit_per_agent_steps`.

## Context

Every conversational blueprint repeats the same steps around its own core: the meta-question gate and answer, user and
organization memory, the join that puts retrieved context into the chat history, the conversation title and follow-up
questions, and the stop. ADR `2026_06_04` chose to copy the thin `@step` wrappers into each blueprint and share only the
free functions behind them, deliberately deferring a general step-sharing mechanism. ADR `2026_06_18` did the same for
conversation metadata, in two forms depending on whether a blueprint's answer was terminal.

That cost grew with every capability times every blueprint. `ExpertRAGAgent` copied `RAGAgent`'s entire pipeline (963
lines) rather than extend it. Issue #1577 asked for the memory steps in three more blueprints, and #1568, #1569 and
#1935 each planned "shared step functions, packaged like the RAG steps, adopted by every conversational blueprint". Each
adoption also grew a hand-maintained wiring test with per-blueprint exception lists.

Two engine facts bounded the options. Steps are matched to events by exact event class. The dispatcher only injected a
config parameter annotated with the blueprint's exact config class, so nothing but free functions could be shared.

## Decision

**1 — A capability is a sub-workflow called with events**, the way `HumanInTheLoop` and `AgentInTheLoop` are used today.
A step returns the capability's request event, built with a typed helper on the capability class; a later step picks the
result up by declaring the result event as a parameter. Fan-out is returning a list of requests; waiting is declaring
parameters. Requests are named in the imperative (`ContextualizeConversationEvent`, `RecallMemoryEvent`) and results in
the past participle (`ConversationContextualizedEvent`, `MemoryRecalledEvent`), and the capability class exposes them
under scoped names (`Conversation.Contextualized`, `Memory.Recalled`, and requests with a `Request` suffix such as
`Memory.RecallRequest`, so no name differs from its call helper only in case) next to the lowercase call helpers, so a
blueprint's annotations say which sub-workflow an event belongs to even though the composed workflow is flat. A
capability's steps are `@staticmethod`s decorated with `@step` that take the blueprint instance first, so the dispatcher
invokes them exactly as it invokes a method.

**2 — Nothing is installed by listing.** Returning a capability's request from a step is what composes that capability's
steps into `Agent.get_steps()`, and only the steps reachable from the blueprint's own events are composed, so a call a
blueprint never makes is pruned from its graph. A capability declares `calls` (request → every outcome the call can end
in, so a call may answer with one of several events or end the run) and `required_config`, the form mixin its steps are
annotated with (`ConversationFields`, `MemoryFields`). The blueprint's config lists the mixins of the capabilities it
calls as bases before `AgentConfig`; the dispatcher injects the run's concrete config into any parameter annotated with
one of its bases. Nested `StepConfig` fields were considered and rejected for now because they change the stored profile
shape.

**3 — Only two calls keep a sub-graph behind them**, because a blueprint must not be able to get them wrong:

- `Conversation.contextualize(history, message)` inspects the message for a meta question and answers it if it is one
  (ending the run), derives the query the turn is answered for (verbatim, or condensed when the profile's
  `condense_question` is on), and titles the thread. The gate lives inside the call: nothing downstream of it exists
  until inspection has cleared the message, so detection can never race the pipeline. A programmatic start passes no
  message and skips inspection.
- `Conversation.complete(answer, stop)` generates the follow-up questions and ends the run with the given stop event, or
  an `LLMStopEvent` carrying the answer. `RAGAgent` passes its outcome events here.

`Conversation.compose(history, blocks)` merges context blocks into the history in the order the blueprint gives, within
the input budget, and its result `ContextComposedEvent` is displayed as what the model saw. `Memory.recall(query)` is
answered with `MemoryRecalledEvent`, one block per scope, empty when memory is off or the run has no identity, so a
waiting step never hangs. `Memory.remember(...)` builds the memory-storage delegation directly, with no step behind it:
returned from the same step as the completion and ahead of it, the list order is what guarantees the delegation is
published before the run tears down (ADR `2026_09_11`). There are no barriers, no counted joins and no injected
blueprint class; the blueprint's declared parameters are the waits.

**4 — Validation replaces the wiring tests.** `Agent.validate_workflow`, run by `AgentRunner` with the config it was
handed, refuses a composed workflow that would stall or crash: a step waiting for an event nothing produces, a call
whose result none of the blueprint's own steps consumes, two steps sharing a name, or a config missing a required mixin.
Each message names the obligation. Each capability's sub-graph is tested once through the test runner with a stub
blueprint; blueprints test only their own steps.

**5 — One refusal type.** An input the turn cannot be answered for, too large for the model or a blank condensation,
ends in a core `RefusalStopEvent` with a `RefusalReason`, shared by every conversational blueprint.
`RAGFailureStopEvent` keeps the retrieval outcomes only.

**6 — Every conversational blueprint runs this way.** `RAGAgent`, `ExpertRAGAgent` (a `RAGAgent` subclass adding the
expert steps and overriding two), `LLMWrappingAgent`, `FewShotAgent` and `McpReactAgent` (whose ReAct loop hands its
final answer to the completion). The explicit per-blueprint wiring of the two superseded ADRs is gone, as are the copied
memory preconditions.

**7 — Two engine changes were needed.** The dispatcher hands an optional list parameter (`list[Event] | None`) every
matching event, which it silently did not before; and the event dumper serializes chat messages nested more than one
list deep, which `ComposeContextEvent.blocks` is the first payload to need. Both are general fixes, not
capability-specific hooks.

### Considered and rejected

- **Plug-ins installed by config, with counted barriers.** The first cut of this work composed enrichers and post-answer
  hooks implicitly, with a join and a stop that counted how many were installed. It was rejected as too implicit:
  reading a blueprint did not show which capabilities ran or in which order their context reached the model, and it made
  per-message choice of capabilities (the super-agent, #1937; OpenWebUI toggles, #590) impossible. Explicit calls keep
  the per-agent code proportional to what the blueprint genuinely decides and let a step return whichever requests fit
  the message.
- **Role decorators on hand-over steps** (`@Conversation.entry`). Rejected because a decorated step still had to
  construct the hand-over event it was annotated with, so the decorator explained nothing the event type did not.

## Consequences

### Positive

- A blueprint reads as what it does: every capability it uses is a call in its own code, the order of context blocks is
  the `blocks=[...]` list, and what runs after the answer is the list it returns.
- `RAGAgent` went from 774 lines and nine preconditions to under 400 and two; `ExpertRAGAgent` from 963 to under 400;
  `LLMWrappingAgent` has four steps. The hand-maintained wiring tests are gone.
- `LLMWrappingAgent`, `FewShotAgent` and `McpReactAgent` gained memory, and `McpReactAgent` self-awareness, by one call
  and one mixin each.
- Web fetch (#1569), attached files (#1935) and web search (#1568) arrive as further calls whose results a blueprint
  passes to `Conversation.compose`; a loop agent can return whichever requests the message needs.
- Every way a workflow can stall is a startup error that names the missing obligation.

### Trade-offs

- Adding a capability to five blueprints means five one-line additions in a fan-out and one parameter on each answer
  step. That is proportional to what each blueprint decides and is what a reviewer wants to see.
- `ContextualizeConversationEvent` carries the limited history, so it lands in JetStream and the event store once more
  than the answer does, the same size as the old `LimitChatHistoryEvent`.
- Stop event types now travel inside `CompleteConversationEvent`, so discovery lists `StopEvent` rather than a
  blueprint's specific outcome events; the emitted stop event is unchanged.
- `FewShotAgent` condenses before its suitability guard rather than after, one extra task-model call on the reject path,
  because the query is what memory is recalled with.
- New LLM wrapping, few-shot and MCP profiles get memory on by default; `number_of_input_tokens` defaults to 128000 on
  all of them.
