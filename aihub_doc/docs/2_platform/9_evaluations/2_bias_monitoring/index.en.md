---
title: Bias Monitoring & Model Drift Detection
index: 2
---

# Bias Monitoring & Model Drift Detection

::: warning Implementation Status
Dedicated bias monitoring and automated model drift detection are **not currently implemented** in the Swiss AI-Hub. However, the platform provides a strong foundation through its evaluation framework and observability infrastructure that can be extended to support these capabilities.
:::

## Current Capabilities

The platform provides several building blocks that form the foundation for bias monitoring and drift detection:

### 1. Evaluation Framework

The AI-Hub includes a comprehensive [evaluation system](../) that can be extended for bias and fairness assessment:

- **Dataset Management**: Create test datasets with diverse inputs
- **LLM-Based Judges**: Extensible evaluator framework with custom metrics
- **Experiment Tracking**: Run evaluations and track results over time via Phoenix
- **Multi-Dimensional Scoring**: Three built-in evaluators (Correctness, Completeness, Conciseness)

**Key Insight**: The evaluation framework's judge architecture can be extended with custom evaluators for fairness metrics such as demographic parity, equalized odds, or disparate impact.

### 2. Observability Infrastructure

The platform's OpenTelemetry integration provides comprehensive monitoring:

- **Distributed Tracing**: End-to-end trace capture across all agent interactions
- **Semantic Events**: Structured events for LLM calls, retrievals, embeddings, and reranking
- **Token Tracking**: Prompt and completion token counts for all LLM interactions
- **Latency Monitoring**: Response time tracking at every layer
- **Phoenix Integration**: Visual trace analysis and historical data storage

**Key Insight**: These traces provide the raw data needed to detect performance degradation and quality drift over time.

### 3. Quality Metrics

Current quality metrics that serve as drift detection baselines:

- **Correctness**: Accuracy against reference answers
- **Completeness**: Coverage of all query aspects
- **Conciseness**: Response efficiency
- **Latency**: Response time tracking (`latency_ms`)
- **Token Usage**: Resource consumption patterns

## What's Missing

### Bias & Fairness Monitoring

The platform currently lacks:

1. **Demographic Parity Metrics**
   - No tracking of outcome distributions across demographic groups
   - No protected attribute monitoring
   - No disparity calculation

2. **Fairness Evaluators**
   - No built-in bias detection evaluators
   - No equalized odds or equality of opportunity metrics
   - No calibration analysis across subgroups

3. **Sensitive Attribute Tracking**
   - No systematic capture of demographic information in evaluation datasets
   - No subgroup performance analysis
   - No intersectional fairness assessment

4. **Bias Detection Alerts**
   - No automated threshold-based alerting for fairness violations
   - No dashboard visualization of bias metrics
   - No historical bias trend tracking

### Model Drift Detection

The platform currently lacks:

1. **Automated Baseline Comparison**
   - No automatic tracking of metric degradation against historical baselines
   - No statistical significance testing for performance changes
   - No confidence interval calculation

2. **Drift-Specific Metrics**
   - No concept drift detection (input distribution changes)
   - No covariate shift monitoring
   - No label drift detection

3. **Alerting & Notifications**
   - No automated alerts when quality metrics fall below thresholds
   - No proactive notification of performance degradation
   - No scheduled drift detection runs

4. **Root Cause Analysis**
   - No automated identification of which inputs cause degradation
   - No segment-specific performance tracking
   - No correlation analysis between drift and external factors

## Extending the Platform

### Approach 1: Custom Bias Evaluators

You can extend the evaluation framework with custom bias-focused evaluators:

**1. Create Bias-Specific Datasets**

Build evaluation datasets that include:
- Diverse demographic representations in test questions
- Metadata fields for protected attributes (gender, age, ethnicity, etc.)
- Multiple question variants testing similar concepts across groups

**2. Implement Custom Judge Evaluators**

Extend the existing `PhoenixExperimentEvaluator` to add fairness judges:

```python
# Example conceptual extension (not implemented)
class FairnessEvaluator(BaseEvaluator):
    """Custom evaluator for demographic parity assessment."""

    async def evaluate(self, response: str, reference: str, metadata: dict) -> JudgeOutput:
        # Analyze response for demographic bias
        # Compare outcomes across protected groups
        # Return fairness score (0.0-1.0)
        pass
```

