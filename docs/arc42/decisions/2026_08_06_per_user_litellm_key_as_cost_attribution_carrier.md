# The Per-User LiteLLM Key Carries User Attribution; Tenant Attribution Lives on the Cost Event

## Context

LLM cost was tracked per model but not per user. Every call originating from the agent runtime, from direct controller
features (translation, knowledge-namespace naming), and from retrieval embeddings authenticated with the shared master
key, so LiteLLM recorded all of it against the service account. Per-user LiteLLM users and deterministic keys already
existed and were already used by the OpenWebUI-facing chat, model-listing, and bot completion paths — the agent runtime
simply never adopted them.

Without per-user attribution, per-user spend is unmeasurable and per-user limits are unenforceable. Issue #1451 exists
to close that gap and unblock its sibling, per-user overall spend limits (#1452).

Two dimensions were in scope: the invoking **user** and the acting **tenant**.

## Decision Drivers

- **Every user-facing call must be attributable** — no anonymous spend against the service account.
- **Must make per-user limits enforceable**, since #1452 depends on it.
- **Must cover all model types** — chat, embedding, and reranking all cost money.
- **No Enterprise dependencies** — we run the free tier (see the pipeline redaction ADR).
- **Tenant attribution must survive** even where the gateway cannot express it.

## Decision

**User attribution rides on the per-user API key.** Every LLM call resolves the invoking user's LiteLLM key instead of
the master key. This populates the `user` column on every spend-log row and simultaneously activates that user's
`USER_MAX_BUDGET`, which is what makes #1452 enforceable rather than merely observable. The key is the only carrier that
reaches all three model types: chat and embedding clients accept it, and so does the reranker, which exposes no header
injection point at all.

Resolution happens in the async context manager that already wraps every agent LLM call, because the key lookup is
asynchronous while model construction is not. The identity itself reaches steps through dependency injection, read from
the per-run context where the dispatcher already stores the start event's fields.

**Tenant attribution does not go to LiteLLM.** Custom request tags — both the `x-litellm-tags` header and
`metadata.tags` in the body — are an Enterprise feature. On our free-tier deployment the proxy accepts either form,
returns HTTP 200, and silently discards the tag; verified by sending both and reading the spend log back. Tenant is
therefore recorded on the platform's own `LLMCostEvent`, which persists to the event store alongside the user, and is
emitted as Langfuse trace metadata. Per-tenant spend is queryable from the platform, not from the gateway.

Background pipelines are out of scope: they have no identity concept to attribute and emit no cost events at all.

Scheduled agent runs are a second unattributed path, and a noisier one: they execute real agent steps, so they do emit
cost events, but as system runs they carry no user and their events land with both `user_id` and `tenant_id` null. A
tenant is in fact knowable there — the agent's own profile has one — but reading it would mean sourcing tenant from
somewhere other than the invoking identity. Declaring a tenant for background and scheduled work belongs to #786.

## Consequences

### Positive

- Every user-facing LLM call is attributable to a user at the gateway, and to both user and tenant in the platform.
- Per-user budgets become enforceable without further work, unblocking #1452.
- Reranking and embedding spend are attributed too, not just chat.
- Per-tenant reporting survives the Enterprise gate by living in the event store.
- No Enterprise license required.

### Trade-offs

- **Budgets activate on a previously unlimited path.** Agent traffic now authenticates as the user, so a deployment with
  `USER_MAX_BUDGET` set will start rejecting agent calls that previously bypassed the limit. This is the intended
  behaviour but it is a behavioural change on upgrade, not only an observability one.
- **User provisioning enters the LLM hot path.** Resolving a key can create the LiteLLM user and generate its key on a
  cache miss. The cache is per-process with a six-hour TTL, so each agent container pays that cost once per user.
- **Two sources of truth for cost.** The platform computes cost locally from the model-info rates while LiteLLM computes
  its own. They will not agree exactly — measured at ~0.2% apart on a validation run. Enforcement must read LiteLLM's
  figure; platform reporting shows the local one.
- **Embedding and reranking spend is attributed at the gateway but absent from platform cost events.** Only calls made
  through the cost-reporting context manager emit an `LLMCostEvent`. The retriever and the reranker build their models
  directly and discard the returned cost tracker, so they carry the user's key — LiteLLM bills the right user — but
  produce no event. The two totals therefore diverge further on retrieval-heavy workloads, and per-model spend in the
  platform reflects chat only.
- **Per-tenant totals cannot reconcile against the platform total.** Sysadmins act outside any tenant, so their spend
  has a user but no tenant.
- **Tenant attribution is not visible in the gateway.** Anyone debugging spend in the LiteLLM UI sees users but never
  tenants, and must know to query the event store instead.

## Related Decisions

- `2026_04_28_litellm_pipeline_message_redaction.md` — also constrained by the free tier, and establishes the
  per-request header mechanism that pipeline calls use. Attribution headers merge with those redaction headers rather
  than replacing them.
- Issue #786 (tenant-specific LLM usage tracking) owns any future gateway-side tenant carrier. LiteLLM teams are the
  candidate: `team_id` is a native, non-Enterprise spend-log column, but adopting it means provisioning a team per
  tenant and joining each user key to it.
