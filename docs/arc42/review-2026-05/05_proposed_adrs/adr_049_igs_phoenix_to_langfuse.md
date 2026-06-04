# aihub-igs: Reconcile Observability — Phoenix in Compose vs Langfuse in Eval Docs

**Status**: Proposed (2026-05-29) **Severity**: P1 (doc/config drift; pre-Langfuse component)
**Drives**: Overview §3.7 #4 (IGS Phoenix/Langfuse drift); [`../c4/igs.md`](../c4/igs.md)

## Context

`aihub-igs` presents two inconsistent observability stories:

- **`docker-compose.latest.yml`** deploys **Phoenix v10.0.4** (`phoenix:version-10.0.4`) as the ML-observability
  backend, plus an **OTEL collector** that ships to **SigNoz Cloud (EU)** via `OTEL_CLOUD_ENDPOINT`. There is **no
  Langfuse service** in the compose. Phoenix v10.0.4 predates the core's adoption of Langfuse (ADR `2026_02_10`).
- **`eval/README.md`** states the opposite: *"Langfuse is the system of record … deployed alongside the IGS platform
  (`https://langfuse.igs.ai-agents.ch`)"*, and the entire eval workflow (datasets, LLM-as-judge evaluators including
  the custom `Citation Quality` judge, experiment runs) is documented against a Langfuse instance.

So either (a) Langfuse runs out-of-band (not in the tracked compose — possibly provided by the Gen 2 playbook), or
(b) the eval docs describe an intended state that the deployed stack does not yet match. Both readings are a
**doc/config drift**: a reviewer or operator cannot determine the real observability topology from the repo.

This matters because IGS is the first Gen 2 customer and a compliance-sensitive (internal infosec directives) use
case — observability for prompt/response capture, cost tracking, and eval is exactly what an auditor will ask about.

## Decision Drivers

- **Single source of truth**: the deployed compose and the eval docs must agree on which observability backend is
  authoritative.
- **Core alignment**: core moved to Langfuse (ADR `2026_02_10`); Phoenix v10.0.4 is a pre-Langfuse component that
  diverges from the current platform baseline (same class of drift as demoscope/fmh).
- **Sovereignty**: SigNoz Cloud "EU" already raises a data-residency question (Overview §5.8); adding a second cloud
  observability backend compounds it.
- **Eval continuity**: the IGS `Citation Quality` judge + `igs_guisan` dataset are valuable and must keep working
  through the reconciliation.

## Decision

1. **Pick Langfuse as the authoritative LLM-observability backend for IGS** (aligns with core ADR `2026_02_10`).
   Either:
   - confirm and document the existing `langfuse.igs.ai-agents.ch` instance and **add it to the tracked compose /
     playbook role** so the topology is reproducible, or
   - if no Langfuse instance actually runs, deploy one (core image) and wire the agents/API/LiteLLM to it.
2. **Remove or justify Phoenix.** If Langfuse covers the need, drop `phoenix` from the IGS compose template. If
   Phoenix is intentionally retained for a specific trace view, document why in this ADR and in `eval/README.md`.
3. **Decide the OTEL → SigNoz Cloud (EU) path** under the core SigNoz-region decision (Overview §5.8): keep, move to
   self-hosted SigNoz, or route OTEL to Langfuse-compatible storage. Document the sovereignty rationale.
4. **Sync the docs**: `eval/README.md` and `c4/igs.md` must reflect the chosen topology; regenerate the compose.

## Consequences

**Positive**

- One authoritative observability backend, reproducible from the repo.
- IGS aligns with the core Langfuse baseline; the `Citation Quality` eval keeps its system of record.
- Sovereignty posture for observability data is explicit, not accidental.

**Negative**

- Requires confirming the live topology with the IGS ops team and a compose/playbook change.
- If Langfuse must be newly deployed, that is added pilot scope before production cutover.

**Open items**

- Confirm whether `langfuse.igs.ai-agents.ch` is live and who operates it (playbook role vs manual).
- Fold this into the broader Phoenix → Langfuse migration tracked for demoscope/fmh (same pre-Langfuse divergence).

## References

- Overview §3.7 #4 (the finding), [`../c4/igs.md`](../c4/igs.md) (IGS observations).
- `aihub-igs/docker-compose.latest.yml` (`phoenix`, `otel-collector`), `aihub-igs/eval/README.md` (Langfuse).
- Core ADR `2026_02_10` (Phoenix → Langfuse), Overview §5.8 (SigNoz Cloud region / sovereignty).
