---
title: Cost control
---

# Cost control

AI agents cost money to operate. The Swiss AI Hub tracks these costs so you can optimize spending, justify investments,
and forecast budgets.

## How AI costs work

AI providers charge based on token usage. Tokens are small chunks of text (roughly 4 characters) that models process.

Cost model comparison:

| Model               | Type               | Cost Structure                                                                                                                                          |
| ------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| API (Pay-per-token) | Variable OPEX      | Pay providers (OpenAI, Google) for each token processed                                                                                                 |
| Locally Hosted      | CAPEX + Fixed OPEX | Capital expense for hardware (GPUs, servers) plus ongoing costs for power and MLOps staff. Per-token cost is \$0, but fixed infrastructure cost is high |

Each interaction consumes different types of tokens at different price points:

::: details Prompt tokens
Your input to the AI, including questions, conversation history, system prompts, and retrieved documents. Longer prompts
cost more.
:::

::: details Completion tokens
The AI-generated responses. Longer, more detailed responses cost more.
:::

::: details Embedding tokens
Document processing for search and retrieval. Typically cheaper than text generation.
:::

::: details Model tiers
| Tier      | Examples   | Use Case                                 | Cost    |
| --------- | ---------- | ---------------------------------------- | ------- |
| Flagship  | GPT-5      | Complex reasoning, high-accuracy tasks   | Highest |
| Balanced  | GPT-5 mini | Standard workflows, internal assistants  | Medium  |
| Efficient | GPT-5 nano | High-volume simple tasks, classification | Lowest  |
:::

## Cost tracking

The Swiss AI Hub tracks costs for each conversation. When you chat with an agent, the platform records token usage and
calculates the cost. This information appears in the conversation thread.

Tracking works for all AI models, whether you use cloud services like OpenAI or self-hosted models. For self-hosted
models, you can assign a cost value to track spending consistently.

You can view cost information per conversation to see which questions are most expensive. This helps with agent design
decisions, model selection, and budget planning.

## Budgets and rate limits

LiteLLM provides per-user budget and rate limiting capabilities through its user management system. These controls are
configured through environment variables and enforced automatically by the proxy.

Available controls:

- Max budget: Hard limit on spending per user within a budget period. Blocks requests when exceeded.

- Soft budget: Alert threshold that triggers notifications without blocking requests.

- Budget duration: Time period for budget reset (e.g., "30d" for monthly budgets). Without this, budgets never reset.

- TPM limit: Maximum tokens per minute a user can consume.

- RPM limit: Maximum requests per minute a user can make.

- Max parallel requests: Maximum concurrent requests a user can have in flight.

::: details Configuration via environment variables
```bash
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # $100 hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at $80
LITE_LLM_PROXY_USER_BUDGET_DURATION="30d"      # Reset monthly
LITE_LLM_PROXY_USER_TPM_LIMIT=10000            # 10k tokens/minute
LITE_LLM_PROXY_USER_RPM_LIMIT=60               # 60 requests/minute
LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS=5    # 5 concurrent requests
```

These settings apply to new users created in the system. Existing users retain their configured limits.
:::

::: warning Not currently enabled
While the infrastructure supports these limits, they are not enabled by default. Set the environment variables above to
activate budget and rate limiting.
:::

## Optimization strategies

### Model selection

Match the model tier to your task. Use flagship models (GPT-5) for complex, customer-facing, or high-accuracy tasks. Use
balanced models (GPT-5 mini) for internal assistants or standard workflows. Use efficient models (GPT-5 nano) for
classification, data extraction, or high-frequency chat.

### Locally hosted models

Local hosting shifts spending from variable per-token fees to fixed infrastructure costs. Organizations choose this for
data privacy (HIPAA, GDPR), compliance, and IP protection, not for immediate cost savings. It requires capital
investment (GPUs, servers) and ongoing operational costs (power, MLOps staff).
