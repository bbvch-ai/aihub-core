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

## Usage per tenant

Every model call the Swiss AI Hub makes for a user is booked to the tenant the user is acting in. This covers chat
through OpenWebUI, the OpenAI-compatible API, agent runs (chat, embeddings and reranking), translation and
speech-to-text. The LiteLLM proxy records the tenant as its *customer*, named after the tenant. A user who belongs to
two tenants has each call counted only in the tenant they were acting in.

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
LITE_LLM_PROXY_USER_MAX_BUDGET=100.0           # $100 hard limit
LITE_LLM_PROXY_USER_SOFT_BUDGET=80.0           # Alert at $80
LITE_LLM_PROXY_USER_BUDGET_DURATION="30d"      # Reset monthly
LITE_LLM_PROXY_USER_TPM_LIMIT=10000            # 10k tokens/minute
LITE_LLM_PROXY_USER_RPM_LIMIT=60               # 60 requests/minute
LITE_LLM_PROXY_USER_MAX_PARALLEL_REQUESTS=5    # 5 concurrent requests
```

A changed max budget, budget duration, TPM limit or RPM limit also reaches users who already exist, on the first
reconciliation after the API restarts (see below). A changed budget duration starts the user's budget period anew. The
soft budget and the parallel-request limit apply only to users created after they are set, because LiteLLM cannot change
them on an existing user.
:::

::: warning Not currently enabled
While the infrastructure supports these limits, they are not enabled by default. Set the environment variables above to
activate budget and rate limiting.
:::

### LiteLLM users follow Keycloak

The Hub creates a LiteLLM user and key for every Hub user on their first request. Users are disabled and removed in
Keycloak, and nothing notifies the Hub, so the API compares LiteLLM's users with Keycloak's every five minutes
(`LITE_LLM_PROXY_USER_RECONCILE_INTERVAL_SECONDS`), once across all API replicas:

- **Limits.** A user whose limits differ from the settings above gets the new ones. Only changed fields are sent, so the
  budget period is not restarted on every run.
- **Disabled users.** LiteLLM cannot block a user, so every key of a user disabled in Keycloak is blocked. When the user
  is enabled again, the keys the Hub blocked are unblocked. A key an operator blocked by hand stays blocked.
- **Removed users.** A user Keycloak no longer has is deleted from LiteLLM together with their keys. Their spend stays
  in LiteLLM's spend logs and usage views. Before deleting, the Hub asks Keycloak for that user again, so an outage or
  an incomplete listing deletes no one.
- **Users the Hub did not create.** LiteLLM users with a role other than `internal_user_viewer`, such as users made by
  hand in the LiteLLM UI, are never changed. If Keycloak has no such user, they are listed in the API log as a warning,
  so an operator can remove them.
- **Keys without a LiteLLM user.** Older versions of the Hub could leave a key whose LiteLLM user was never created.
  Such a key has no limits and is never blocked. It is listed in the API log as a warning, with the user's state in
  Keycloak, so an operator can delete it.

Each run logs a summary line, `LiteLLM user reconciliation: …`, with the users it deleted and blocked. A user disabled
or removed in Keycloak keeps a working key until the next run. LiteLLM's built-in admin, `default_user_id`, is ignored.
`LITE_LLM_PROXY_USER_RECONCILE_EXEMPT_USER_IDS` lists further user ids to leave alone; development uses it for the test
identity.

## Optimization strategies

### Model selection

Match the model tier to your task. Use flagship models (GPT-5) for complex, customer-facing, or high-accuracy tasks. Use
balanced models (GPT-5 mini) for internal assistants or standard workflows. Use efficient models (GPT-5 nano) for
classification, data extraction, or high-frequency chat.

### Locally hosted models

Local hosting shifts spending from variable per-token fees to fixed infrastructure costs. Organizations choose this for
data privacy (HIPAA, GDPR), compliance, and IP protection, not for immediate cost savings. It requires capital
investment (GPUs, servers) and ongoing operational costs (power, MLOps staff).
