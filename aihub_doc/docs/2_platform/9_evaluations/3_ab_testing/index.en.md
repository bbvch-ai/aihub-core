---
title: A/B Testing & Agent Variants
index: 3
---

# A/B Testing & Agent Variants

::: warning Implementation Status
Production A/B testing with automatic traffic splitting is **not currently implemented**. The platform provides evaluation-based comparison capabilities for pre-deployment testing.
:::

## What Exists

### Evaluation-Based Comparison
- **Run experiments** against identical test datasets for different agent variants
- **Compare results** across three metrics: Correctness, Completeness, Conciseness
- **Track experiments** in Phoenix with full result history
- **Analyze differences** in quality, latency, and token usage

### Configuration-Based Variants
- **AgentConfig system**: Flexible agent configuration (`AgentConfig.py`)
- **Adjustable parameters**: System prompts, LLM models, temperature, RAG settings
- **Multiple configs**: Deploy different configurations to different environments
- **No code changes**: Configuration-only variant testing

## What's Missing

### Production Traffic Splitting
- No percentage-based routing (e.g., 90% A, 10% B)
- No gradual rollout or canary deployment
- No session-sticky variant assignment
- No automated variant selection

### Statistical Analysis
- No sample size calculation
- No p-value computation or confidence intervals
- No automated significance testing
- No early stopping mechanisms

### Experiment Management
- No scheduled start/stop times
- No pause/resume functionality
- No real-time production A/B dashboards
- No automatic rollback on degradation

## Pre-Deployment Comparison Workflow

**Current recommended approach:**

1. **Create variants**: Define two agent configurations
2. **Build dataset**: 20-50 representative test questions
3. **Run experiments**: Execute both variants against same dataset
4. **Compare in Phoenix**: Analyze scores, latency, token costs
5. **Deploy winner**: Roll out superior variant to production

## Manual Production Testing

If you need real user data:

### Approach 1: Sequential Deployment
Deploy variants in sequence (Week 1: A, Week 2: B), compare metrics manually. Account for temporal effects.

### Approach 2: User Group Segmentation
Deploy different variants to different user groups, monitor separately via Phoenix traces.

### Approach 3: API-Level Routing
Implement custom routing logic in client or middleware layer, call different agent IDs via [Agent Interaction API](../../16_api/2_agent_interaction_api/).

## Best Practices

- **Start with offline evaluation** before production testing
- **Use representative test data** matching production queries
- **Define success metrics** before running experiments
- **Track with timestamps**: Name experiments like "RAG_Agent_2025_10_24"
- **Practical significance**: >0.5 star difference is meaningful

## Related Documentation

- [Agent Evaluations](../) - Core evaluation framework
- [Agent Interaction REST API](../../16_api/2_agent_interaction_api/) - API for programmatic agent invocation
- [Agent Fundamentals](../../5_agents/1_fundamentals/) - Understanding agent configuration
