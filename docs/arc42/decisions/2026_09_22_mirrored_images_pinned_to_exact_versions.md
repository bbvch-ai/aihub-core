# Mirrored Third-Party Images Are Pinned to Exact Versions

## Context

`infra/deployment/compose-config.yml` pinned Langfuse to the floating major tag `3` — `langfuse/langfuse:3` and
`langfuse/langfuse-worker:3`. Rendered through `global.registry_prefix`, that resolves to
`ghcr.io/bbvch-ai/aihub-core/langfuse/langfuse:3`: **our GHCR mirror**, which is the only pull source for every non-dev
compose stage and for customer self-hosted release bundles.

The mirror is populated by `make mirror-image` (`infra/deployment/Makefile`), a manual `docker pull` → `docker tag` →
`docker push`. It copies a *floating* tag to a *floating* tag **name**. Upstream's `:3` means "newest 3.x" and keeps
moving; our copy is a point-in-time snapshot wearing the same name. Nobody ran that command between 2026-01-15 and
2026-09-22, so compose served Langfuse **3.147.0** while upstream's `:3` had reached **3.225.8** — eight months and 78
minor versions of drift, on a component that stores full prompt and response content.

`aihub-k8s` pulls `docker.io/langfuse/langfuse:3` directly, so Kubernetes ran 3.225.x. One tag name, two registries,
two realities, and nothing comparing them.

Four properties kept this invisible:

1. **The version never appears in git.** `compose-config.yml` read `:3` before a mirror refresh and `:3` after one. No
   diff, no commit, no review artifact — nothing for a human to notice.
2. **No bot can watch it.** The `docker` ecosystem in `.github/dependabot.yml` scans Dockerfile directories only.
   Pointing any bot at the *generated* compose files would not help either: the pinned value is
   `ghcr.io/bbvch-ai/aihub-core/...`, so it would ask our own frozen mirror whether anything newer exists — circular,
   and structurally incapable of detecting upstream drift. This applies to every mirrored image, not just Langfuse.
3. **No CI check.** The `Env / Compose Consistency` job regenerates and runs `make check-env`, but never
   `git diff --exit-code`, and nothing asserts the mirror actually serves the tag we pinned.
4. **No owner.** A manual developer command with no schedule and no runbook.

The drift was not cosmetic. Langfuse added a private-address check on LLM connections in 3.167.1, so 3.225.x rejects
our in-network base URLs with `400 Blocked IP address detected` while 3.147.0 accepts them. That gap is the sole reason
the evaluator-provisioning bug presented as Kubernetes-only; the defect was in our code on every deployment the whole
time. See `2026_09_22_langfuse_llm_connections_stay_in_cluster.md`, which names this work as its follow-up.

A second defect falls out of the same mechanism: `docker pull` resolves a multi-arch index down to the pushing host's
single platform. Upstream `langfuse/langfuse:3.225.8` is a manifest list (`linux/amd64` + `linux/arm64`); the mirror's
`:3` is a bare single-platform OCI image manifest, pushed from one developer's laptop. CI runs on `ubuntu-24.04-arm`.

## Decision Drivers

- **Reproducibility.** The release bundle promises version-pinned images to self-hosted operators. A floating tag voids
  that promise for the services it covers, and `generate_compose.py` passes flat-string tags through to bundles verbatim.
- **Irreversibility.** Langfuse migrations are forward-only, so a surprise upgrade cannot be undone at the data layer.
  A version bump must be a deliberate, reviewed act.
- **The mirror is the only pull source** for non-dev compose. A pin without a corresponding mirror push is not a
  version — it is an outage.
- **Cross-repo convergence.** The Helm chart lives in `aihub-k8s`, so compose and Kubernetes agreeing on a version has
  to be explicit rather than assumed.
- **Detectability without vigilance.** The failure mode was eight months of nobody looking. Any fix that depends on
  somebody remembering is the same fix that already failed.

## Decision

**1. Exact pins.** `compose-config.yml` pins `langfuse/langfuse:3.225.8` and `langfuse/langfuse-worker:3.225.8`. The
`langfuse/` vendor segment is retained deliberately: the value *is* the GHCR repository path suffix, and the live mirror
package is `ghcr.io/bbvch-ai/aihub-core/langfuse/langfuse`. This matches the existing minority convention
(`clickhouse/clickhouse-server`, `otel/opentelemetry-collector-contrib`). Both entries must always carry the identical
version — a mismatch means two migration sets racing the same databases.

