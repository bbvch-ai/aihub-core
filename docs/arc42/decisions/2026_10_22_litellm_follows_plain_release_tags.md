# LiteLLM Follows Its Plain Release Tags

## Context

The gateway ran LiteLLM `v1.83.10-stable`. LiteLLM stopped publishing `-stable` tags after `v1.83.14-stable`; newer
releases carry plain tags (`v1.106.2`) and several minor lines receive patch releases side by side. Staying on the last
`-stable` tag would leave the gateway on a line that receives no fixes, while LiteLLM has had a series of security
incidents. The upgrade also had to keep everything the platform relies on: the config template and its variants, the
mounted callbacks (RAG figure inlining, the Presidio guardrail and its audit span), prompt injection detection, OTEL,
embedding caching, per-user keys and spend logs, and the model info fields the Hub reads.

## Decision Drivers

- Security fixes reach the gateway without waiting for a `-stable` tag that no longer comes.
- One version on every stage, mirrored into our registry like every other upstream image.
- A database migration that is fast and reversible on a production-sized spend log.

## Decision

- The gateway follows LiteLLM's plain release tags and moves to the newest patch release of the newest line. This
  upgrade pins `v1.106.2` (`image_tags.litellm`), mirrored from `ghcr.io/berriai/litellm:v1.106.2`.
- Every upgrade re-runs the guardrail's unit tests with the matching `litellm` package and its live tests through a real
  proxy (`infra/deployment/CLAUDE.md`), and the gateway smoke checks: chat, streamed chat, embeddings, reranking,
  transcription, RAG figure inlining, a per-user key with its spend log, and prompt injection detection.
- Rollback is the previous image tag. Migrations between `v1.83.10-stable` and `v1.106.2` only add tables, columns and
  indexes, and `v1.83.10-stable` starts and serves on the migrated database. A `pg_dump -Fc` of the `litellm` database
  taken before the upgrade is the fallback when an older version must also see the old schema.

## Consequences

### Positive

- The gateway receives LiteLLM's security fixes again.
- 98 migrations ran in 2.1 s on a copy with 1.5 million spend log rows (3.3 GB); the spend log changes are column
  additions with constant defaults, which PostgreSQL applies without rewriting the table.
- Prompt injection detection now rejects similarity matches with a 400. On `v1.83.10-stable` the same request passed.

### Trade-offs

- Plain release tags appear several times a week; picking one is a judgement call rather than following a label.
- Prompt injection detection can now reject a legitimate message that resembles a known attack. Callers see a 400
  "Rejected message. This is a prompt injection attack."
- Models priced per second or per image report `input_cost_per_token` and `output_cost_per_token` as missing rather than
  `0`; the Hub's model DTO accepts both.
- Image generation was not verified: the dev deployment reaches no image provider, on either version.

### Related Decisions

- `2026_10_21_presidio_streaming_guardrail_for_pii_anonymisation.md` (guardrail interface the upgrade must keep)
- `2026_08_06_per_user_litellm_key_as_cost_attribution_carrier.md` (tags, amended for this version)
- `2026_09_23_litellm_config_variants_selected_per_deployment.md` (config variants)
