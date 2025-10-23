---
title: Cost Control
index: 14
---

# Cost Control

AI-powered agents can deliver tremendous value, but they come with operational costs that must be understood and
managed. The AI-Hub provides comprehensive cost tracking to help you optimize spending, justify AI investments, and
forecast budgets accurately.

## Understanding AI Costs

The cost of an AI interaction is primarily driven by **token usage**. Tokens are small chunks of text (roughly 4
characters). AI providers charge based on how many tokens are processed.

There are two main cost models to consider:

1. **API (Pay-per-token):** This is a variable, operational expense (OPEX). You pay a provider (like OpenAI) for each
   token you send (prompt) and receive (completion).
2. **Locally Hosted (Fixed Cost):** This is a capital expense (CAPEX) and fixed OPEX. You pay upfront for hardware
   (GPUs, servers) and ongoing costs for power and specialized MLOps staff. The per-token cost is \$0, but the fixed
   infrastructure cost is high.

Costs are driven by three main token types:

- **Prompt Tokens**: The input you send to the AI (your question, conversation history, system prompts, retrieved
  documents). Longer prompts cost more.
- **Completion Tokens**: The AI-generated response. Longer, more detailed responses cost more.
- **Embedding Tokens**: Document processing for search and retrieval (RAG agents). This is generally cheaper than text
  generation.

::: info Why Model Tiers Have Different Costs
The 'right' model is a trade-off between power and price.

- **Flagship Models (e.g., GPT-5):** Offer the most power and reasoning at the highest cost.
- **Balanced Models (e.g., GPT-5 mini, GPT-4o):** Provide an excellent mix of performance and price, suitable for most
  standard tasks.
- **Efficient Models (e.g., GPT-5 nano):** Are much cheaper and faster, ideal for high-volume, simple, or on-device
  tasks.
:::

## Cost Tracking and Visibility

The AI-Hub automatically tracks all AI usage and costs without any configuration. Every agent run generates real-time
cost data linked to the specific agent, conversation, and user.

This is powered by an integration with **LiteLLM**, a unified proxy that sits between your agents and all model
providers—including AI providers (OpenAI, Azure, etc.) *and your own locally hosted model endpoints*. This provides a
single interface for all models and enables centralized monitoring, budget enforcement, and rate limiting.

::: tip How It Works
The platform uses `LLMCostEvent` objects to track token counts and costs. For locally hosted models, you can set a
*custom price* (e.g., amortized hardware/energy cost) in the LiteLLM config to track its "cost" in the same unified
dashboard as your API models.
:::

The platform allows you to analyze costs from several angles:

- **Per-Conversation**: Identify which types of questions are most expensive.
- **Per-Agent**: Compare costs between simple Q&A agents and complex RAG agents to calculate ROI.
- **Per-User**: Track usage by individual users or departments to allocate costs or detect anomalies.

::: info LiteLLM Dashboard
You can also access the LiteLLM web interface at its configured proxy URL to view real-time cost analytics, manage user
budgets, and configure rate limits.
:::

## Enforceable Budgets and Rate Limits

::: warning Experimental Feature
The budget and rate limiting features described in this section are **not yet fully tested in production**. Use with
caution and test thoroughly in a development environment before relying on them.
:::

Beyond tracking, the LiteLLM proxy is designed to provide **enforceable cost controls** to prevent budget overruns.

You can configure **Budget Limits** for individual users via environment variables, such as `USER_MAX_BUDGET` (a hard
cap that blocks requests), `USER_SOFT_BUDGET` (a warning threshold), and `USER_BUDGET_DURATION` (the reset period, e.g.,
`"1mo"`).

Similarly, **Rate Limits** control request volume with `USER_TPM_LIMIT` (tokens per minute), `USER_RPM_LIMIT` (requests
per minute), and `USER_MAX_PARALLEL_REQUESTS` (concurrent requests).

**Example Configuration:**

