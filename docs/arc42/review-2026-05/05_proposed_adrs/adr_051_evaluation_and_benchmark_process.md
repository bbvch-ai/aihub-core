# Continuous Evaluation & Performance Benchmark Process (Accuracy + Performance NFR Gate)

**Status**: Proposed (2026-05-29) **Severity**: P1 (answer quality, performance, customer satisfaction)
**Drives**: Overview §3.1 #32 (no eval/benchmark process), §3.6 #12 (F\*H answer-quality complaint), §3.5 #11 (W\*P
performance complaint); pairs with `adr_044` (RAG/vector-design gate) and `adr_046` (load-test baselines)

## Context

Two production customers are unhappy for reasons that trace to a **missing non-functional process**, not a single bug:

- **F\*H** is dissatisfied with answer quality; structured TARDOC/TARMED data was ingested without a designed vector
  schema and there is **no RAG testing/eval strategy** — an `evaluation/` framework exists in the repo but is **unused**
  (§3.6 #12).
- **W\*P** reports poor platform performance with **no baseline to compare against**, so the issue cannot be
  triaged (§3.5 #11).

Across the platform there is **no standing methodology** to (a) measure RAG/agent **accuracy/quality** or (b)
**benchmark performance** before/at release:

- Quality is measured ad-hoc and per-customer: IGS has a Langfuse `Citation Quality` LLM-as-judge harness, F\*H has its
  own evaluator/testset, but neither is a **core capability** or a **CI gate**.
- §11 QA gaps confirm: **no load test in CI, no coverage threshold, no chaos**; `adr_046` proposes load-test baselines
  but a *quality* eval gate is still missing.
- Result: regressions in retrieval quality or latency are discovered by **customers**, not by the team.

This is the non-functional risk the review previously only captured indirectly (FMH-12, WPE-11, ADR-044/046). CORE-32
now records it as a first-class platform risk.

## Decision Drivers

- **Quality must be measurable and gated**, not anecdotal — "the customer is unhappy" is too late.
- **Reuse what exists**: IGS `Citation Quality` judge + F\*H evaluators/testsets are working seeds.
- **Performance needs a baseline** to make "slow" actionable (ties `adr_046`).
- **Per-customer divergence** of eval setups means no comparability — needs a shared core capability.

## Decision

1. **Promote evaluation to a core capability.** Ship a reusable eval module (golden datasets + LLM-as-judge metrics:
   relevance, correctness, conciseness, citation quality) building on the IGS `Citation Quality` judge and F\*H
   evaluators. Datasets live in Langfuse (system of record) + mirrored in-repo for PR review (as IGS already does).
2. **Accuracy/quality gate in CI.** Run the eval suite on a representative dataset per agent on release; fail or warn on
   regression beyond a threshold. Record scores over time (Langfuse runs).
3. **Performance benchmark process.** Define and run a performance benchmark (latency p50/p95, throughput, RU/cost) per
   release against a fixed corpus/hardware profile; publish a baseline (ties `adr_046`). Make "slow" a
   measured delta, not a guess.
4. **Design-before-implement for RAG.** Couple with `adr_044` (RAG/vector-design gate): field-aware chunking + metadata
   schema + an eval harness before go-live for structured-data customers (the F\*H lesson).
5. **Document the methodology** so every new customer (and pre-sales) inherits it rather than reinventing it.

## Consequences

**Positive**

- Quality and performance regressions are caught in CI, before customers feel them.
- Comparable, versioned eval across customers; the F\*H/IGS work becomes a reusable asset.
- Performance complaints become triable against a baseline.

**Negative**

- Building/curating golden datasets is ongoing effort; LLM-as-judge runs add CI cost/time.
- Thresholds need tuning to avoid flaky gates.

**Open items**

- Who owns the gold dataset corpus per customer/domain.
- Gate vs warn initially (start as warn, harden to gate).

## References

- Overview §3.1 #32, §3.6 #12 (F\*H), §3.5 #11 (W\*P), §11 QA gaps.
- `aihub-igs/eval/` (Citation Quality judge + `igs_guisan` testset), F\*H `evaluation/` framework.
- Related: `adr_044` (RAG/vector-design gate), `adr_046` (load-test baselines), `adr_037` (supported use cases).
