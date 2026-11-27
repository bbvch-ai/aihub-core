# Agents Called as Tools Through Tool Families

## Context

Delegating to another agent was wired by hand: a blueprint named one agent in a step and waited for it (#2299). A model
in the tool loop could not decide to ask an agent, so a question about law reached the law RAG agent only if the user
picked that agent. The tool loop assumed every capability offers one tool with a name fixed in code, which cannot
express "one tool per agent the asking user may use", known only per run.

ADR `2026_11_27_in_the_loop_deadlines_and_delegation_answers_through_jetstream` made delegations durable and gave them
deadlines; this builds on it.

## Decision Drivers

- *One tool per agent*, so the model reads each agent's name and description and calls it by name (#2300 adds one per
  start event).
- *Only what the asking user may use*: online, permitted, admitted by the profile, never the asking agent itself.
- *The answer reaches the model, not the user*, and the user still sees that the agent works.
- *No change for blueprints and tools that do not use it.*

## Decision

- **Tool families.** A capability with `tool_family = True` owns every tool named `{tool_name}__{member}`. It returns
  its members per run from `tool_definitions(context)` (async) and each member's label and approval policy from
  `member_options(name, run_context)`. `ToolSet.owner/offers/family_of/options_in_run` resolve members;
  disabling the family or an approval rule on it applies to every member. Static tools are unchanged.
- **`AgentTools`** (`ask_agent`) is such a family. Per run it asks the API for the online profiles over NATS
  request/reply (`CallableAgentsClient` → `CallableAgentsResponder`, `aihub.rpc.callable_agents.agent`), keeps the
  conversational ones the run's `AccessChecker` allows, the profile admits (`AgentToolsConfig.only_listed`/`agents`)
  and that are not the caller, and records them in the run context (`OfferedAgents`). Calls resolve their agent from
  that record only, so the model cannot reach anything it was not offered. A run at `max_depth` of a delegation chain
  is offered none.
- **The call** is an `AgentInTheLoop` delegation with the asking user, on a thread and display of its own, the profile's
  `timeout_seconds`, and the `tool_call_id`. Its answer text (`StopEvent.answer_text()`), failure or timeout becomes the
  tool result; the run continues either way.
- **The user sees the steps.** A run delegated with a `tool_call_id` publishes a `DelegatedProgressEvent` per step into
  the caller's display. The OpenWebUI pipe shows each as a status and lists them above the answer in the tool's block.
  Such a run cannot ask the user anything: a HITL request ends it with an exception the caller receives.
- **A start nobody picked up by the deadline expires** (`Nats-TTL` on the start event; agent streams allow message TTLs),
  so an agent coming back online later does not run it for nobody. This replaces pinging before a call (#587, closed).

## Consequences

- The API answers the catalogue for the whole deployment; the asking agent filters it by the user, as it does for
  knowledge. Every call is persisted as its `AgentInTheLoopRequestEvent` (caller, callee, user and tenant) and logged.
- A delegated run's start event may expire while the run still works past the caller's deadline; its answer is then
  dropped by the caller, as any late answer is.
- An agent that crashed after discovery last saw it is still offered, and a call to it ends at the deadline.
