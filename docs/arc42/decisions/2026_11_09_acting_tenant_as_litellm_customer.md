# The Acting Tenant Is the LiteLLM Customer of Every Call

## Context

Operators must tell a customer how many tokens and how much LLM cost their tenant used in a month, in total and per
model. A dedicated instance serves one customer, and LiteLLM's Global Usage view already answers that for it. A tenant on
the shared instance has no such view. The gateway attributed calls to users only (ADR
`2026_08_06_per_user_litellm_key_as_cost_attribution_carrier`), and one user key serves a user in every tenant they
belong to, so the key cannot carry the tenant. The platform's own per-tenant figures come from `LLMCostEvent`, which only
agent runs emit, so plain chat, embeddings, translation, speech-to-text and pipelines are missing from them.

LiteLLM v1.106.4, which every deployment runs, ships Customer Usage and Tag Usage views to proxy administrators without
an Enterprise licence, with spend, tokens and a per-model breakdown. Both read daily aggregate tables that LiteLLM fills
on every call: one per customer (end user), one per request tag.

## Decision Drivers

- **Every call made for a user in a tenant is attributed**, whichever path made it.
- **A user in two tenants is counted in each separately.**
- **Calls without a tenant are a line of their own**, so the tenants' totals and that line add up to the instance total.
- **Readable by an operator** in a UI that already exists, without an Enterprise licence.
- **Per-user keys and budgets stay as they are**, since per-user limits depend on them.

## Decision

**The acting tenant is the LiteLLM customer.** Every call the Hub makes for a user sends the header
`x-litellm-customer-id: <tenant id>` (`LiteLLMCustomerService.header_for`). The per-user OpenAI client carries it, which
covers the OpenAI-compatible API and so OpenWebUI's chats, speech-to-text, text-to-speech and RAG embeddings, and the
bots. Agent calls get it from `LLMConfig.cost_reporting_llm`, and the embedding, reranking and translation call sites
pass it to `to_llama_index`. Cohere's client takes no headers, so the reranker sets them on the client wrapper both API
versions share.

Before the first call for a tenant in a process, the Hub makes sure LiteLLM has a customer with the tenant's name as its
alias (`/customer/new`, or `/customer/update` after a rename), cached like the user key. LiteLLM would otherwise create
the customer on its first spend without a name, and its view would list tenants by id.

**The customer header wins over the `user` field.** LiteLLM resolves the customer from its standard headers before the
request body's `user`, which the OpenAI-compatible API sets to the user's id. That is also why a call for a user acting
outside any tenant names the customer `no-tenant` instead of leaving the header out: LiteLLM would otherwise make the
user a customer of their own.

**Calls without a customer are booked to `no-tenant` in the gateway.** A LiteLLM pre-call hook (`tenant_attribution.py`,
mounted next to `custom_callbacks.py`) stamps `no-tenant` on every call that resolved no customer. That catches the
callers that act for no user and do not run through the Hub's per-user code: pipelines, scheduled runs, the memory
writer, and MinerU, which calls LiteLLM from its own container with the master key. LiteLLM writes a customer's daily
spend only when a call names one, so without the hook those calls would be in the instance total and on no customer
line.

Customers were preferred over request tags. A tag is free text any caller can add next to others, and the Tag Usage view
counts a call once per tag. A call has exactly one customer, so customers partition the instance total, which is what
makes the per-tenant figures add up. The same customer is the direction for tenant budgets and the tenant filter of the
Grafana dashboards.

Verified on LiteLLM v1.106.4 with a fake upstream, by driving the Hub's call paths for one user in two tenants, a
sysadmin, a pipeline, a run without a user and a raw master-key call. Each tenant's line held exactly its own calls,
per model. `no-tenant` held the four calls without a tenant. The customers' requests, tokens and spend summed exactly to
Global Usage.

## Consequences

### Positive

- An operator reads a tenant's tokens and cost for any period, per model, in LiteLLM's Customer Usage view, and the
  instance total in Global Usage. The runbook is in the platform docs under Cost control.
- Every path is covered, including the ones `LLMCostEvent` never saw: plain chat, embeddings, reranking, translation,
  speech-to-text, pipelines and document parsing.
- Per-user keys, the `user` column and per-user budgets are unchanged.

### Trade-offs

- **Calls made before this change are not attributed.** OpenAI-compatible calls from before it appear under customers
  named after a user id, and calls without a user under none.
- **The hook is part of the gateway configuration.** A deployment that keeps its own LiteLLM configuration, such as the
  Kubernetes chart, must mount `tenant_attribution.py` and list it under `callbacks`, or calls without a tenant are
  missing from Customer Usage while still counted in Global Usage.
- **Customer provisioning joins the first call per tenant and process**: one lookup, and one write when the customer is
  new or was renamed.
- **The customer is a gateway object with budget fields of its own.** Nothing sets them today; tenant budgets would.
- **Scheduled runs, pipelines and the memory writer count as no tenant** even where a tenant is knowable from the
  agent's profile or the knowledge database. Giving them one belongs to the work on background tenants.

## Related Decisions

- `2026_08_06_per_user_litellm_key_as_cost_attribution_carrier.md` — user attribution on the key. This decision adds the
  gateway-side tenant carrier that ADR left open, and supersedes its "tenant attribution does not go to LiteLLM".
