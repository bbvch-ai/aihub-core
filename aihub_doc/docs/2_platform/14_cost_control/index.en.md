---
title: Cost control
---

# Cost control

AI agents cost money to operate. The AI-Hub tracks these costs so you can optimize spending, justify investments, and forecast budgets.

## How AI costs work

AI providers charge based on token usage. Tokens are small chunks of text (roughly 4 characters) that models process.

Cost model comparison:

| Model | Type | Cost Structure |
|-------|------|----------------|
| API (Pay-per-token) | Variable OPEX | Pay providers (OpenAI, Google) for each token processed |
| Locally Hosted | CAPEX + Fixed OPEX | Capital expense for hardware (GPUs, servers) plus ongoing costs for power and MLOps staff. Per-token cost is $0, but fixed infrastructure cost is high |

Each interaction consumes different types of tokens at different price points:

::: details Prompt tokens
Your input to the AI, including questions, conversation history, system prompts, and retrieved documents. Longer prompts cost more.
:::

::: details Completion tokens
The AI-generated responses. Longer, more detailed responses cost more.
:::

::: details Embedding tokens
Document processing for search and retrieval. Typically cheaper than text generation.
:::

::: details Model tiers

| Tier | Examples | Use Case | Cost |
|------|----------|----------|------|
| Flagship | GPT-5 | Complex reasoning, high-accuracy tasks | Highest |
| Balanced | GPT-5 mini | Standard workflows, internal assistants | Medium |
| Efficient | GPT-5 nano | High-volume simple tasks, classification | Lowest |

:::

## Cost tracking

The AI-Hub tracks costs for each conversation. When you chat with an agent, the platform records token usage and calculates the cost. This information appears in the conversation thread.

Tracking works for all AI models, whether you use cloud services like OpenAI or self-hosted models. For self-hosted models, you can assign a cost value to track spending consistently.

You can view cost information per conversation to see which questions are most expensive. This helps with agent design decisions, model selection, and budget planning.

## Budgets and rate limits

::: warning Not currently configured
Budget and rate limiting capabilities exist but are not enabled by default. This feature hasn't been tested yet.
:::

The platform can enforce spending limits and usage restrictions. When enabled, administrators can set:

- Budget caps: Block requests when users exceed spending limits
- Usage alerts: Notify when approaching budget thresholds
- Rate limits: Control how many requests or tokens users can consume per minute
- Concurrent request limits: Restrict simultaneous AI operations

These controls require environment configuration during deployment.

## Optimization strategies

### Model selection

Match the model tier to your task. Use flagship models (GPT-5) for complex, customer-facing, or high-accuracy tasks. Use balanced models (GPT-5 mini) for internal assistants or standard workflows. Use efficient models (GPT-5 nano) for classification, data extraction, or high-frequency chat.

### Locally hosted models

Local hosting shifts spending from variable per-token fees to fixed infrastructure costs. Organizations choose this for data privacy (HIPAA, GDPR), compliance, and IP protection, not for immediate cost savings. It requires capital investment (GPUs, servers) and ongoing operational costs (power, MLOps staff).