**2. 3.225.8 specifically**, because Kubernetes had already run it. Converging on a proven schema beats picking a third
version. Upstream `:3` and `:3.225.8` were verified to be the same digest at the time of pinning, for both images.

**3. Standing mirror procedure.**

- Mirror with `docker buildx imagetools create`, **not** `make mirror-image` — it copies the whole manifest index
  without pulling layers, so the multi-arch index survives.
- Mirror **before** the pin is committed. The pin is a promise the registry must already keep.
- **Never re-point an existing tag.** Push the new exact tag; leave the old one in place as an image-level rollback
  target.

**4. Kubernetes pins the same exact version.** Today's chart uses `tag: "3"` with `pullPolicy: IfNotPresent`, which is
worse than per-instance drift: a node never re-pulls a tag it already holds, so `:3` there means "whatever 3.x this node
cached first, indefinitely", and two pods in one namespace can differ. Pinning makes `IfNotPresent` correct. Executed in
the chart repo; recorded here because the decision is shared. Pinning Kubernetes *backwards* to a pre-check Langfuse is
rejected in the sibling ADR.

**5. Bump mechanism.** A scheduled drift check that compares three values — the pinned compose tag, the pinned chart
tag, and the newest upstream release in the tracked line — and opens an issue on divergence; plus a PR-time assertion
that the mirror actually serves the pinned tag, so "pinned but never mirrored" is a red check rather than a staging
outage. Deliberately **not** an auto-PR: a Langfuse bump needs a human mirror push and a migration measurement.
Deliberately **not** Dependabot, for the reason in Context — it would poll our own mirror and would edit generated files
that the next `make generate-compose` reverts. This requires a `mirror_sources:` map recording each mirrored image's
upstream origin; that metadata exists nowhere today, which is why no off-the-shelf bot can be wired up without it.

### Rejected: keep the floating `:3` and just refresh the mirror

This reintroduces the identical failure with no signal. The version would still be absent from git, the two deployments
would still resolve one tag name to different bytes at different times, and the next eight-month gap would be equally
invisible.

## Consequences

### Positive

- The running Langfuse version is a reviewable value in git. A bump is a diff.
- Compose and Kubernetes converge on one proven version, which is what makes the evaluator-provisioning fix verifiable
  on compose at all.
- The mirror now carries multi-arch indexes, so arm and amd hosts get the same image.
- Measured on a throwaway stack seeded from real 3.147.0 data: the 51 new Prisma migrations took **0.55 s**, a cold
  install applied all 424 in **1.8 s**, and boot-to-healthy was **17 s** against a ~180 s healthcheck budget — a ~10x
  margin, so no healthcheck tolerance change was warranted. ClickHouse advanced 34 → 37. Valkey 8.0.5 (reporting
  `redis_version:7.2.4`) raised no BullMQ version-check complaint.

### Trade-offs

- **Every future Langfuse upgrade is explicit work**: mirror the exact tag, bump the pin, regenerate, measure. That is
  the point, but it is real cost that a floating tag hid.
- **Rollback is image-only.** Reverting the pin restores old binaries against a migrated schema. Migrations are
  forward-only, so restoring a pre-upgrade backup is *not* a rollback: the restore path validates artifact presence
  only, has no version stamp, and reverts Postgres and ClickHouse independently with no cross-consistency check and no
  post-restore migration step.
- **The mirror grows one tag per bump.** Old tags are kept deliberately as rollback targets.
- **Anyone adding a new mirrored image must register its upstream source**, or the drift check cannot cover it.
- **The dev-scale migration numbers are a lower bound.** ClickHouse migration time scales with `traces`/`observations`
  row counts; production-size timing has to come from a staging rehearsal.

### Related Decisions

- `2026_09_22_langfuse_llm_connections_stay_in_cluster.md` — the private-address fix this pin depends on, and which
  names this work as its follow-up.
- `2026_07_23_upgrade_seaweedfs_to_4_01_for_content_disposition.md` — the precedent for treating a mirrored-image
  version change as a deliberate decision rather than a routine tag bump.
- `2026_02_10_replace_phoenix_with_langfuse.md` — why Langfuse is in the stack at all.
