# Load-Test Baselines (Per Project + Core)

**Status**: Proposed (2026-05-29) **Severity**: P1 (no performance baseline anywhere — can't diagnose or defend SLAs)
**Drives**: Overview §5.5 (W\*P), §5.8 (cross-cutting); ties ADR-NEW-010 / ADR-NEW-033 (SLI/SLO)

## Context

Review 2026-05 found that **neither core nor any customer project has load testing or a documented performance
baseline**. The consequence is concrete and already biting:

- **W\*P**: the customer reports the platform is slow. With **no baseline**, there is no way to say whether it is the
  LLM, retrieval, the VM, network, or config — and the customer is unresponsive, so we cannot get their numbers either.
  A baseline is the only way to turn "it's slow" into a located bottleneck.
- More broadly, without baselines the SLI/SLO work (ADR-NEW-010, ADR-NEW-033) has nothing to anchor to, capacity
  planning is guesswork, and regressions ship silently.

This pairs with the design-gate ADR ([`adr_044`](adr_044_rag_vector_design_gate.md)): that gate measures **answer
quality**; this ADR measures **performance under load**. Both are prerequisites for defensible enterprise operation.

## Decision Drivers

- **Diagnosis needs a reference**: you can't find a regression or a bottleneck without a known-good number.
- **SLA defensibility**: SLI/SLO targets must be grounded in measured capacity.
- **Per-deployment reality**: customers differ (CPU-only Dem*scope, Azure F*H, on-prem) — baselines are per project, not
  one global number.
- **Cheap, scriptable, repeatable**: use a lightweight, code-defined tool that runs in CI and locally.
- **Catch regressions early**: a baseline that only exists once is nearly useless — it must be re-runnable.

## Decision

1. **Adopt Locust** (Python, code-defined scenarios — fits the stack) as the standard load-test tool. Define a shared
   scenario library for the common paths: chat/RAG query, document upload+ingest, and agent run end-to-end.

2. **Establish a baseline per environment**: run against **core** (reference deployment) and against each live
   customer's profile (or a representative replica), capturing **p50/p95/p99 latency, throughput, and error rate** at
   defined concurrency levels. Store the numbers as the documented baseline.

3. **Use the baseline to diagnose W\*P first**: run the scenarios against W*P (or a replica of its config/hardware) to
   locate the bottleneck the customer can't describe — this is the unblock path for the W*P performance complaint.

4. **Wire into CI/cadence**: run the load suite on a schedule (and before releases) against a staging deployment; alert
   on regression vs baseline. Feed the measured numbers into the SLI/SLO definitions (ADR-NEW-010 / ADR-NEW-033).

## Consequences

**Positive**

- W\*P's "it's slow" becomes a located, fixable bottleneck.
- SLI/SLO targets get a measured foundation; capacity planning stops being guesswork.
- Performance regressions are caught before customers feel them.

**Negative**

- Building realistic scenarios + representative data is real effort.
- Load-testing against (or near) production needs care to avoid impacting live customers — prefer staging/replica.
- Per-customer baselines add maintenance as deployments change.

**Open items**

- Where load tests run (dedicated staging vs per-customer replica) and how prod-like the data must be.
- Concurrency targets and pass/fail regression thresholds per scenario.
- Whether baselines live in arc42 ch. 10 (Quality) alongside the SLI/SLO definitions.

## References

- [Locust](https://locust.io/) — Python load-testing framework.
- Ties to: ADR-NEW-010 (SLI/SLO Definition), ADR-NEW-033 (SLI/SLO + business metrics).
- Related: [`adr_044`](adr_044_rag_vector_design_gate.md) (quality gate — the companion to this performance gate).
