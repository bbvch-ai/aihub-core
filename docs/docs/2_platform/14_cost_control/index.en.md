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
| Locally Hosted      | CAPEX + Fixed OPEX | Capital expense for hardware (GPUs, servers) plus ongoing costs for power and MLOps staff. Per-token cost is 0, but fixed infrastructure cost is high |

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

## How cost is computed

Every figure the platform reports is a token count, or a duration, multiplied by a price written into the LiteLLM
configuration. No price is looked up anywhere else: a model without a configured price costs 0.

### Currency

All prices and costs are in **CHF**, the currency the providers invoice in. This includes the cost per conversation, the
Admin UI, the Hub API, LiteLLM's usage views, Langfuse and user budgets.

::: warning The dollar sign in LiteLLM and Langfuse
LiteLLM and Langfuse have no currency setting and always print "\$". The amounts they show are CHF.
:::

### Where prices come from

Prices are set per model in the LiteLLM configuration, as a price per token (`input_cost_per_token`,
`output_cost_per_token`) or per second of audio (`input_cost_per_second`). Each price is copied from the provider's CHF
price list or, where a provider publishes none, measured from its usage report.

The Docker Compose deployments take their prices from `infra/deployment/compose-config.yml`; the files in
`infra/configs/litellm/` are generated from it. Kubernetes deployments keep their own prices in the LiteLLM
configuration of their chart, following the same rules.

### How each call is priced

LiteLLM books the cost of every call in its spend log, from the usage the provider returns:

| Call                    | Cost booked                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------- |
| Chat                    | prompt tokens × input price + completion tokens × output price                          |
| Chat with reasoning     | reasoning tokens are part of the completion tokens and cost the output price            |
| Chat with cached input  | cached prompt tokens cost the full input price; no discounted cache price is configured |
| Streamed chat           | the same as without streaming; LiteLLM always asks the provider for the usage           |
| Embedding               | input tokens × input price                                                              |
| Rerank                  | input tokens × input price; the usage views show the cost but 0 tokens                  |
| Transcription           | seconds of audio, as reported by the provider, × price per second; 0 tokens             |
| Fallback                | the price of the model that answered, booked under that model's name                    |
| Cache hit               | 0, since the provider is not called; the tokens are counted again                       |
| Model without a price   | 0; the tokens are still recorded                                                        |
| Provider sends no usage | 0 tokens and 0 cost when not streamed; LiteLLM counts the tokens itself when streamed   |

The configurations cache embeddings for one day, so repeated embeddings of the same text are free but appear again in
the token totals. A call to a model that fails falls back to `text-generation/gemma-4-31B-it` and is booked at its
price.

### Three figures for the same calls

| Figure            | Where it is shown                        | Tokens counted from                                                                                                |
| ----------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| LiteLLM spend log | LiteLLM's Usage and Customer Usage views | the usage the provider returns                                                                                     |
| Hub cost events   | cost per conversation, Admin UI          | the usage the provider returns, or a local tokenizer when there is none; always the local tokenizer for embeddings |
| Langfuse          | traces                                   | the usage in the trace, priced from model definitions created from LiteLLM's prices                                |

The LiteLLM spend log is the one to compare with invoices: it covers every call through the proxy. Hub cost events cover
agent runs only. Langfuse stores each generation's cost when it records it: when the Hub API starts and finds a price
changed in LiteLLM, it replaces that model's definition in Langfuse, and generations recorded before keep the cost they
were given. Models priced per second of audio, such as transcription, are not priced in Langfuse.

### Prices of the Docker Compose deployments

Checked against the providers' price lists on 2026-11-17. Prices per million tokens unless noted.

