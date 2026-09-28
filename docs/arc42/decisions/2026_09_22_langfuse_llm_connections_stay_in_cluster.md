# Langfuse LLM Connections Stay In-Cluster and Are Allowlisted

## Context

Langfuse's managed evaluators run as LLM-as-a-judge calls, and dataset experiments call the agent under test.
Langfuse issues both **from its own containers**, using the `baseURL` stored on the two LLM connections we
register at API startup in `LangfuseProvisioner`: `ai-hub-litellm` (the judge) and `ai-hub-agents` (the agent).

Since Langfuse 3.167.1 those URLs are validated and any address resolving to a private IP is refused:

```
PUT /api/public/llm-connections
400 {"message":"Invalid baseURL: Blocked IP address detected","error":"InvalidRequestError"}
```

Both connections carried in-cluster addresses, so both registrations are rejected wherever that check runs.

**The check only manifests on Kubernetes today**, for two compounding reasons. First, compose pulls a
hand-mirrored `ghcr.io/bbvch-ai/aihub-core/langfuse/langfuse:3` frozen at 3.147.0, which predates the check,
while Kubernetes pulls upstream `docker.io/langfuse/langfuse:3` (3.225.x). Second, the write-time check only
fires when the submitted URL differs from the stored one, so rows written under 3.147.0 are grandfathered.
Kubernetes namespaces started with an empty `llm_api_keys`, so their first insert is the one validated — and
it fails permanently.

The constraint therefore arrived without any change on our side, and it is latent on every deployment.

## Decision Drivers

- **Reachability, not just validity.** Judge calls and experiments run in `langfuse-worker`, which sits only
  on `backend`, `data` and `storage` — all `internal: true`. It has no egress. A URL that passes validation
  but cannot be reached from there is not a fix.
- **Production completions must keep their in-cluster route.** `LITE_LLM_PROXY_BASE_URL` carries all real LLM
  traffic; it cannot be repointed.
- **One behaviour on every deployment**, whichever Langfuse version it runs, fresh install or upgrade.
- **No new ingress and no new public exposure** of LiteLLM or the superuser token.

## Decision

Keep both connections on the in-cluster URLs the platform already uses, and allowlist their hostnames on the
Langfuse side.

**Allowlist.** `LANGFUSE_LLM_CONNECTION_WHITELISTED_HOST` is set on **both** `langfuse-web` and
`langfuse-worker`. Upstream added this variable in the same change that added the check
([langfuse#13073](https://github.com/langfuse/langfuse/pull/13073)); it is matched as an exact lowercase
hostname and short-circuits before any DNS or IP resolution. Both services need it because `-web` validates
the write and `-worker` revalidates on every call it makes through the connection
(`packages/shared/src/server/llm/secureLlmFetch.ts`). Any deployment of this platform must set it to the
hostnames of the two registered connections; Kubernetes uses its own `*.svc.cluster.local` names, so the
compose values do not carry over.

**Evaluators connection.** A dedicated `LiteLLMProxySettings.INTERNAL_BASE_URL`
(`LITE_LLM_PROXY_INTERNAL_BASE_URL`) that no other code path reads, falling back to `BASE_URL`. The fallback
is correct wherever the API and Langfuse share a network — every containerised deployment — so only local
development, where the API runs on the host and `BASE_URL` is `http://localhost:4000`, has to set it.

**Agents connection.** Unchanged from before the incident: `AIHUB_OPENAI_API_BASE_URL` stays
`http://api:8000/api/v1/active/openai`. `api` and `langfuse-worker` share the `backend` network. Local
development sets it to `http://host.docker.internal:8000/...` because dev renders no `api` container.

**A loopback guard** rejects either URL at startup when it resolves to the loopback interface, and a Langfuse
400 naming a blocked address is re-raised naming the offending hostname and the allowlist variable. The first
turns the one case where the fallback is wrong into a loud failure instead of a plausible bad row; the second
puts the remedy in the operator's own logs, which matters because the Kubernetes chart lives in another repo.

### Rejected: register both connections against public URLs

`https://litellm.${DOMAIN}` and `https://${DOMAIN}/api/v1/active/openai` pass validation, but
`langfuse-worker` has no egress, so every judge call and every experiment would fail at request time on a
stack whose provisioning logs read as success. It would also route production judge traffic out through
Traefik and back, and expose the LiteLLM master key to a caller outside the cluster.

### Rejected: route judge traffic through AI Hub's own OpenAI-compatible endpoint

Network-wise this works, but `OpenaiService._apply_model_identity` prepends a platform-authored *"you are
model X"* system message to **every** plain-model request, merging it into the caller's own system message
when one is present. Per ADR
[2026_08_14_model_identity_system_prompt_for_plain_llm_chats](2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md)
that injection is deliberately unconditional and has no opt-out; the ADR pre-rejects payload-shape gating and
names non-reproducible evals as an accepted cost. It would rewrite the judge's rubric, in German (the locale
on that path resolves to `de`), move all judge cost onto the superuser identity, and bypass usage limits.

### Rejected: pin Kubernetes back to a pre-check Langfuse

The 400 would disappear, but 3.147.0 is 51 Postgres and 6 ClickHouse migrations behind the version those
instances already ran, and Langfuse migrations are forward-only. It would also revert a security fix on the
one deployment that is actually exposed, and would not make the evaluators selectable anyway.

## Consequences

- No judge or experiment traffic leaves the cluster, and `langfuse-worker` keeps its no-egress posture. A
  comment at its `networks:` block records that the decision depends on it.
- Allowlisting disables SSRF protection for those hostnames for *any* LLM connection a Langfuse user creates,
  not only ours. Langfuse is sysadmin-gated (ADR
  [2026_06_11_langfuse_access_restricted_to_sysadmins](2026_06_11_langfuse_access_restricted_to_sysadmins.md)),
  so the exposure is bounded, and `host.docker.internal` is allowlisted on `dev` only.
- Upgrading compose to 3.2x becomes safe in both directions: an existing stack is grandfathered at write time
  and covered by the allowlist at call time; a fresh install is covered by the allowlist at both.
- Managed evaluators now work in local development, which they never did — the previous value was reachable
  from the host but not from the Langfuse container.
- The loopback guard makes a Langfuse running in host-network mode unsupported. That is not a topology this
  platform deploys.
- OCR/VLM models (`MinerU*`, `olmOCR*`, `LightOnOCR*`) are filtered out of the judge list. LiteLLM reports
  them as `mode: chat`, but they cannot grade text.
- **A project-level default evaluation model is still required** for managed evaluators to become selectable,
  and Langfuse exposes no public API for it (only `/api/public/llm-connections`, `/api/public/models` and
  `/api/public/models/{id}` exist). It is set once per deployment by a sysadmin in Langfuse's own UI and is
  documented as a setup step rather than provisioned by us.
- Pinning the Langfuse image to an exact tag instead of the floating `:3` is a worthwhile follow-up. The
  mirror refresh must land after this change, since a fresh install on 3.2x is exactly the failure case above.
