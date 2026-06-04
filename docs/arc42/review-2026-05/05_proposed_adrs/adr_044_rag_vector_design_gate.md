# RAG / Vector-DB Design Gate (Design before Implement)

**Status**: Proposed (2026-05-29) **Severity**: P0 (answer quality + performance across multiple live customers)
**Drives**: Overview §5.4 (Dem*scope), §5.5 (W*P), §5.6 (F\*H), §5.8 (cross-cutting), §6.4 (process)

## Context

Review 2026-05 found a **process gap** common to every customer project: requirements went straight to implementation
**without a design/analysis step**. The most damaging omission is **vector-DB design** — chunking strategy, collection
schema and metadata, index type and tuning, and an evaluation plan. Because this was never deliberately designed, answer
quality and performance are capped and hard to debug. Concrete symptoms:

- **F\*H**: customer unhappy with answers. The data is **structured** (TARDOC/TARMED handbook + positions), but
  ingestion was not designed for that structure (generic chunking, no field/metadata model), and there is **no
  testing/eval strategy** even though an `evaluation/` framework exists in the repo. Likely root cause of poor answers —
  not the LLM.
- **Dem\*scope**: hash-partitioned Milvus held **in-memory** — works only because the box has 200 GB RAM; a design
  review would have flagged the cost wall as data grows (see Overview §5.4).
- **W\*P**: customer reports poor platform performance; **no baseline** exists to locate the bottleneck (pairs with
  [`adr_046`](adr_046_load_test_baselines.md)).

Core actually provides the building blocks to do this well — configurable chunking
(`MarkdownStructuralNodeParserResource`), Milvus index choice (`HNSW`/`IVF_FLAT`) and `dimensions` in
`MilvusVectorStoreResource`, summary/parent-child retrieval, rerank, and an evaluation module
(`packages/core/.../generative_ai/evaluation/`). The gap is **process, not capability**: these knobs are left at
defaults and never validated against a test set.

## Decision Drivers

- **Quality is set at ingestion**: retrieval can't recover information that chunking/schema destroyed.
- **Structured data needs structured design**: field-aware chunking + metadata filters beat naive splitting.
- **Measurable, not anecdotal**: "the answers are bad" must become a number on a test set.
- **Cheap to add**: a lightweight design gate + an eval harness, reusing core's existing evaluation module.
- **Reversible cost wall**: index/memory decisions (e.g. in-memory vectors) must be a conscious, documented trade-off.

## Decision

Introduce a **RAG/vector-design gate** as a required step between requirement intake and implementation for any project
that ingests data:

1. **Design artefact (1–2 pages) before coding**, covering:

   - **Chunking**: strategy + size/overlap, justified by document structure (esp. structured sources like F\*H).
   - **Schema/metadata**: Milvus fields and filterable metadata (source, ACL, tenant, language, doc-type, dates).
   - **Index & sizing**: index type (`HNSW`/`IVF_FLAT`/DISKANN), `dimensions`, and a **memory/disk plan** with a
     data-growth projection (explicitly decide in-memory vs disk-backed; record the cost wall — Dem\*scope lesson).
   - **Retrieval**: top-k, rerank, summary/parent-child post-processing.
   - **Eval plan**: a test set + metrics (retrieval hit-rate, answer correctness/faithfulness) using core's
     `generative_ai/evaluation/` module and/or Langfuse datasets.

2. **Eval harness wired before go-live**: a runnable test set with a baseline score, so quality regressions are caught
   and tuning is measured. This harness is also the gate reused by
   [`adr_043`](adr_043_continuous_component_update_strategy.md) for component upgrades.

3. **Design review sign-off**: architect/lead reviews the artefact (it is small) before implementation starts. For
   existing customers, run a **retro-fit design pass** starting with F*H (worst answer quality) and Dem*scope (cost
   wall).

## Consequences

**Positive**

- F\*H-class answer-quality problems get a root cause and a measurable fix, not LLM-swapping guesswork.
- Cost walls (in-memory vectors) become conscious, documented decisions with a growth plan.
- A reusable eval harness underpins both quality assurance and safe component upgrades.
- Uses core capabilities already present (chunkers, index config, evaluation module) — no new framework.

**Negative**

- Adds a step before implementation; small calendar cost up front (pays back in rework avoided).
- Building/maintaining test sets is real work and needs an owner per customer.
- Retro-fitting existing customers means a re-index when chunking/schema changes.

**Open items**

- Minimum eval metric thresholds for "go-live ready" per customer.
- Whether the gate is enforced in CI (eval must pass) or as a review checklist initially.
- Test-set ownership and refresh cadence (customer SME involvement, esp. F\*H medical content).

## References

- `packages/core/swiss_ai_hub/core/generative_ai/evaluation/` — existing evaluation module to base the harness on.
- `packages/pipeline/swiss_ai_hub/pipeline/resources/parser/` — `MarkdownStructuralNodeParserResource` (chunking) and
  parser resources.
- `packages/pipeline/swiss_ai_hub/pipeline/resources/vector_store/` — `MilvusVectorStoreResource` (index type,
  dimensions).
- Related: [`adr_039`](adr_039_fmh_azure_ai_search_vs_milvus.md) (F\*H vector backend choice),
  [`adr_046`](adr_046_load_test_baselines.md) (load-test baselines),
  [`adr_043`](adr_043_continuous_component_update_strategy.md) (eval-gated upgrades), ADR-NEW-028 (embedding
  versioning).
