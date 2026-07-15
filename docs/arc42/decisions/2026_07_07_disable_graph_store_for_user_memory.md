# Disable the Graph Store for User Memory (Keep It for Organization Memory)

## Status

Accepted. Amends `2025_12_18_adopt_mem0_for_agent_memory` for the **user-memory** scope only; organization memory is
unchanged.

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
- **Organization memory: graph ON**, always.

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
- Organization memory's graph capability is untouched.

**Negative / risks**

- **Lost prompt feature:** retrieval currently renders a "Knowledge Graph Relationships" block (graph triples) into the
  user-memory system prompt (`extend_chat_history_with_user_memory`). With the graph off this block is empty.
  Materiality is unquantified — see open question.
- **Cross-agent semantics change:** cross-agent user facts now flow through the vector store (unpartitioned reads)
  instead of the graph. Behavior is equivalent in intent, but relevance is now purely semantic (threshold + rerank)
  rather than graph-linked.
- Does **not** by itself meet issue #1179's ≤5s target — the residual vector reconciliation call remains (see above).
- The graph branch still runs unconditionally in mem0 for `infer=False` writes; org memory is unaffected, but this is a
  mem0-internals caveat to note if org write latency ever matters.

**Follow-up (monitor after rollout):** production graph-usage stats — what fraction of users interact with 2+ agents,
and how often the removed relations block mattered — to confirm the vector-based cross-agent replacement covers the
need.

## Related

- Supersedes the user-memory graph portion of `2025_12_18_adopt_mem0_for_agent_memory` (organization memory portion
  stands).
- Neo4j data is retained (only user-memory writes stop populating it); a future graph-store replacement (Neo4j is
  flagged as outdated) is out of scope for this decision.
