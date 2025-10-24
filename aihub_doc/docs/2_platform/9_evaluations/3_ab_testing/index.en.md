---
title: A/B Testing & Agent Variants
index: 3
---

# A/B Testing & Agent Variants

::: warning Implementation Status
Production A/B testing with automatic traffic splitting is **not currently implemented** in the Swiss AI-Hub. However, the platform provides robust evaluation and experimentation capabilities that enable systematic agent comparison and quality assessment before deployment.
:::

## Current Capabilities

The platform provides several mechanisms for agent experimentation and comparison:

### 1. Evaluation-Based Agent Comparison

The AI-Hub's [evaluation framework](../) enables systematic comparison of agent variants:

**How It Works:**
- Create multiple agent configurations (variants) with different settings
- Run identical test datasets against each variant
- Compare results across three quality dimensions:
  - **Correctness**: Accuracy against reference answers
  - **Completeness**: Coverage of all query aspects
  - **Conciseness**: Response efficiency and brevity
- Analyze latency and token usage differences

**Best For:**
- Pre-deployment quality assessment
- Comparing different agent configurations (prompts, models, parameters)
- Validating improvements before rolling out to users

**Example Use Case:**
```
Variant A: RAG Agent with temperature=0.7, top_k=5
Variant B: RAG Agent with temperature=0.3, top_k=10

Run same 50-question dataset against both
Compare average correctness, completeness, conciseness scores
Select winning variant for deployment
```

### 2. Configuration-Based Agent Variants

The platform supports flexible agent configuration through the `AgentConfig` system:

**Key Features:**
- Each agent has a configurable `AgentConfig` object
- Parameters can be adjusted without code changes:
  - System prompts
  - LLM model selection
  - Temperature and other LLM parameters
  - RAG retrieval settings (top_k, similarity threshold)
  - Custom domain-specific configurations
- Agents can be deployed with different configurations to different environments

**Configuration Inheritance:**
```python
class RAGAgentConfig(AgentConfig):
    llm: ChatLLMConfig
    temperature: float = 0.7
    top_k: int = 5
    similarity_threshold: float = 0.75
    # ... additional parameters
```

**Best For:**
- Testing different prompt strategies
- Comparing LLM models (GPT-4 vs GPT-3.5, Azure OpenAI vs self-hosted)
- Tuning retrieval parameters for RAG agents
- A/B testing system instructions

### 3. Experiment Tracking & Results

The evaluation system provides comprehensive result tracking via Phoenix:

**Metrics Captured:**
- Per-evaluator scores (correctness, completeness, conciseness)
- Response latency (`latency_ms`)
- Token usage (prompt tokens, completion tokens, total)
- Experiment metadata (timestamp, agent_class, agent_id, locale)
- Individual question-level results with reasoning

**Result Analysis:**
- Summary statistics (count, average score)
- Detailed question-by-question breakdown
- Historical comparison across experiments
- Visual trace analysis in Phoenix UI

**Best For:**
- Comparing agent performance over time
- Identifying which changes improved or degraded quality
- Documenting agent iteration history

## What's Missing

### Production Traffic Splitting

The platform currently lacks:

1. **Automatic Traffic Allocation**
   - No percentage-based routing (e.g., 90% to Variant A, 10% to Variant B)
   - No gradual rollout (canary deployment)
   - No session-sticky variant assignment

2. **Runtime Variant Selection**
   - No automatic routing between agent versions based on user ID
   - No randomized variant assignment for live traffic
   - No real-time traffic distribution control

3. **Multi-Armed Bandit Algorithms**
   - No adaptive traffic allocation based on performance
   - No epsilon-greedy or Thompson sampling strategies
   - No automatic promotion of winning variants

### Statistical Analysis

The platform currently lacks:

1. **Sample Size Calculation**
   - No automated determination of required experiment size
   - No power analysis for detecting meaningful differences
   - No minimum detectable effect (MDE) estimation

2. **Significance Testing**
   - No p-value computation for result differences
   - No confidence interval calculation
   - No Bayesian credible intervals

3. **Early Stopping**
   - No sequential testing frameworks
   - No automated experiment termination when significance is reached
   - No false discovery rate control

### Experiment Management

The platform currently lacks:

1. **Experiment Lifecycle**
   - No scheduled start/stop times
   - No pause/resume functionality
   - No experiment state tracking (draft, running, completed, archived)

2. **Production Monitoring**
   - No real-time metrics dashboard during live A/B tests
   - No user experience quality tracking per variant
   - No automatic rollback on quality degradation

## Practical A/B Testing Workflows

### Pre-Deployment Comparison (Current Approach)

This is the recommended approach with current capabilities:

**Step 1: Define Variants**

Create two agent configurations:

```yaml
# config_variant_a.yaml
agent_id: "rag_agent_v1"
temperature: 0.7
system_prompt: "You are a helpful assistant..."
top_k: 5

# config_variant_b.yaml
agent_id: "rag_agent_v2"
temperature: 0.3
system_prompt: "You are a precise, factual assistant..."
top_k: 10
```

**Step 2: Create Evaluation Dataset**

Build a representative test dataset with 20-50 questions:
- Cover typical user queries
- Include edge cases
- Ensure questions represent real production distribution

**Step 3: Run Experiments**