```bash
# Monthly budget limits
USER_MAX_BUDGET=100.0         # Hard limit: $100/month per user
USER_SOFT_BUDGET=75.0         # Alert at $75/month
USER_BUDGET_DURATION="1mo"    # Reset monthly

# Rate limits
USER_TPM_LIMIT=150000         # Max 150k tokens/minute
USER_RPM_LIMIT=100            # Max 100 requests/minute
```

::: warning User Experience Considerations
When users hit these limits, they receive error messages. Communicate these limits clearly to users in advance to avoid
frustration.
:::

## Cost Strategies and Optimization

Reducing costs requires a strategic approach to model selection, deployment, and prompt engineering.

### Choose the Right Model for the Task

Not every task needs the most expensive model. Use the model *tier* that matches your needs.

- **High-Stakes Reasoning:** Use flagship models (e.g., **GPT-5**) for complex, customer-facing, or high-accuracy tasks.
- **General Use:** Use balanced models (e.g., **GPT-5 mini** or **GPT-4o**) for internal assistants or standard
  workflows.
- **Simple/High-Volume:** Use efficient models (e.g., **GPT-5 nano**) for classification, data extraction, or
  high-frequency chat.

### Consider Locally Hosted Models

This is a strategic decision, not a simple cost-saving one. It shifts spending from *variable per-token fees* to *fixed
infrastructure and personnel costs*.

- **Primary Benefits:** The main drivers for local hosting are **data privacy** (HIPAA, GDPR), **compliance**, **IP
  protection**, and eliminating vendor dependency—not immediate cost savings.
- **Cost Trade-off:** This requires significant upfront capital investment (GPUs, servers) and high ongoing operational
  costs (power, and specialized MLOps staff).
- **Best-Fit Scenarios:** Local hosting is ideal for:
  1. **High-Volume, Stable Workloads:** Where you can run your hardware at high utilization.
  2. **Small, Specialized Tasks:** Running a small, efficient model (like a `GPT-5 nano` variant or an open-source
     model) locally for a specific, high-frequency task can make the marginal cost per-inference near-zero.

### Other Optimization Strategies

- **Optimize Prompts and Context:** Every token costs money. Keep system prompts concise and limit the number of
  retrieved documents for RAG agents.
- **Tune Response Length:** Configure agents to be concise. Avoid asking agents to "explain in detail" unless necessary.
- **Optimize Evaluations:** Start tests with small datasets (10-20 examples) and consider using cheaper models (like
  `GPT-5 nano`) for initial workflow validation before scaling.
- **Establish a Monitoring Routine:** Assign ownership for cost monitoring. Check weekly for spikes and review monthly
  reports to detect anomalies against your baseline.

## Common Questions

::: details What's a "normal" cost per conversation?
This varies widely. A simple Q&A on an efficient model might cost fractions of a cent, while a complex, multi-hop RAG
agent using a flagship model could cost \$0.50 or more. Use your agent's cost data to establish your own baselines.
:::

::: details Why did costs suddenly increase?
Common causes include: increased user adoption, longer conversations, more document retrieval, model upgrades (e.g.,
switching from **GPT-4o** to **GPT-5**), or enabling additional guards.
:::

::: details How do we reduce costs without sacrificing quality?
Focus on efficiency: choose the *right-tier* model for the task (e.g., using **GPT-5 mini** instead of the full
**GPT-5** for simple queries), optimize prompts, and limit unnecessary context.
:::

::: details Can we set hard budget limits?
The LiteLLM proxy supports budget limit configuration (`USER_MAX_BUDGET`), but this feature is **experimental**. For
now, monitor costs regularly and test the configuration thoroughly in a dev environment first.
:::

::: details How accurate is the cost tracking?
For API models, it is highly accurate, based on the provider's published rates. For locally hosted models, its accuracy
depends on the *custom price* you set in the LiteLLM config to represent your amortized internal costs.
:::

::: details Are there hidden costs not being tracked?
Yes. The platform tracks LLM-related costs.

- **API:** It does not track infrastructure costs (compute, storage) for the AI-Hub platform itself.
- **Local Hosting:** It *especially* does not track the primary costs of this strategy: GPU/server hardware, power,
  cooling, and MLOps personnel salaries. These must be budgeted separately.
    :::

<!-- end list -->
