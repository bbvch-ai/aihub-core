# Presidio With GLiNER and a Streaming Guardrail Anonymise Calls to External Models

## Context

Calls to language models hosted outside a deployment should not carry personal data. The gateway had two built-in
LiteLLM Presidio guardrails, off by default and requested by no caller, against a stock Presidio analyzer that ships
only an English model (German requests failed with HTTP 500). Turning them on would not have been enough:

- LiteLLM's built-in guardrail buffers a streamed answer until it is complete; on v1.83.10 it sends it back masked again
  (`<PERSON>`) instead of restored.
- It numbers overlapping detections separately, which breaks placeholders. With the analyzer below, 38% of a 484-sample
  benchmark answer could not be restored. LiteLLM's main branch has a fix that is not in a release yet.

A benchmark of 484 synthetic Swiss samples in DE-CH, FR, IT and EN compared this setup with gheim (a Swiss-tuned PII
model with its own LiteLLM guardrail). With the same ID and number formats on both sides, both restore every answer;
gheim scores slightly higher on names and record numbers and runs faster on CPU, Presidio masks birth dates and more
international formats. Both sides' figures are optimistic, because the formats were written with knowledge of the test
data.

## Decision Drivers

- *No personal data reaches an external provider*, whoever calls: chats, agents (including side calls), bots.
- *Users read the real values*, also while an answer streams, without waiting for the whole answer.
- *German, French, Italian and English* with one setup, Swiss formats included.
- *Nothing leaves the deployment for detection*, and only the gateway and agents can reach the detector.
- *A failure must not leak*: if detection is unavailable, the call is refused.
- *Patterns are configuration*, changeable without a code release.

## Decision

The gateway anonymises chat requests through a project-managed Presidio analyzer and a custom LiteLLM guardrail.

- **Analyzer**: Presidio 2.2.364 with GLiNER's multilingual PII model and spaCy's German pipeline baked into our image
  (`infra/deployment/docker/presidio-analyzer`, hub offline at run time, pinned model revision). Every text is analysed
  under the language code `de`, where all recognizers are registered; GLiNER is multilingual, so one language means one
  model copy in memory. The recognizers (Swiss and international patterns, GLiNER labels) are a mounted deployment
  template, not part of the image. The stock REST server gets two changes: a shared API key on every route but the
  health probe, and a GLiNER text chunker whose chunks start at a word (Presidio's own starts the next chunk inside a
  word, and GLiNER then tags word tails such as "nne" as names). The analyzer lives alone with its callers in the
  internal `pii-detection` network.
- **Guardrail** (`litellm_functions/pii_anonymisation_guardrail.py`, mounted like the RAG-figure callback): one numbered
  placeholder per distinct value, overlapping detections merged before numbering, placeholders already in the input
  passed through and never reused. The answer is restored in its text, reasoning and tool-call arguments (JSON kept
  valid), streamed chunk by chunk with only a possible placeholder prefix held back. The placeholder map stays in the
  gateway process, keyed by the request's call id, and never enters request metadata, which LiteLLM forwards to spend
  logs and callbacks. A failed or timed-out analysis fails the call. Pronouns, roles and field labels in the four
  languages ("Sie", "Benutzer", "Adresse", "IBAN") are an allow-list in the gateway config, also when followed by a short
  number ("Position 2"): GLiNER tags them as names or as the type they name, and masking them garbles the prompt and the
  answer and hides line numbers from document extraction.
- **Which calls**: every model declares `model_info.aihub_hosting_location` (`local`, `swiss_cloud`, `eu`, `global`).
  The guardrail runs on every call to a model that is not `local`; a model without the field counts as external, and the
  compose generator rejects missing or unknown values. Calls to local models run it when they request
  `pii-anonymisation` by name.
- The built-in Presidio guardrails and the Presidio anonymizer service are removed.

### Rejected: LiteLLM's built-in Presidio guardrail

It cannot stream a restored answer and breaks placeholders on overlapping detections in every released version.

### Rejected: one recognizer set per language

Per-language spaCy pipelines would need a language decision per request and one model copy per language. GLiNER covers
all four languages under one code.

## Consequences

### Positive

- External providers receive placeholders only, for every caller, without changes in the callers.
- Answers keep streaming; the first text arrived after about 0.2 s in the benchmark.
- Patterns change with `make generate-compose` and an analyzer restart.

### Trade-offs

- Analysis adds latency: a few hundred milliseconds for a question, about 50 s on CPU for a 20,000-token prompt.
- The analyzer image is 5.5 GB and needs up to 4 GB of memory.
- Restoration depends on the model writing placeholders back unchanged.
- The patterns for record numbers, insurance cards, ID documents and birth dates were written against synthetic data and
  need checking against real document formats.
- The guardrail uses LiteLLM's custom-guardrail interface; a LiteLLM upgrade must re-run its tests.
- Embeddings, reranking, transcription and image generation are not anonymised.

### Related Decisions

- `2026_07_10_inline_rag_figures_as_base64.md` (mounted LiteLLM module pattern)
- `2025_12_22_docker_network_isolation.md` (network zones)
- `2026_04_28_litellm_pipeline_message_redaction.md` (spend log content)