Execute evaluation experiments for each variant:
1. Run Variant A against test dataset → Experiment "RAG_v1_2025_10_24"
2. Run Variant B against test dataset → Experiment "RAG_v2_2025_10_24"

**Step 4: Compare Results**

Analyze results in Phoenix:
- Compare average scores for correctness, completeness, conciseness
- Review individual question results for patterns
- Check latency differences
- Examine token usage for cost implications

**Step 5: Deploy Winner**

Deploy the variant with superior performance to production.

### Manual Production A/B Testing

If you need to test variants with real users:

**Approach 1: Scheduled Deployment**

Deploy variants sequentially and compare metrics:

1. **Week 1**: Deploy Variant A to production
   - Monitor user interactions via Phoenix traces
   - Track quality metrics manually
   - Collect user feedback

2. **Week 2**: Deploy Variant B to production
   - Monitor using same metrics
   - Compare against Variant A baseline
   - Account for external factors (day of week, seasonality)

**Limitations**:
- Time-based confounds (user behavior may change)
- No simultaneous comparison
- Requires careful metric tracking

**Approach 2: User Group Segmentation**

Deploy different variants to different user groups:

1. **Group A (e.g., Department 1)**: Uses Variant A
2. **Group B (e.g., Department 2)**: Uses Variant B

Deploy separate agent instances or route users via different agent IDs:
- Configure access permissions per group
- Users in Group A interact with `agent_variant_a`
- Users in Group B interact with `agent_variant_b`
- Monitor Phoenix traces per agent_id

**Limitations**:
- Requires manual user segmentation
- No randomization (groups may have inherent differences)
- Complex to manage multiple deployments

**Approach 3: API-Level Routing**

If you have control over the frontend or API layer:

Implement custom routing logic:

```python
# Pseudo-code example (not implemented in platform)
def route_to_agent(user_id: str) -> str:
    # Hash user ID to assign variant deterministically
    if hash(user_id) % 100 < 10:  # 10% to Variant B
        return "rag_agent_variant_b"
    else:  # 90% to Variant A
        return "rag_agent_variant_a"
```

Call appropriate agent via [Agent Interaction REST API](../../16_api/2_agent_interaction_api/).

**Limitations**:
- Requires custom client-side or middleware implementation
- No built-in statistical analysis
- Manual result aggregation required

## Best Practices

### 1. Start with Offline Evaluation

Always use the evaluation framework before production testing:

- **Faster Iteration**: Run 50 experiments in an hour vs. days of live testing
- **No User Impact**: Test risky changes without affecting real users
- **Controlled Environment**: Eliminate external confounds
- **Comprehensive Coverage**: Test edge cases that may be rare in production

### 2. Use Representative Test Data

Create evaluation datasets that:
- Match production query distribution
- Include both common and rare question types
- Cover success and failure scenarios
- Represent diverse user needs

### 3. Define Success Metrics

Before running experiments, decide:
- **Primary Metric**: What determines the winner? (e.g., correctness score)
- **Secondary Metrics**: Additional considerations (e.g., latency, token cost)
- **Guardrail Metrics**: Minimum thresholds (e.g., completeness must stay above 4.0)

### 4. Document Experiment Rationale

Use Phoenix experiment names and descriptions to:
- Explain what hypothesis you're testing
- Document configuration differences between variants
- Record expected outcomes
- Track learnings from results

### 5. Iterate Based on Results

When experiments show clear differences:
- **Winning Variant**: Deploy to production
- **Close Call**: Run additional experiments with more test questions
- **Both Poor**: Iterate further before deployment

## Statistical Considerations

When comparing agent variants manually, consider:

### Sample Size

Aim for at least 20-30 test questions per experiment:
- More questions → more reliable results
- Reduces noise from individual question variance
- Enables detection of smaller performance differences

### Practical Significance

A statistically significant difference may not be practically meaningful:
- **0.1 star difference**: Likely not worth deployment effort
- **0.5 star difference**: Noticeable improvement, consider deploying
- **1.0+ star difference**: Major improvement, deploy immediately

### Evaluation Reliability

LLM-based judges can have variance:
- Run the same experiment twice to check consistency
- If results differ significantly, increase dataset size
- Consider using stronger judge models for more reliable scoring

## Related Documentation

- [Agent Evaluations](../) - Core evaluation framework
- [Agent Interaction REST API](../../16_api/2_agent_interaction_api/) - API for programmatic agent invocation
- [Agent Configuration](../../5_agents/1_fundamentals/) - Understanding agent configuration and workflows
- [Observability](../../12_auditing/2_low_level_traces/) - Monitoring production agent interactions

## Future Roadmap

Potential future enhancements for production A/B testing:

- **Traffic Splitting**: Automatic percentage-based routing between agent variants
- **Canary Deployment**: Gradual rollout with automated quality monitoring
- **Multi-Armed Bandits**: Adaptive traffic allocation based on real-time performance
- **Statistical Testing**: Built-in significance calculation and confidence intervals
- **Experiment Scheduler**: Time-based experiment start/stop automation
- **Real-Time Dashboards**: Live A/B test monitoring during production experiments
- **Automatic Rollback**: Quality-based automatic reversion to baseline variant
- **Segmentation Engine**: User cohort assignment and stratified analysis

Organizations interested in these capabilities should contact the AI-Hub team to discuss requirements and timelines.
