---
title: Bias Monitoring & Model Drift Detection
index: 2
---

# Bias Monitoring & Model Drift Detection

::: warning Implementation Status
Dedicated bias monitoring and automated model drift detection are **not currently implemented**. The platform provides foundational capabilities through its evaluation framework and observability infrastructure.
:::

## What Exists

### Evaluation Framework
- **Dataset Management**: Create test datasets via [evaluation system](../)
- **LLM Judges**: Three built-in evaluators (Correctness, Completeness, Conciseness)
- **Experiment Tracking**: Run evaluations and track results in Phoenix
- **Extensibility**: Judge architecture supports custom evaluators

### Observability Infrastructure
- **OpenTelemetry Tracing**: End-to-end trace capture via `AihubInstrumentor`
- **Semantic Events**: LLM calls, retrievals, embeddings tracked as structured events
- **Metrics**: Token counts, latency, performance data stored in Phoenix
- **Historical Data**: All traces preserved for trend analysis

## What's Missing

### Bias & Fairness
- No demographic parity or fairness metrics
- No protected attribute tracking in datasets
- No bias-specific evaluators
- No automated disparity detection or alerting

### Drift Detection
- No automated baseline comparison
- No statistical significance testing
- No drift-specific metrics (concept drift, covariate shift)
- No automated alerting on quality degradation

## Practical Workarounds

### Manual Bias Assessment

1. **Create demographic-specific test datasets** in the evaluation system
2. **Run separate experiments** for each demographic group
3. **Compare results manually** by exporting from Phoenix
4. **Track trends** using timestamped experiment names

### Manual Drift Monitoring

1. **Establish baseline**: Run comprehensive evaluation at deployment
2. **Schedule regular runs**: Execute same dataset monthly
3. **Compare metrics**: Check if scores drop >10% from baseline
4. **Investigate**: Review failing test cases in Phoenix for patterns

## Extension Options

The evaluation framework can be extended with custom evaluators for fairness metrics. The OpenTelemetry infrastructure provides data for custom drift detection logic. External libraries (AIF360, Fairlearn) can process exported evaluation results.

## Related Documentation

- [Agent Evaluations](../) - Core evaluation framework
- [Observability](../../12_auditing/2_low_level_traces/) - Tracing and Phoenix integration
