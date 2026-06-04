# Pluggable Document Parser (Open the Loader Registry, add Docling)

**Status**: Proposed (2026-05-29) **Severity**: P1 (RAG quality, CPU stability, supplier risk) **Drives**: Overview §5.1
(strategic — replaceability), §5.8 (cross-cutting); pairs with
[`adr_043`](adr_043_continuous_component_update_strategy.md) (continuous component-update strategy)

## Context

Document parsing is the first quality gate of every RAG pipeline: garbage extraction caps every downstream embedding and
answer. Core ships a parser abstraction in
`packages/pipeline/swiss_ai_hub/pipeline/resources/parser/document_parser_resource.py` — a Dagster
`ConfigurableResource` (`DocumentParserResource`) that selects a reader by file extension. The engine is chosen via a
**closed enum**:

```python
class LoaderType(StrEnum):
    MINERU = "mineru"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
```

`MineruLoader` (`packages/core/.../document/loaders/mineru_loader.py`) talks to MinerU over HTTP using a
`vlm-http-client` backend (VLM server), which keeps AGPL isolation but means MinerU's quality and stability depend on
the VLM model and the hardware it runs on. **Verified field finding (review 2026-05)**: MinerU is **unstable on CPU-only
deployments** — without a GPU the VLM backend is slow and flaky, and several customer environments have no GPU.

The replaceability problem, verified by reading the code:

- The two built-in loaders **can** be swapped via config (`default_definitions(..., document_parser_loader_type=...)`),
  so MinerU ↔ Azure Document Intelligence is a configuration change.
- But the loader set is a **closed enum baked into core**. Adding a new engine (e.g. **Docling**, which runs well on
  CPU) requires a *core code change*: a new `DoclingLoader(BaseReader)` plus a new `LoaderType` value plus a branch in
  `DocumentParserResource._get_readers_map()`. A customer **cannot register their own parser** without forking core or
  hand-rolling a parallel resource (the resource docstring even tells them to "create a new resource").

So the user concern — "if we need to replace MinerU it is not easy" — is accurate in nuance: config-swap between the two
built-ins, **code-change in core** for anything new. As more document engines appear (and some go commercial), a closed
enum is a recurring tax.

## Decision Drivers

- **CPU stability**: customers without GPU need a parser that is reliable on CPU (Docling is a strong candidate).
- **Open/Closed**: adding a parser should not require editing a `match`/`if` in core.
- **Sovereignty**: a self-hostable, OSS, CPU-friendly parser reduces reliance on Azure Document Intelligence.
- **Quality is measurable**: parser choice should be backed by an extraction-quality benchmark, not opinion.
- **No premature abstraction**: the existing `BaseReader` + readers-map is already most of the seam — open it, don't
  rebuild it.

## Decision

1. **Add a first-class `DoclingLoader`** (`BaseReader`) in core alongside `MineruLoader`, and a `LoaderType.DOCLING`
   value. Docling runs in-process / containerised without a GPU.

2. **Open the loader registry.** Replace the hard-coded enum branch in `DocumentParserResource` with a registry keyed by
   `LoaderType` (or string), populated by core's built-ins and **extendable by customers** — a customer can register a
   `BaseReader` for a set of extensions via the resource config, without modifying core. Keep the two built-ins as the
   default registration so existing pipelines are unchanged.

3. **Benchmark before defaulting.** Run an extraction-quality + latency benchmark (Docling vs MinerU vs Azure DI) on a
   representative CPU host using a fixed document set (PDF with tables/figures, Office docs, scans). Publish the result;
   pick the default per deployment profile (GPU vs CPU-only).

4. **Document the contract**: which `BaseReader` methods a custom parser must implement, image/table handling
   expectations, and the metadata keys it must emit (`NUMBER_OF_PAGES`, etc.). This becomes part of the SDK public API
   surface tracked by [`adr_038`](adr_038_sdk_import_discipline.md).

## Consequences

**Positive**

- CPU-only customers get a stable parser; fewer "agent fails on ingest" incidents.
- New engines (Docling today, the next OSS/commercial parser tomorrow) plug in via registration, not a core PR.
- Parser choice becomes a benchmarked, reversible decision per deployment.
- Reduces Azure Document Intelligence lock-in for sovereignty-sensitive customers.

**Negative**

- Docling and MinerU produce slightly different markdown/structure → embeddings change → a **re-index** is needed when a
  customer switches engines (pairs with embedding-versioning ADR-NEW-028).
- A registry is marginally more indirection than an enum; must keep the default behaviour identical to avoid surprising
  existing pipelines.
- Maintaining 3 loaders is more surface than 2.

**Open items**

- Whether Docling becomes the **CPU default** and MinerU stays the **GPU default**, or Docling becomes the global
  default.
- Whether the customer-registered-parser hook ships in the same release as `DoclingLoader` or follows it.
- Benchmark corpus ownership (who curates the gold document set + expected extractions).

## References

- `packages/pipeline/swiss_ai_hub/pipeline/resources/parser/document_parser_resource.py` — `DocumentParserResource`,
  `LoaderType` (the closed enum this ADR opens).
- `packages/core/swiss_ai_hub/core/generative_ai/document/loaders/mineru_loader.py` — HTTP/VLM MinerU loader.
- `packages/core/swiss_ai_hub/core/generative_ai/document/loaders/document_intelligence_loader.py` — Azure DI loader.
- [Docling (OSS document parser)](https://github.com/DS4SD/docling).
- Related: [`adr_043`](adr_043_continuous_component_update_strategy.md) (continuous component-update strategy),
  [`adr_044`](adr_044_rag_vector_design_gate.md) (RAG/vector-design gate), ADR-NEW-028 (embedding versioning &
  migration).
