---
title: Capabilities and Tools
description: Reuse the steps every chat agent needs through capabilities, and let the model choose tools with the tool loop.
---

# Capabilities and Tools

Every conversational agent repeats the same work: derive a query from the history, recall memory, read attached files,
search referenced knowledge, put it all in front of the model, and finish with a title and follow-up questions. The SDK
packages this as **capabilities** that a blueprint calls with events. Because a capability is called, not installed,
reading a blueprint shows which context reaches the model and what runs after the answer.

## Calling a capability

A capability is called the way human-in-the-loop requests are: a step returns the capability's **request event**, built
with a typed helper, and a later step declares the **result event** as a parameter. Returning a list fans out, and
declaring several parameters waits for all of them.

| Capability      | Call                                                      | Result                          | Config mixin         |
| --------------- | --------------------------------------------------------- | ------------------------------- | -------------------- |
| `Conversation`  | `contextualize(history, message)`                         | `Conversation.Contextualized`   | `ConversationFields` |
| `Conversation`  | `compose(history, blocks)`                                | `Conversation.Composed`         | `ConversationFields` |
| `Conversation`  | `complete(answer, stop=None)`                             | ends the run                    | `ConversationFields` |
| `Memory`        | `recall(query)`; `remember(...)` stores in the background | `Memory.Recalled`               | `MemoryFields`       |
| `AttachedFiles` | `read(files, history, query)`                             | `AttachedFiles.Contents`        | `AttachedFilesFields` |
| `Knowledge`     | `search(references, query)`                               | `Knowledge.Searched`            | `KnowledgeFields`    |

The blueprint's config lists the mixins of the capabilities it calls before `AgentConfig`, and the dispatcher injects
the run's config into any step parameter annotated with one. The chat blueprints in
`packages/agent/swiss_ai_hub/agent/agents/llm_wrapping_agent/` are the smallest complete example: one step limits and
contextualizes, one gathers memory, files and referenced knowledge in parallel, one composes, one answers and completes.

What the calls do for you:

- **`contextualize`** runs the meta-question check, derives the query the turn is answered for and titles the thread.
- **`compose`** puts the gathered blocks behind the leading system messages, within the input budget, and hands the
  model **one** system message. Older turns give way before the blocks do. The event history shows the result as what
  the model saw.
- **`complete`** generates follow-up questions and ends the run with a stop event. A stop event passed to it travels
  inside the request, so declare it in `Agent.completion_stops`, or the REST response model and workflow graph show a
  bare `StopEvent`.
- **Citations.** Documents a capability hands to the model carry a short stable id the model cites as `[s3f9a1c]`; the
  Open WebUI integration turns the ids into numbered source chips.

### Validation

A workflow is validated when the runner starts. It refuses a step that waits for an event nobody produces, a call whose
result no step consumes, duplicate step names, and a config missing a required mixin, and the message names the
obligation. A capability that is called but has nothing to do (memory switched off, no files attached) still answers
with an empty result, so waits never hang.

### Who is asking

A step that declares `AccessChecker | None` receives the asking user's access rules, or `None` for a run without a user
(scheduled or mail-triggered). Use it to narrow retrieval to what the user may read; the knowledge capability and the
RAG blueprints do.

### Chat features

Web Search, Code Interpreter and Image Generation toggles in Open WebUI arrive as `UserMessageEvent.requested_features`
(the OpenAI-compatible API accepts the same list in `metadata.features`). A capability declares the feature it serves,
and an agent only shows, and is only sent, features its capabilities support. `RequestedFeatures.contains(...)` lets a
step or precondition check one.

## The tool loop

When the path to an answer cannot be written as steps, the `ToolLoop` capability lets the model decide which tools to
use, runs them, and lets it decide again until it can answer. A blueprint declares tool sets as class attributes and
starts a loop wherever it fits.

```python
class AnsweringToolLoopAgent(Agent):
    tools = ToolLoop.over(Knowledge, ClockTools)

    @step()
    async def loop_step(self, ctx: Conversation.Contextualized) -> ToolLoop.RunRequest:
        return AnsweringToolLoopAgent.tools.run(ctx.history)

    @step()
    async def complete_step(self, finished: ToolLoop.Finished) -> Conversation.CompleteRequest:
        return Conversation.complete(answer=finished.answer)
```

`tools.run(history)` ends with the model's reply (`ANSWER` mode). `tools.route(history)` makes one gathering decision and
returns the results as a context block for the blueprint's own answer. Every event of a loop carries the set's name, so
a blueprint can run several sets in a row.

### Three kinds of tool

All look the same to the model.

- **Capability tools.** A capability that offers itself as a tool, such as `Knowledge` (which searches the profile's
  `tool_collections`). A model-chosen call produces the same events and citation chips as an explicit one.
- **LlamaIndex tool specs.** A `BaseToolSpec` subclass whose listed methods are the tools; the schema is read from
  signatures and docstrings, so LlamaHub specs work unchanged. It is built per run with a `ToolContext` (config, user,
  locale, displayer).
- **LlamaIndex tools.** Any `BaseTool`, for example `FunctionTool.from_defaults(...)`.

A tool that raises returns an error result to the model instead of ending the run. `@ToolOptions.of(...)` adds what
users need and the model does not: a localized label, an approval summary, an approval default, and the chat toggle the
tool needs.

### What stays under the admin's control

The runner publishes the loop's form with the blueprint's tools as options, so profiles get limits (decisions and tool
calls), a list of disabled tools, and per-tool approvals (never, every call, once per answer, once per conversation).
Approval is asked as a yes/no confirmation in the chat; a declined tool is withdrawn for the rest of the answer. Only
tools actually offered can run: a call to a disabled tool, a tool whose toggle is off, or a name the model made up goes
back to it as an unknown tool. At a limit the model answers without tools and a notice says it stopped early. When the
conversation and the tool schemas outgrow the input budget, earlier results and turns are condensed in place and the
chat shows a status.

### Events

Each stage is an event, so the loop is as inspectable as any workflow: `ToolCallsDecidedEvent` with a `ToolEvent` per
call, `ToolApprovalRequestEvent` and `ToolApprovalResponseEvent`, `ToolResultEvent`, `ToolLoopIterationEvent` per round
and `ToolLoopStatusEvent` while the model decides. The playground at
`packages/agent/playground/minimal_workflow/tool_loop_workflow/` shows an answering and a gathering agent side by side.

## Free-form map fields in events

Start, stop and human-in-the-loop events are rebuilt from the JSON Schema an agent announces, so the REST endpoints
validate them. Map fields such as `dict[str, bool]` are preserved, including nested ones; use them freely in event
payloads.
