# Pipeline-Originated LiteLLM Calls Are Message-Redacted at the Proxy

## Context

A production deployment's LiteLLM database grew past 130 GB during the testing phase, with very few users. The dominant
contributor is the ingestion pipeline: every document chunk crosses the LiteLLM proxy at least once for embedding, and
embedding responses are large vectors. Stored prompts and responses for chat traffic are valuable for debugging — those
should remain visible. Pipeline traffic content is not: embedding inputs are reproducible from source documents,
embedding outputs are vectors, and pipeline runs aren't linked back to user-visible run IDs.

## Decision Drivers

- **Selective**: redact pipeline traffic; keep agent and end-user traffic intact.
- **Spend tracking must survive**: we want to know that the call happened, the cost, and the token count — only the
  message content is uninteresting.
- **No Enterprise dependencies**: per-key/per-team logging is Enterprise-only; we run the free tier.
- **Survives growth**: a new pipeline LLM caller should be redacted by default, without each author remembering.

## Decision

LiteLLM exposes a per-request HTTP header that drops message content from the spend log row while keeping spend
metadata. We inject this header on every LiteLLM call originating from the pipeline scope and pin the proxy to a version
that honors it.

Agent, end-user, and bot traffic continue to be logged in full. The redaction is scoped strictly to pipeline traffic
through a shared constant that pipeline-side resources opt into; non-pipeline scopes do not see or use it. The proxy
upgrade was necessary because earlier versions silently accept the header without acting on it.

## Consequences

### Positive

- Pipeline calls stop bloating the spend log; spend, tokens, model name, and request ID are preserved.
- Agent and end-user traffic is untouched — debugging visibility is retained where it matters.
- New pipeline LLM callers inherit redaction with no per-author effort.
- No Enterprise license required.

### Trade-offs

- The header is documented as **beta** by LiteLLM. The contract could change between proxy versions; smoke-test on each
  upgrade.
- The 130 GB of historical content is not retroactively redacted. A one-time database cleanup is required to reclaim
  disk; that is operational, not part of this decision.
- Redaction depends on both the per-request header and the proxy version. Downgrading the proxy silently re-enables
  logging without an obvious failure mode.

## Related Decisions

None. This is the first ADR touching LiteLLM proxy logging behavior.
