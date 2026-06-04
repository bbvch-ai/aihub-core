# aihub-fmh: Azure AI Search vs Core Milvus

**Status**: Proposed (2026-05-28) **Severity**: P0 (cost runaway, vendor lock-in, sovereignty exposure) **Drives**:
Overview §3.6 #3 (FMH stack divergence);
[Details §24 ADR-NEW-039](../02_architecture_review_details.md#24-proposed-adrs-36-total)

## Context

The Swiss AI Hub Core stack standardizes on **Milvus** as the vector database (deployed via docker-compose for Gen 1
customers, via the `aihub-common` Helm chart for Gen 3). RAG retrieval, hybrid index, and ACL-aware retrieval all assume
Milvus collections with the core-provided schema.

The customer deployment **aihub-fmh** (HEAD commit `5509d39 2026-04-07`, pinned to core v0.186.0) instead uses **Azure
AI Search** as the vector backend. Evidence:

- `aihub-fmh/lib/common/...mongo_aisearch_storage_context_resources*` — indexer + retriever wired to Azure SDK.
- Pulumi `iac_azure/deploy_units/stores/` provisions an Azure AI Search resource (separate from any Milvus instance).
- Two pipelines (`handbook_ingestion`, `position_ingestion`) write embeddings directly into AI Search, not Milvus.

Architectural and cost consequences observed:

- **Double inference cost.** Every RAG retrieval makes an AI Search query call (managed-service per-query fee) **plus**
  the downstream LLM call. The core Milvus path runs entirely on the tenant VM and has no per-query line item.
- **Vendor lock-in.** The retriever class is coupled to `azure-search-documents`, not the abstract `VectorStoreIndex`
  that core exposes. Migrating to Milvus would require rewriting the indexer + retriever pair for both pipelines.
- **Stack drift.** F\*H ships **MongoDB + Redis + Phoenix v10.0.4 + LiteLLM v1.77.7** alongside Azure AI Search — a
  pre-Langfuse and pre-FerretDB baseline that diverges from core. The 104-minor SDK drift (v0.186.0 → v0.290.4) makes a
  "just upgrade core" path impossible without also revisiting this storage choice.
- **Sovereignty argument is unique.** TARDOC / TARMED handbook data is Swiss-only by mandate, so Azure Switzerland North
  storage **is defensible** — unlike B*D Sweden or unverified W*P regions. But "defensible region" does not cover
  "defensible cost of staying off the core path".

The same pattern (Azure managed search service alongside the LLM call) is flagged for **aihub-ctc** in §3.3 #12 ("Azure
stack triple redundancy: DI + Foundry + core MinerU+LiteLLM"). The decision for F\*H sets precedent for that customer
too.

## Decision Drivers

- **Cost predictability**: managed AI Search query cost grows linearly with traffic; Milvus is a fixed-capacity VM cost.
- **Vendor sovereignty**: Azure AI Search Switzerland is acceptable for Swiss-only data; not for cross-customer generic
  use.
- **Engineering cost of migration**: F\*H pipelines + agents are already tested against AI Search; migration is weeks of
  work plus index re-population.
- **Core SDK upgrade coupling**: F\*H is 104 minors behind; a Milvus migration in the same window doubles risk.
- **Reusability**: the AI Search adapter is currently F*H-only and not contributed back to core; a Milvus migration
  removes the F*H-specific code path.

## Decision

Two options, to be picked by stakeholders (this ADR documents the trade-off; it does not bind to either).

### Option A — Migrate to core Milvus (recommended for long-term stack coherence)

Steps:

1. Replace `mongo_aisearch_storage_context_resources*` with the core `MilvusVectorStore` resource pair.
2. Re-run `handbook_ingestion` and `position_ingestion` against a tenant Milvus collection.
3. Decommission Azure AI Search resource from Pulumi `stores/`.
4. Bundle into the same release as the SDK upgrade (v0.186 → v0.220 step in §3.6 #1) so the F\*H team does one
   coordinated cutover, not two.

Cost saved: AI Search query line item. Engineering cost: ~2-4 weeks. Risk: TARMED billing accuracy is regression-
sensitive; the evaluation framework in `aihub-fmh/evaluation/` MUST stay green across the cut.

### Option B — Keep Azure AI Search, formalize the divergence

Steps:

1. Promote the AI Search adapter to a first-class core extension point (interface in `packages/core`, F\*H-specific
   implementation in customer code). Aligns with the proposed hexagonal-ports concern in Overview §5.1 Strategic.
2. Add a per-call cost line in Langfuse for the AI Search query (so the cost-per-tenant attribution still works).
3. Document the cost model in F\*H repo `README.md`: expected query rate × per-query cost × 12 months.
4. Add an ADR in `aihub-fmh` repo (once it gets its own arc42, see §3.6 #10) referencing this ADR.

Cost saved: zero per-query. Engineering cost: ~1 week for the interface + cost-tracking. Risk: stack coherence worsens —
F\*H stays on a different vector backend forever.

## Consequences

**Option A consequences**

- F\*H rejoins the core stack; future RAG improvements (hybrid index, ACL filter, BGE reranker) propagate for free.
- AI Search per-query cost goes to zero.
- One-time migration cost; index rebuild downtime to plan.

**Option B consequences**

- F*H stays on Azure AI Search indefinitely. Sets a precedent that other Azure-heavy customers (C*C) can also keep
  Azure-managed services if they document the trade-off.
- Core must absorb a new abstraction (vector-store interface) to keep both backends pluggable.
- Per-query cost stays in production; SLA for AI Search outage becomes a customer-visible concern.

**Cross-cutting**

- Either option, the LlamaIndex monkey-patch (`lib/common/register_openai_models.py`, §3.6 #2) is independent and must
  be removed via first-class core support before the SDK upgrade.
- Either option, the Pulumi state account SPOF (§3.6 #9) is unchanged.

## References

- Overview §3.6 (F\*H priority items), §1 Summary (Azure AI Search row), §4.1 Pillar 9 (cost).
- ADR `2026_02_09` (MinerU adoption — sets the precedent of "standardize on core stack").
- Proposed ADR `adr_040` (k8s chart core version pin) — related precedent for "decide what is part of the core
  contract".
- `aihub-fmh/evaluation/` — must stay green during any migration.
