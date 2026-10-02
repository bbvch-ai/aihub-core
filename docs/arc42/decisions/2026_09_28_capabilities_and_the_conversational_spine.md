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

## Amendment 2026-09-30: the tool loop, and tools declared by the blueprint

Once web search, code execution or image generation are switched on they should become options the model weighs, not
steps that always run, and a knowledge agent should be able to retrieve first and then decide whether it needs more.
That needs a loop in which the model decides, and it has to be placeable anywhere in a blueprint and as observable as a
fixed flow (#1950).

**Decision.** The loop is a capability, `ToolLoop`, called like any other: `ToolLoop.run(history, mode)` answers with
`ToolLoopFinishedEvent`, carrying the model's reply (`ANSWER`) or the tool results as a context block for the
blueprint's own answer step (`GATHER`); `ToolLoop.route(...)` is the one-decision preset. Its steps are the loop's
stages as events: decide (`ToolEvent` per call, `ToolCallsDecidedEvent` for the join), gate (the approval policy,
`ToolApprovalRequestEvent` when the user must approve), run, and join (`ToolResultEvent`s back to the model, cut to fit
the budget). There are two kinds of tool, indistinguishable to the model:

- **Capability tools.** A capability sets `tool_name` and `tool_definition(config, locale)` and adds two adapter steps:
  one turns the `ToolCallApprovedEvent` into its ordinary request (carrying the call's `tool_call_id`), one turns its
  ordinary result into a `ToolResultEvent`. A model-chosen call therefore runs the same sub-workflow, with the same
  events and chat sources, as an explicit call. `Knowledge` is the first.
- **Function tools** are LlamaIndex tools: a `BaseToolSpec` whose listed methods are the tools (schema from their
  signatures and docstrings, the spec built per run with a `ToolContext`), or any `BaseTool`. `@ToolOptions.of(...)`
  adds what the model does not need but users do: a label, an approval summary, the approval default, the chat toggle.
  Using LlamaIndex's contract instead of our own keeps LlamaHub's tool specs usable as they are.

A blueprint declares **named tool sets** as class attributes, `research = ToolLoop.over(WebSearch, WeatherTools)`, and
runs one with `research.run(history)`. **This is the one exception to "nothing is installed by listing":** a capability
tool is installed from the declaration, because no step of the blueprint returns its request; the model does, at run
time. A tool list passed only at run time would be invisible to that, which is why the sets are declared; naming them
still gives each loop its own tools, and every loop event carries the set's name so several sets can run one after
another in a run. Validation refuses sets no step runs and one name meaning two tools. The profile (`ToolLoopFields`:
limits, disabled tools, approval rules, its form published by the runner with the blueprint's tools as options through
`Capability.published_config`) and the chat toggles of #590 narrow a set per message; with none left, gathering ends
without a model call.

Two engine rules came with it. A capability step is composed into a blueprint only when *every* required input can be
produced, not any one of them, so a tool adapter never shows in the graph of a blueprint that only calls the capability
explicitly. And the "every outcome is consumed" check covers only calls made from outside the capability, since a
model-chosen call is answered through the capability's own adapter step.

**Rejected:** tools only as executors inside the loop (a model-chosen knowledge search would have shown different, and
fewer, events than a `#` reference); a separate router capability (tool calling already picks several tools with
arguments; a one-iteration preset covers routing); looping a whole fixed flow back to its start (hard to bound and to
read; a re-runnable part becomes a tool instead).

## Amendment 2026-10-02: an open-format agent, and capabilities as its tools

The Universal Agent (#1937) is the first production blueprint built on the tool loop: it loads nothing into the prompt
up front and offers `Knowledge`, `AttachedFiles` and `Memory` as tools, so the model decides per message what it needs.

- **RAG keeps its own retrieval.** RAG is a fixed workflow that forces its steps; the Universal Agent is open-format.
  The knowledge tool any agent can offer is `Knowledge` grown to search the profile's collections
  (`KnowledgeToolFields`, RAG's own database picker) or every collection the user can read, plus the message's `#`
  references, always narrowed to what the user may read. The two retrievals may diverge, and that is accepted;
  extracting RAG's steps into a shared capability was rejected because it would loosen the workflow RAG guarantees.
- **A tool may need settings an explicit call does not.** A capability names them as `tool_config`, and validation
  requires that mixin wherever the capability sits in a tool set, so the tool settings stay off the forms of blueprints
  that only call the capability.
- **Tool definitions see the run, not just the profile.** `tool_definition` receives the run's `ToolContext`, which
  carries the user's access and the message's files and references, because what a tool offers (readable collections,
  attached files) depends on them.
- **Condensing belongs to the loop.** Only the loop sees its conversation grow between decisions, so `ToolLoop`
  condenses it in a step of its own when it outgrows the input budget, rather than leaving that to the model as a tool
  or cutting each result to a share of the room left, which starved every result after a few calls.