| Model                                           | Provider   | Input              | Output | Source and check                                                    |
| ----------------------------------------------- | ---------- | ------------------ | ------ | ------------------------------------------------------------------- |
| `text-generation/gemma-4-31B-it`                | Infomaniak | 0.20               | 0.40   | Infomaniak price page; matches                                      |
| `text-generation/gemma-4-31B-it` (stoney)       | stoney     | 0.25               | 1.00   | measured from stoney's usage report, which has no public price list |
| `text-generation/Ministral-3-14B-Instruct-2512` | Infomaniak | 0.30               | 0.40   | Infomaniak price page; matches                                      |
| `text-generation/Kimi-K2.6`                     | Infomaniak | 0.60               | 3.00   | Infomaniak price page; matches                                      |
| `text-generation/Apertus-70B-Instruct-2509`     | Infomaniak | 0.70               | 2.50   | the price page lists only Apertus-v1.5-70B, at this price           |
| `text-generation/Qwen3.5-122B-A10B-FP8`         | Infomaniak | 0.40               | 3.20   | no longer on the price page; unverified                             |
| `embedding/bge-m3`                              | Phoeniqs   | 0.4309             | -      | Phoeniqs publishes no price list; unverified                        |
| `reranker/bge`                                  | Phoeniqs   | 0.0077             | -      | Phoeniqs publishes no price list; unverified                        |
| `transcription/whisper-large-v3`                | Phoeniqs   | 0.00245 per minute | -      | Phoeniqs publishes no price list; unverified                        |
| `text-generation/MinerU2.5-2509-1.2B` (OCR)     | stoney     | unpriced           |        | stoney publishes no price; costs 0                                  |
| `image-generation/flux`                         | not set    | unpriced           |        | no provider is configured by default; costs 0                       |
| all models of the `*.gpu` variants              | own GPUs   | 0                  | 0      | priced 0 on purpose: the cost is the hardware, not the call         |

### Keeping prices up to date

When a provider changes a price, or a model is added:

1. Take the CHF price from the provider's price list, or measure it from its usage report.
2. Write it as a price per token (per million divided by 1,000,000) in `infra/deployment/compose-config.yml` and in the
   LiteLLM configuration of the Kubernetes chart, with a comment naming the source and the date.
3. Run `make generate-compose` and update the table above.

A provider that invoices in another currency needs its price converted to CHF when it is entered, with the rate and its
date in the comment.

## Usage per tenant

Every model call the Swiss AI Hub makes for a user is booked to the tenant the user is acting in. This covers chat
through OpenWebUI, the OpenAI-compatible API, agent runs (chat, embeddings and reranking), translation and
speech-to-text. The LiteLLM proxy records the tenant as its *customer*, named after the tenant. A user who belongs to two
tenants has each call counted only in the tenant they were acting in.

Calls made outside any tenant are booked to the customer `no-tenant`: sysadmins acting outside a tenant, scheduled agent
runs, data pipelines, the memory writer and document parsing. They appear as their own line, never inside a tenant.

Costs are computed from the prices configured for each model in LiteLLM.

### Reading last month's usage of a tenant

On a shared instance that serves several tenants:

1. Open the LiteLLM UI at `https://litellm.<your domain>/ui` and sign in as a proxy administrator.
2. Open **Usage** and switch the view from **Global Usage** to **Customer Usage**.
3. Set **Select Time Range** to the first and last day of the month.
4. In **Select customer to filter**, pick the tenant by its name.
5. Read the figures:
   - **Cost** tab: total spend, requests and tokens of the tenant, and spend per model.
   - **Model Activity** tab: requests, tokens and spend per model, with prompt (input) and completion (output) tokens
     shown separately in **Total Tokens Over Time**.
   - **Export Data** downloads the same figures as a file.

Without a customer filter, the **Cost** tab lists every tenant and `no-tenant` under **Spend Per Customer**. Their sum
equals the instance total shown under **Global Usage** for the same period.

::: details Reading the figures through the API
The UI reads them from LiteLLM's admin API, which you can query with the LiteLLM master key. The response lists each day
with its prompt tokens, completion tokens and spend, in total and per model:

```bash
curl -s "https://litellm.<your domain>/customer/daily/activity?end_user_ids=<tenant id>&start_date=2026-10-01&end_date=2026-10-31&page_size=1000" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

`/customer/list` lists the customers with their tenant names, and `/user/daily/activity` with the same dates returns the
instance total.
:::

### Reading last month's usage of a dedicated instance

On an instance that serves one customer, the whole instance is that customer's usage. Open **Usage** → **Global Usage**,
set the time range to the month, and read the totals and the **Model Activity** tab as above.

::: warning Calls made before tenants were recorded
Only calls made since the Swiss AI Hub started recording tenants are booked to one. Earlier calls through the
OpenAI-compatible API appear under customers named after a user id, and earlier calls without a user under no customer
at all. Deployments that maintain their own LiteLLM configuration must register the `tenant_attribution` callback
shipped next to `custom_callbacks.py`, or calls without a tenant are missing from the customer view.
:::

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
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # 100 CHF hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at 80 CHF
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
