---
title: Cost Control
index: 14
---

# Cost Control

AI-powered agents come with operational costs that must be understood and managed. The AI-Hub provides comprehensive cost tracking to help you optimize spending, justify AI investments, and
forecast budgets accurately.

## Understanding AI Costs

AI interaction costs are primarily driven by **token usage**—small chunks of text (roughly 4 characters) that AI providers charge to process.

**Cost Model Comparison**

| Model                     | Type               | Cost Structure                                                                                                                                         |
|---------------------------|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **API (Pay-per-token)**   | Variable OPEX      | Pay providers (OpenAI, Google) for each token processed                                                                                                |
| **Locally Hosted**        | CAPEX + Fixed OPEX | Capital expense for hardware (GPUs, servers) plus ongoing costs for power and MLOps staff. Per-token cost is $0, but fixed infrastructure cost is high |


Each interaction consumes different types of tokens at different price points:

::: details Prompt Tokens
Your input to the AI, including questions, conversation history, system prompts, and retrieved documents. Longer prompts cost more.
:::

::: details Completion Tokens
The AI-generated responses. Longer, more detailed responses cost more.
:::

::: details Embedding Tokens
Document processing for search and retrieval. Typically cheaper than text generation.
:::

::: details Model Tiers

| Tier          | Examples    | Use Case                                  | Cost     |
|---------------|-------------|-------------------------------------------|----------|
| **Flagship**  | GPT-5       | Complex reasoning, high-accuracy tasks    | Highest  |
| **Balanced**  | GPT-5 mini  | Standard workflows, internal assistants   | Medium   |
| **Efficient** | GPT-5 nano  | High-volume simple tasks, classification  | Lowest   |

:::

## Cost Tracking and Visibility

The AI-Hub tracks costs for each conversation with your AI agents. When you chat with an agent, the platform records how many tokens were used and calculates the associated cost. This information appears directly in the conversation thread.

Cost tracking works for all types of AI models, whether you're using cloud services like OpenAI or models hosted on your own infrastructure. For self-hosted models, you can assign a cost value to track spending consistently across all your AI services.

You can view cost information per conversation to understand which types of questions are most expensive. This helps you make informed decisions about agent design, model selection, and budget allocation.


## Budgets and Rate Limits

::: warning Not Currently Configured
Budget and rate limiting capabilities exist in the platform but are **not enabled by default**. This feature is not yet tested.
:::

The platform can enforce spending limits and usage restrictions through configuration. When enabled, administrators can set:

- **Budget caps**: Block requests when users exceed spending limits
- **Usage alerts**: Notify when approaching budget thresholds
- **Rate limits**: Control how many requests or tokens users can consume per minute
- **Concurrent request limits**: Restrict simultaneous AI operations

These controls require environment configuration and are typically set up during initial deployment based on your organization's needs. O

## Cost Optimization Strategies

### Model Selection

Match the model tier to your task requirements. Use flagship models (GPT-5) for complex, customer-facing, or high-accuracy tasks. Use balanced models (GPT-5 mini, GPT-4o) for internal assistants or standard workflows. Use efficient models (GPT-5 nano) for classification, data extraction, or high-frequency chat.

### Locally Hosted Models

Local hosting shifts spending from variable per-token fees to fixed infrastructure costs. The primary drivers are **data privacy** (HIPAA, GDPR), **compliance**, and **IP protection**—not immediate cost savings. This requires significant capital investment (GPUs, servers) and ongoing operational costs (power, MLOps staff).
