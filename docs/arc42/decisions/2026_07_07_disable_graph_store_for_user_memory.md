# Disable the Graph Store for User Memory (Extended to Organization Memory)

## Status

Accepted, amended 2026-08-26 by issue #1713. Amends `2025_12_18_adopt_mem0_for_agent_memory` — originally for the
**user-memory** scope only, and since #1713 for organization memory as well.

The "keep the graph for organization memory" half of the original decision is **superseded**. Everything from here to
the Amendment section records the original 2026-07-07 reasoning and is kept for history; read it together with the
Amendment, which corrects the cost model it rests on.

## Context

Issue #1179 reported that saving user memory after an agent answers is slow and keeps the "thinking" indicator visible
until the run finishes. Instrumented measurement of one `AgentMemory.add_user_memory` call (mem0 1.0.11, model
`text-generation/Ministral-3-14B-Instruct-2512`) found:

- One save fans out to **5 LLM calls**: 2 on the vector branch (fact extraction + ADD/UPDATE/DELETE reconciliation) and
  **3 sequential** calls on the graph branch (entity extraction → relation extraction → obsolete-relation detection),
  plus ~120 one-per-node embedding round-trips.
- Vector and graph branches run under `asyncio.gather`, so wall-clock ≈ the slower (graph) branch.
- A representative slow run took ~66s total; the graph branch (~31s of LLM + the bulk of the embeddings) was the long
  pole. The dominant factor is **output-token throughput** — latency ≈ `completion_tokens ÷ ~55–80 tok/s` — so the graph
  branch's extra generation is pure, avoidable cost.

Per `2025_12_18_adopt_mem0_for_agent_memory`, the graph store served two purposes for user memory: (1) sharing user
facts **across agents** (the vector store is `_agent_id`-scoped, so it cannot do this), and (2) multi-hop relationship
traversal. Investigation found purpose (2) is **unused** — retrieval renders graph relations as flat triples into the
prompt; no traversal exists in application code. Purpose (1) is real but its usage is unquantified in production.

For user memory specifically, memories are flat personal preferences written on **every** chat turn — high frequency,
low relational value. Organization memory is the opposite: rare, explicitly curated, entity-rich facts written only by
`ExpertAskingAgent` — where the graph's cost is amortized and its relational value plausibly applies.

> **Superseded by the Amendment below.** This paragraph is the load-bearing error: it reasons only about *write*
> frequency. mem0 also runs the graph on reads, so the cost is paid per retrieval and amortizes against nothing.

## Decision Drivers

