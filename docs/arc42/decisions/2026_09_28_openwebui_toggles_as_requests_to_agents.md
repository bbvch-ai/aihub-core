# OpenWebUI Chat Toggles Are Requests to Our Agents

## Context

OpenWebUI is the chat UI for our agents, but it also runs its own web search, image generation, code interpreter, memory
and file retrieval. For agent models these ran next to the agent rather than inside it: before the pipe is called,
OpenWebUI searches the web, generates images and rewrites the prompt for the code interpreter whenever a toggle is on,
gated only by per-model capabilities, the function-calling mode and the `features` the frontend sends. The provisioner
hid Web Search on every agent model to stop one of these paths, and left the others running. None of this work is
traced, cost-attributed or access-checked by our platform, and the agent cannot tell what the user asked for.

The same pattern repeats for every capability we want agents to own: attached files (#1935), code execution (#1570), web
search (#1568), image generation (#1571). This decision fixes the signal path they all share (#590).

## Decision Drivers

- OpenWebUI is a UI layer for agents: it shows toggles and renders results, and runs none of the work.
- A toggle is a request. The agent decides whether and how to serve it.
- Which toggles an agent shows must follow from what its blueprint can do, without a second declaration to keep in sync.
- Adding a feature, including one OpenWebUI has no toggle for, must not change the invocation contract or OpenWebUI.
- Plain LLM models keep OpenWebUI's built-ins.

## Decision

**1 — `ChatFeature` on the invocation.** `UserMessageEvent.requested_features` carries the features requested for the
message, as one extensible enum rather than one field per feature. The OpenAI-compatible API accepts the same list in
`metadata.features`. The dispatcher copies it into the run context, and `RequestedFeatures.contains` answers whether a
feature was requested for the run.

**2 — Support is derived from capabilities.** A capability (ADR `2026_09_28_capabilities_and_the_conversational_spine`)
may declare the `ChatFeature` it serves. A blueprint supports exactly the features of the capabilities its steps call;
discovery announces them and `AgentClassEntity` stores them. A requested feature the blueprint does not support never
counts as requested, whoever sent it.

**3 — The OpenWebUI model row describes the agent.** The provisioner writes, per agent model:

- `meta.capabilities`: every native toggle explicitly on or off from the supported features (OpenWebUI treats a missing
  capability as enabled), and `memory: false`.
- `meta.filterIds`: our agent filters, plus one toggle filter per supported feature that has no native toggle.

Our agent filters are registered non-global (`global: false` in their frontmatter), so they run only on the models
listing them and plain LLM chats never load them. OpenWebUI-side tools (`meta.toolIds`) stay unused: they would run
inside OpenWebUI, outside the agent.

**4 — One inlet filter strips the toggles.** `aihub_feature_filter` runs right before OpenWebUI reads `features`. It
removes every toggle OpenWebUI would act on from the body and hands the pipe, through `__metadata__`, only those the
selected model supports. This check is per request because OpenWebUI sends a toggle's state even after the user switched
to a model that hides it. Toggle filters for custom features add their feature to the same metadata list.

## Consequences

### Positive

- OpenWebUI runs none of its own web search, image generation or code interpreter for agents in any function-calling
  mode, and the messages the agent receives are no longer rewritten.
- Installing a capability that serves a feature is all it takes for its toggle to appear on every agent of that
  blueprint, including features OpenWebUI has no toggle for.
- The filters no longer have to recognise agents by model id, which is how the turn-scope filter silently stopped
  matching after the agent ids changed.

### Trade-offs

- Until a capability serves a feature, no agent shows Web Search, Code Interpreter or Image Generation. Agents that
  relied on OpenWebUI generating images before the pipe lose that path until #1571.
- A custom feature needs a small toggle-filter function file of its own, since OpenWebUI functions are standalone
  modules.
- The filter and the pipe share a metadata key by convention, pinned by a unit test rather than a shared import.
