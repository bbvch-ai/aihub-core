# Langfuse LLM Connections Use Public URLs

## Context

Langfuse's managed evaluators (Correctness, Hallucination, Conciseness, …) run as LLM-as-a-judge calls. Langfuse issues
those calls **from its own container**, using the `baseURL` stored on the LLM connection we register at API startup in
`LangfuseProvisioner._register_litellm_connection`.

Langfuse 3.2x resolves that `baseURL` and refuses any address landing on a private IP:

```
PUT /api/public/llm-connections
400 {"message":"Invalid baseURL: Blocked IP address detected","error":"InvalidRequestError"}
```

We registered the connection with `LITE_LLM_PROXY_BASE_URL` — an in-cluster address (`http://litellm:4000` in compose, a
`svc.cluster.local` name in Kubernetes). Every such registration is now rejected, so the evaluator connection is absent
and no judge can run.

The constraint arrived without any change on our side: both repos pin the floating tag `langfuse/langfuse:3`, and the
check does not exist in older images (verified: 3.147.0 accepts private addresses, 3.225.4 rejects them). Langfuse's
documented escape hatch does not apply — `LANGFUSE_UNSAFE_TRUSTED_PRIVATE_IPS` is implemented for webhooks only
([langfuse/langfuse#13097](https://github.com/langfuse/langfuse/issues/13097), closed as *not planned*).

`LITE_LLM_PROXY_BASE_URL` cannot simply be repointed: it is also what the API uses for **all** real LLM traffic, so a
public value would send every production completion out to the internet and back.

## Decision Drivers

- *Judge calls must originate from Langfuse's container* and therefore need an internet-reachable address.
- *Production completions must keep using the in-cluster route.* No change to `httpx_client`, `httpx_aclient` or
  `openai_aclient`.
- *Judge prompts must reach the model unmodified.* LLM-as-a-judge uses strict rubrics and structured output.
- *No new ingress.* LiteLLM is already published at `https://litellm.${DOMAIN}` by the existing Traefik router.

## Decision

Both LLM connections Langfuse dials must carry an internet-reachable address, for the same reason: Langfuse resolves
every connection's `baseURL` from its own container and refuses private ones.

**Agents connection** (`ai-hub-agents`, the agent under test) — `AIHUB_OPENAI_API_BASE_URL` becomes
`https://${DOMAIN}/api/v1/active/openai` on every deployed stage, replacing the in-cluster `http://api:8000/...`. That
setting is documented as single-purpose and is read only when registering this connection; internal server-to-server
traffic uses `AIHUB_INTERNAL_API_BASE_URL`, so nothing else moves.

**Evaluators connection** (`ai-hub-litellm`, the judge) — register it against **LiteLLM's public URL**, via a dedicated
setting `LiteLLMProxySettings.PUBLIC_URL` (`LITE_LLM_PROXY_PUBLIC_URL`) that **no other code path reads**. It is
injected only into the `api` service, which is the only process that provisions Langfuse. Judge calls therefore continue
to hit LiteLLM directly, exactly as before, authenticated by the LiteLLM master key.

**Rejected: routing judge traffic through AI Hub's own OpenAI-compatible endpoint** (`AIHubSettings.OPENAI_API_BASE_URL`
with the superuser token). It would work at the network level, but `OpenaiService._apply_model_identity` prepends a
platform-authored *"you are model X"* system message to **every** plain-model request, merging it into the caller's own
system message when one is present. Per ADR
[2026_08_14_model_identity_system_prompt_for_plain_llm_chats](2026_08_14_model_identity_system_prompt_for_plain_llm_chats.md)
that injection is deliberately unconditional and has no opt-out; the ADR pre-rejects payload-shape gating and names
non-reproducible evals as an accepted cost. It would also rewrite the judge's rubric in German (the locale on that path
resolves to `de`), move all judge cost onto the superuser identity, and bypass usage limits.

## Consequences

- Judge traffic leaves the cluster and re-enters through Traefik. It is TLS-terminated and master-key-authenticated, but
  the LiteLLM master key is now used by a caller outside the cluster.
- **Managed evaluators cannot work on `dev`, `local` or `build`** — Langfuse rejects every private address and those
  stages have no public domain. `LITE_LLM_PROXY_PUBLIC_URL` is left unset there and provisioning now fails loudly at
  ERROR, naming the variable, instead of logging an INFO line that read like success.
- OCR/VLM models (`MinerU*`, `olmOCR*`, `LightOnOCR*`) are filtered out of the judge list. LiteLLM reports them as
  `mode: chat`, but they cannot grade text.
- Pinning the Langfuse image to an exact tag instead of the floating `:3` is a worthwhile follow-up — this class of
  breakage arrives silently on image drift.
- Agent experiments do not work in local development either: the `api` service does not exist in the dev compose file
  (the API runs on the host), so `api` is `NXDOMAIN` inside the Langfuse container. Point `AIHUB_OPENAI_API_BASE_URL` at
  `http://host.docker.internal:8000/api/v1/active/openai` to exercise them locally.
- On `local` and `build` the public URL is served with a self-signed certificate, so Langfuse may reject the TLS
  handshake when calling either connection. Those stages are for wiring checks, not for running experiments.
- A **project-level default evaluation model** is still required for managed evaluators to become selectable, and
  Langfuse exposes no public API for it (only `/api/public/llm-connections`, `/api/public/models`,
  `/api/public/models/{id}` exist). It is set once per deployment by a sysadmin in Langfuse's own UI and is documented
  as a setup step rather than provisioned by us.