- Cut the per-turn user-memory save latency (issue #1179), where the graph branch is the largest single cost.
- Preserve organization memory's graph, where the cost/value trade-off is favorable.
- Keep the change measurable, and avoid a silent cross-agent regression.

## Decision

Make the mem0 graph store **per-memory-type**:

- **User memory: graph OFF (unconditional).** `AgentMemory` builds a graph-less mem0 service for user memory; mem0 then
  skips the entire graph branch (3 LLM calls + graph embeddings). The graph is not needed for user memory — cross-agent
  user facts are served from the vector store instead (see below). There is no runtime toggle: the graph was providing
  no value for flat per-turn user preferences, so it is removed rather than made configurable.
- **Organization memory: graph ON**, always. *(Superseded — organization memory is graph OFF since #1713; see the
  Amendment.)*

Because mem0 has no per-call graph switch (`enable_graph` is fixed at `Memory` construction from whether a `graph_store`
is configured) and `AgentMemory` previously shared one service for both scopes, the two scopes are now served by two
lazily-built services with different configs. Lazy construction means a user-memory-only agent (e.g. RAG) never opens a
Neo4j connection when the graph is off.

**Cross-agent replacement (replaces graph purpose 1):** user-memory *reads* (`search_user_memory`) drop the `agent_id`
filter and search all of the user's memories regardless of which agent wrote them — mirroring
`search_organization_memory`. The writer's `_agent_id` remains on the stored record as trace metadata; it no longer
partitions reads. This moves cross-agent user-fact sharing from the graph to the vector store.

## Measured effect

Dev run with the graph off (~28 stored memories): Ministral LLM calls **5 → 2**, embedding calls **~120 → 13**, save
wall-clock **~66s → ~17.5s** (~73% reduction). The residual is the vector ADD/UPDATE/DELETE reconciliation call (~15s,
~1,200 completion tokens) whose output **scales with the stored-memory count** — it is unaffected by the graph and is
tracked separately (bounding memory count / decoupling the save from the run's critical path).

## Consequences

**Positive**

- ~73% faster user-memory saves; ~3 fewer LLM calls and ~100 fewer embedding round-trips per save; RAG-type agents stop
  connecting to Neo4j entirely.
- Organization memory's graph capability is untouched. *(Superseded — see the Amendment.)*

**Negative / risks**

- **Lost prompt feature:** retrieval currently renders a "Knowledge Graph Relationships" block (graph triples) into the
  user-memory system prompt (`extend_chat_history_with_user_memory`). With the graph off this block is empty.
  Materiality is unquantified — see open question.
- **Cross-agent semantics change:** cross-agent user facts now flow through the vector store (unpartitioned reads)
  instead of the graph. Behavior is equivalent in intent, but relevance is now purely semantic (threshold + rerank)
  rather than graph-linked.
- Does **not** by itself meet issue #1179's ≤5s target — the residual vector reconciliation call remains (see above).
- The graph branch still runs unconditionally in mem0 for `infer=False` writes; org memory is unaffected, but this is a
  mem0-internals caveat to note if org write latency ever matters. *(Resolved by the Amendment: mem0 gates
  `_add_to_graph` on `enable_graph`, so org writes now skip it too.)*

**Follow-up (monitor after rollout):** production graph-usage stats — what fraction of users interact with 2+ agents,
and how often the removed relations block mattered — to confirm the vector-based cross-agent replacement covers the
need.

## Amendment (2026-08-26, issue #1713)

### What was wrong

The decision above kept the graph for organization memory on the argument that its cost is **write-side** and amortized
by rare, entity-rich writes. That cost model is incomplete: **mem0 runs the graph on reads, not just writes.** Every
organization-memory retrieval therefore paid the graph cost on the chat critical path of every message, where nothing
amortizes it — the opposite of the trade-off the original decision assumed it was making.

Measured for organization-memory retrieval (figures from issue #1713):

- **~1.9 s median** with the graph, against **~0.25 s** for the same search without it.
- **67 s** observed on a cold call.
- A failure anywhere in the graph path ended the run with an `ExceptionEvent` — a user-visible chat failure caused by an
  optional context-enrichment step.

The original investigation had already found that graph *relations* are unused: retrieval renders them as flat triples
into the prompt and no traversal exists in application code. So the read-path cost bought nothing.

### Decision

- **Organization memory: graph OFF**, unconditionally. Both agent-facing scopes are now graph-free, so the two per-scope
  services of the original decision collapse into a single `AgentMemory._memory_service` built with `enable_graph=False`
  — keeping them apart would have meant two identical mem0 clients per agent.
- **The admin CRUD paths keep the graph.** `UserMemory` and `OrganizationMemory` (the Admin-UI memory endpoints) still
  build a graph-enabled service. This is deliberate and matches what user memory has done since 2026-07-07: mem0 only
  purges Neo4j in `delete_all` when the service has the graph enabled, and those endpoints are the GDPR delete path.
  Disabling the graph there would orphan existing personal relations in Neo4j permanently.
- **The graph-relations block is removed from the organization-memory system prompt** (all four locales), and
  `extend_chat_history_with_organization_memory` no longer takes a `relations` argument. The block could only ever
  render empty.
- **Memory retrieval failures degrade instead of ending the run.** `do_retrieve_user_memory` and
  `do_retrieve_organization_memory` return an *empty* event on failure, timeout included — a hung backend blocks the
  chat turn as surely as a raise ends it, so both take the same path. Note that `stop_on_error=False` alone would be
  worse than the status quo: the dispatcher would suppress the `ExceptionEvent` but publish nothing, and
  `check_memory_ready_for_chat_history` blocks until the retrieval event exists — so the run would hang rather than end.
  Returning an empty event is what keeps that precondition satisfiable. Namespace-allow-list violations stay fatal: they
  are caller errors, and answering from the wrong scope would hide them.

### Consequences

**Positive**

- Organization-memory retrieval costs roughly what user-memory retrieval costs; no Neo4j connection is opened by the
  retrieval step.
- A memory-subsystem outage degrades the answer instead of failing the chat turn.
- Organization-memory writes (`ExpertAskingAgent`) also skip the graph, closing the `infer=False` caveat the original
  decision left open under Consequences.

**Negative / risks**

- **The organization-memory graph now decays.** Nothing writes org relations any more, so
  `pages/[tenant]/service/organization-memories/graph.vue` shows only pre-#1713 data and will be empty on any deployment
  provisioned after it. This is the state `user-memories/graph.vue` has been in since 2026-07-09; #1713 makes the two
  consistent rather than introducing a new failure mode. Removing or reworking those pages belongs to #1715.
- **Agent and admin surfaces disagree about relations.** Agent org retrieval returns none; the admin org endpoints still
  return them from Neo4j. This follows directly from keeping the graph on the CRUD paths (above) and is expected, not a
  bug.
- Failures are now silent to the user — logged at `warning`, with no display event saying memory was unavailable.
  Surfacing that is deliberately out of scope here.

## Related

- Supersedes the graph portion of `2025_12_18_adopt_mem0_for_agent_memory` for both memory scopes — the user-memory
  portion on 2026-07-07, the organization-memory portion in the Amendment above.
- Neo4j data is retained; nothing writes to it from the agent path any more. Removing mem0 and Neo4j from the platform
  is tracked in #1715 (decouple memory events and UI from mem0) and #1716 (distilled memory on the shared substrate).