**3. Run Subgroup Analysis**

Execute experiments separately for each demographic subgroup and compare results:
- Run standard evaluations on subgroup-specific datasets
- Aggregate and compare correctness, completeness scores across groups
- Calculate statistical disparity metrics

**Integration**: Results are automatically logged to Phoenix for historical tracking and visualization.

### Approach 2: OpenTelemetry-Based Drift Detection

Leverage the existing observability infrastructure for drift monitoring:

**1. Establish Performance Baselines**

Use Phoenix to:
- Query historical evaluation experiment results
- Calculate baseline metrics (mean, standard deviation, percentiles)
- Store baseline values for comparison

**2. Schedule Regular Evaluations**

Implement scheduled evaluation runs:
- Run the same evaluation datasets weekly or monthly
- Capture results in Phoenix with timestamped experiments
- Compare current results against baseline

**3. Implement Statistical Tests**

Add custom analysis logic to detect significant changes:
- Mann-Whitney U test for non-parametric comparison
- Two-sample t-test for metric means
- Chi-square test for categorical distributions

**4. Alert on Degradation**

Build alerting logic that:
- Queries Phoenix for recent experiment results
- Calculates deviation from baseline
- Triggers notifications when thresholds are exceeded (e.g., >10% accuracy drop)

### Approach 3: External Integration

Integrate specialized bias and fairness libraries:

**Recommended Tools:**
- **AI Fairness 360 (AIF360)**: IBM's fairness metrics and bias mitigation library
- **Fairlearn**: Microsoft's fairness assessment and algorithm toolkit
- **What-If Tool**: Interactive ML fairness and interpretability dashboard

**Integration Strategy:**
1. Export evaluation results from Phoenix to external analysis tools
2. Process results through fairness libraries
3. Generate bias reports and fairness scorecards
4. Feed insights back into evaluation datasets for iterative improvement

## Practical Workarounds

Until dedicated bias monitoring is implemented, consider these approaches:

### Manual Bias Assessment

1. **Create Diverse Test Datasets**
   - Include test questions representing different demographics
   - Document demographic attributes in dataset descriptions
   - Organize datasets by subgroup for comparative evaluation

2. **Run Comparative Experiments**
   - Execute separate experiments for each demographic subset
   - Export results from Phoenix (via API or web interface)
   - Manually compare performance metrics across groups
   - Document findings in experiment descriptions

3. **Regular Quality Reviews**
   - Schedule monthly evaluation runs against standard datasets
   - Track trends in correctness, completeness, conciseness over time
   - Investigate any degradation patterns

### Monitoring Best Practices

1. **Establish Quality Baselines**
   - Run comprehensive evaluations at initial agent deployment
   - Document baseline scores for all three metrics
   - Use these as reference points for future comparisons

2. **Track Performance Over Time**
   - Name experiments consistently with timestamps (e.g., "RAG_Agent_2025_10_24")
   - Maintain a spreadsheet or dashboard tracking key metrics
   - Look for downward trends in any metric

3. **Investigate Anomalies**
   - When scores drop significantly, review individual test case details in Phoenix
   - Identify patterns in failing examples
   - Correlate performance changes with system updates or knowledge base changes

## Related Documentation

- [Agent Evaluations](../) - Core evaluation framework and experiment execution
- [Observability](../../12_auditing/2_low_level_traces/) - OpenTelemetry tracing and Phoenix integration
- [Guards](../../13_language_models/3_guards/) - Real-time safety and quality controls
- [Compliance](../../19_compliance/) - Regulatory considerations for bias and fairness

## Future Roadmap

Potential future enhancements for bias monitoring and drift detection:

- **Automated Fairness Evaluators**: Built-in demographic parity and equalized odds metrics
- **Drift Detection Service**: Background service comparing current performance to baselines
- **Bias Dashboard**: Dedicated UI for fairness metric visualization and historical tracking
- **Alerting System**: Configurable thresholds and notifications for quality degradation
- **Subgroup Analysis**: Automatic performance comparison across demographic segments
- **Integration with Fairness Libraries**: Native support for AIF360, Fairlearn, or similar tools

Organizations interested in these capabilities should contact the AI-Hub team to discuss priorities and timelines.
