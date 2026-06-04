# Observability Completeness — Metrics Producers, Bot Tracing, Host Monitoring, Alerting & SLO

**Status**: Proposed (2026-05-29) **Severity**: P1 (operability, incident response, SLO)
**Drives**: Overview §3.1 #18 (no alerting — partially mitigated), §3.1 #19 (no business metrics + SLI/SLO — partially
mitigated), §10 Observability (G7.1 bot OTEL); supersedes/absorbs the SigNoz-region concern in §5.8

## Context

SigNoz is now wired: the OTEL Collector (`infra/configs/otel/otel-config.*.yml`) has `service.pipelines` for **traces,
metrics, and logs**, all exporting via a generic `otlp/cloud` exporter to `OTEL_CLOUD_ENDPOINT`
(`ingest.eu.signoz.cloud:443`), plus a `traces/langfuse` pipeline for OpenInference LLM traces. So the **sink and the
transport are in place**. But a verified read of the code (2026-05-29) shows the *producers* and the *operational
layer* are not:

- **Metrics are effectively empty from the platform.** There is **no `MeterProvider` / `OTLPMetricExporter` in
  `packages/core`** (`infrastructure/opentelemetry/` only configures tracing + log export). The `metrics` pipeline in
  the collector is an empty pipe — only OpenWebUI (`ENABLE_OTEL_METRICS: True`) and LiteLLM self-emit. No business
  metrics exist (agent runs, HITL escalations, RAG latency, ingestion rate, token/cost).
- **The bot scope has no OTEL at all** (grep of `packages/bot` → zero references) → traces break at the bot boundary
  (G7.1).
- **No host/system telemetry on Gen 1.** The collector defines only the `otlp` receiver (app push) — no `hostmetrics`,
  `filelog`/`journald`, `docker_stats`, or `prometheus` receiver. Host metrics + system logs exist only via the Gen 2
  `aihub-playbook` SigNoz role, so **all 5 Gen 1 production customers have no host monitoring**.
- **Logs are unstructured** (text, default level) — hard to query/correlate in any backend.
- **No alert rules as-code and no on-call routing in the repo.** SigNoz Cloud *can* alert, but rules are not
  versioned/managed here; the only failure signal as-code is the Dagster run-failure → Apprise sensor (pipelines only).
- **No formal SLI/SLO.**
- **Sovereignty**: observability data leaves tenant infra to **SigNoz Cloud (EU)** — no Swiss region; self-hosting is
  not decided.

Net: "we have SigNoz" is true at the *plumbing* level, but full-stack monitoring (logs + metrics + traces) with
alerting and SLOs is **not** complete — Overview §3.1 #18 and #19 remain HIGH (now annotated *partially mitigated*).

## Decision Drivers

- **Failures must be noticed** without a customer reporting them (today's failure mode — see W*P §3.5 #11).
- **Metrics are the missing leg** — traces are strong, metrics are near-zero from core.
- **Gen 1 customers are blind at the host level** while they remain the entire production fleet.
- **Sovereignty** — observability data residency must be an explicit decision, not a default.
- **Reuse, don't rebuild** — the collector, OTLP transport, and instrumentor seam already exist; this ADR fills
  producers + receivers + rules, not a new platform.

## Decision

Implement an 8-item completeness package (ordered by impact):

1. **Core metrics producer.** Add `MeterProvider` + `OTLPMetricExporter` to `OpenTelemetrySettings` /
   `AihubInstrumentor`, and emit business metrics: `agent_runs_total`, `hitl_escalations_total`, `rag_query_latency`,
   `ingestion_docs_total`, `llm_tokens_total` / `llm_cost`, `events_published_total` / `events_failed_total`.
2. **Bot OTEL.** Call `AihubInstrumentor` in the `packages/bot` entrypoint (as api/agents already do) → unbroken traces
   to the Teams/Slack boundary (closes G7.1).
3. **Host + system telemetry for Gen 1.** Add `hostmetrics` + `filelog`/`journald` (and optionally `docker_stats`)
   receivers to `infra/configs/otel/otel-config.*.yml` so every Gen 1 customer gets CPU/mem/disk + container logs.
4. **Structured logging.** Emit JSON logs with configurable level across services (replace text logs).
5. **Alert rules as-code + on-call.** Version alert rules in the repo (SigNoz alert API / IaC) for: error rate, p95
   latency, JetStream DLQ depth, ingestion failure, LLM cost spike, healthcheck down; wire on-call
   (PagerDuty/OpsGenie). Pairs with proposed `adr_032`.
6. **SLI/SLO definition.** Document per-service SLIs/SLOs (availability, latency p95, ingest success rate) + error
   budget. Pairs with proposed `adr_010` / `adr_033`.
7. **Observability sovereignty decision.** Decide self-hosted SigNoz vs a compliant region; capture rationale (ties
   §5.8 SigNoz-EU concern and `adr_000`).
8. **Per-tenant cost attribution.** Tag traces/metrics + cost events by tenant in Langfuse (enables showback).

## Consequences

**Positive**

- Full-stack observability (logs + metrics + traces) with the metrics leg actually populated.
- Failures are detected and routed to on-call instead of surfacing as customer complaints.
- Gen 1 fleet gains host-level visibility without waiting for Gen 2/Gen 3 migration.
- SLOs make reliability measurable and contractible; sovereignty of telemetry becomes explicit.

**Negative**

- Touches multiple scopes (core instrumentor, bot, collector templates) + a deployment change to regenerate Gen 1
  compose.
- Self-hosting SigNoz (if chosen in #7) adds operational surface (ClickHouse, query service).

**Severity downgrade criteria**

- **§3.1 #19 → MEDIUM** when (1)+(2)+(6) land: core emits business metrics, bot is traced, SLOs documented.
- **§3.1 #18 → MEDIUM** when (5) lands: alert rules as-code + on-call routing.
- Full-stack monitoring considered "sufficient" only when items 1–6 are complete; 7–8 are hardening.

**Open items**

- Whether to adopt SigNoz alerting natively or run Prometheus + AlertManager alongside (overlaps `adr_032`).
- Self-hosted SigNoz vs Cloud region for #7.

## References

- `infra/configs/otel/otel-config.latest.yml` — collector pipelines (traces/metrics/logs → `otlp/cloud`; +
  `traces/langfuse`).
- `packages/core/swiss_ai_hub/core/infrastructure/opentelemetry/` — `open_telemetry_settings.py` (tracing + log export,
  **no metrics**), `aihub_instrumentor.py`.
- Overview §3.1 #18, §3.1 #19, §10 Observability, §5.8 (SigNoz Cloud region).
- Related proposed ADRs: `adr_032` (Prometheus + AlertManager + on-call), `adr_010` / `adr_033` (SLI/SLO),
  `adr_000` (sovereignty), `adr_049` (IGS Phoenix → Langfuse).
