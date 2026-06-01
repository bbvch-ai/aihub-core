# Continuous Component-Update Strategy (Replaceable Building Blocks)

**Status**: Proposed (2026-05-29) **Severity**: P1 (strategic — keeping pace with a fast-moving AI stack)
**Drives**: Overview §5.1 (strategic), §6.2 (strategic priorities); generalises
[`adr_042`](adr_042_pluggable_document_parser_docling.md)

## Context

The AI tooling layer moves faster than any other part of the platform: document parsers, embedding models, rerankers,
vector stores, and LLM serving runtimes are all improving (or being deprecated, or going commercial) on a quarterly
cadence. Two concrete pressures surfaced in review 2026-05:

- **Replacement is hard today.** The MinerU finding (see [`adr_042`](adr_042_pluggable_document_parser_docling.md))
  showed that even where core has a seam, the choice is a closed enum — swapping in a better engine is a core code
  change, not config. The same brittleness applies wherever a concrete dependency is wired directly into business code.
- **Commercial/EOL risk.** Some libraries the platform leans on are OSS today but may relicense or stall. Without a
  deliberate abstraction + watch process, a single upstream decision can strand a customer deployment.

What core already does well (and should be the template): **LiteLLM** decouples application code from the LLM/embedding/
rerank provider — switching models is a config change, not a code change. The gap is that this pattern is **not applied
consistently** to the other swappable building blocks (parser, vector store, OCR), and there is **no routine** for
discovering, evaluating, and adopting upstream changes.

This ADR is intentionally high-level: it sets the *approach and the stack*, not per-component designs.

## Decision Drivers

- **Replaceability without forks**: a customer must be able to change a building block without editing core.
- **Evidence-gated upgrades**: never adopt a new version/engine on vibes — gate on a quality + latency benchmark.
- **Early warning**: license changes, CVEs, and deprecations should page someone, not be discovered at upgrade time.
- **Low operational tax**: prefer automation (bots, CI) over manual dependency chores.
- **Don't over-abstract**: only the genuinely swappable seams get a port; everything else stays concrete.

## Decision

Adopt a four-part strategy. The "stack" named below is the recommendation; specifics are decided per component in
follow-on ADRs.

1. **Ports & Adapters for the swappable seams.** Define a thin abstract interface (a "port") for each building block that
   the market churns: **document parser** (already `BaseReader`), **vector store**, **OCR**, **embedding/rerank/LLM**
   (already covered by LiteLLM). Concrete engines are adapters behind the port, selected by config and **registerable by
   customers** (the generalisation of [`adr_042`](adr_042_pluggable_document_parser_docling.md)). Follow the LiteLLM
   precedent — it is the proof this works in this codebase.

2. **Automated dependency intake.** Run **Renovate** (or Dependabot) across core + customer repos: grouped, scheduled
   PRs; pinned versions (CLAUDE.md already forbids floating ranges); changelogs surfaced in the PR. This turns "we are 104
   minors behind" into a continuous trickle instead of a cliff.

3. **Eval-gated adoption.** No swappable-component upgrade merges until it passes an **automated evaluation harness** in
   CI (extraction quality for parsers; retrieval/answer quality for embeddings/rerank/LLM; see
   [`adr_044`](adr_044_rag_vector_design_gate.md) for the gate and ADR-NEW-028 for embedding migration). A regression
   blocks the bump; a win is recorded as evidence.

4. **Market-watch + exit plan.** Keep a short living register of each external building block: upstream health, license,
   and a named **fallback adapter** (e.g. Docling as the OSS fallback for a commercial parser; self-hosted vLLM as the
   fallback for a cloud LLM). Review quarterly. A license change triggers the documented switch to the fallback, not a
   scramble.

## Consequences

**Positive**

- Customers can adopt better/cheaper/sovereign components as they appear — replaceability becomes routine.
- Upgrades are continuous and evidence-backed, shrinking the per-customer drift that makes today's upgrades expensive.
- Commercial/EOL surprises have a pre-planned exit.
- Reuses an existing, proven pattern (LiteLLM) rather than inventing a new framework.

**Negative**

- Ports add indirection and a small maintenance cost; only justified for genuinely churny seams.
- Renovate PR volume needs triage discipline or it becomes noise.
- The eval harness must exist and be trustworthy first (depends on [`adr_044`](adr_044_rag_vector_design_gate.md)).

**Open items**

- Which seams get a port first (recommended order: parser → vector store → OCR; LLM already done).
- Renovate vs Dependabot, and grouping/scheduling policy.
- Where the market-watch register lives (arc42 ch. 11 risks vs a dedicated doc).

## References

- `packages/core/swiss_ai_hub/core/infrastructure/litellm/` — the provider-agnostic precedent to generalise.
- [`adr_042`](adr_042_pluggable_document_parser_docling.md) — the concrete first application (parser registry + Docling).
- [`adr_044`](adr_044_rag_vector_design_gate.md) — the eval gate this strategy depends on.
- [Renovate](https://docs.renovatebot.com/) · [Dependabot](https://docs.github.com/code-security/dependabot).
- Root `CLAUDE.md` — dependency rules (`uv add/remove`, pinned versions, no manual `pyproject.toml` edits).
