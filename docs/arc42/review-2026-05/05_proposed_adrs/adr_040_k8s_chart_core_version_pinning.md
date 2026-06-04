# aihub-k8s Helm Chart Core Version Pinning

**Status**: Proposed (2026-05-28) **Severity**: P0 (reproducibility, audit trail, supply chain) **Drives**: Overview
§3.1 #20 (K8s migration path), §3.5 #5 (W\*P `${CORE_VERSION:-latest}` fallback);
[Details §24 ADR-NEW-040](../02_architecture_review_details.md#24-proposed-adrs-36-total)

## Context

The Gen 3 deployment target `aihub-k8s` ships two Helm charts:

- `aihub-common` — shared services per cluster (CloudNativePG, Keycloak Operator, SeaweedFS, Milvus, FerretDB, Langfuse,
  LiteLLM, MinerU, SearXNG).
- `aihub-tenant` — per-namespace tenant deployment (~13 services: api, web, openwebui, dagster, NATS, Redis, Neo4j,
  Phoenix, Jupyter, Playwright, Presidio, rclone, agents).

Verified 2026-05-28:

- Both `Chart.yaml` files declare `appVersion: "0.1.0"`.
- Both charts pull container images via Helm values resolved against `${CORE_VERSION:-latest}` (defaults to the Docker
  tag `latest` if the env var is unset at deploy time).
- The previous version of this overview's Component-versions table claimed "chart targets v0.289.3" — that is
  **incorrect**. The chart does not pin a core version at all; the deployed version is whatever `CORE_VERSION` is set to
  at `helm upgrade --install` time.

This is the same anti-pattern flagged in §3.5 #5 for **aihub-wpe** (docker-compose
`image: ghcr.io/...:${CORE_VERSION:-latest}`). The Gen 3 chart inherits the Gen 1 customer flaw rather than fixing it.

Operational consequences:

- **No audit trail of which core version is in production.** `helm history` shows the chart revision; it does not show
  the image tag that the chart resolved to.
- **`latest` fallback silently rolls deploys forward.** If a sysadmin runs `helm upgrade --install` without exporting
  `CORE_VERSION`, every image moves to `:latest`. There is no fail-fast.
- **Gen 3 tenants can drift independently of one another.** Two tenants on the same cluster can be on different core
  versions because the env var is set per-deploy, not per-chart.
- **Sets a bad precedent.** The k8s chart is the canonical infrastructure artifact for new customers; whatever it does,
  new customer repos will copy.

## Decision Drivers

- **Reproducibility**: A given Helm chart revision must deploy a single, well-known set of images.
- **Audit**: `helm history` + `git log` for the chart repo must answer "what version was running on date X".
- **Fail-fast on misconfiguration**: A missing env var must fail the deploy, not silently roll forward.
- **Coordinated release cycle**: Core releases and chart releases must be matched, not independent.
- **Backward compatibility**: Existing test tenants (`tenant1`, `jointcreate`, `postgres-test`) must keep working during
  the migration.

## Decision

Adopt a chart-level core-version-pin policy:

1. **`Chart.yaml` `appVersion` reflects the deployed core version.** When `aihub-core` releases v0.290.5, the chart repo
   gets a matching tagged release `aihub-common-0.290.5` / `aihub-tenant-0.290.5` with `appVersion: "0.290.5"`.

2. **`values.yaml` pins image tags to `Chart.appVersion`.** Replace `${CORE_VERSION:-latest}` with
   `{{ .Chart.AppVersion }}` (or an explicit string per release). The env-var path becomes the *override* mechanism for
   development only, never the default.

3. **Fail-fast on override.** When `CORE_VERSION` is provided, the chart emits a NOTES.txt warning explaining that the
   deployed version differs from `Chart.appVersion`. A planned `--set` flag at the cluster level forbids overrides in
   production namespaces.

4. **CI gate.** A workflow in `aihub-k8s` validates that:

   - Every release tag has matching `Chart.yaml` `appVersion` and `version`.
   - No `:latest` tag appears in resolved Helm output (`helm template … | grep ':latest'`).
   - The chart can install against a kind cluster with no env-var overrides.

5. **Customer template inherits the policy.** When a customer migrates to Gen 3 (per §3.1 #20), they consume the pinned
   chart by tag, not by `main`. The `aihub-{customer_id}` repo records the chart version in its README.

## Consequences

**Positive**

- One-line answer to "what core version is in prod": `helm list -A | grep aihub`.
- Each chart release is reproducible across rebuilds.
- Aligns the Gen 3 path with the SDK versioning policy proposed in ADR-NEW-001.
- Cleans up the W\*P-style anti-pattern at the source instead of fixing it per customer.

**Negative**

- Every core release now also produces a chart release. Release pipeline gets one more job (charts → ghcr OCI registry).
- Operators losing the freedom to upgrade just the image without a chart bump — by design, but a workflow change.
- Existing test tenants must be re-deployed once the migration lands; their drift becomes visible.

**Open items**

- Whether to publish the chart to a public OCI registry (ghcr.io) or keep it internal.
- Whether `aihub-common` and `aihub-tenant` should release on the same cadence as `aihub-core` or can lag (e.g., monthly
  tag matching the latest core release of the month).
- How to test against multiple cluster types (AKS + Stoney Magnum) per release without burning hours of CI minutes.

## References

- Overview §3.1 #20 (K8s migration path), §3.5 #5 (W\*P fallback), Component versions table footnote on the chart.
- `aihub-k8s/helm/aihub-common/Chart.yaml` and `aihub-k8s/helm/aihub-tenant/Chart.yaml` — current `appVersion: "0.1.0"`.
- Proposed ADR `adr_NEW-001` — SDK Versioning and Deprecation Policy (paired policy).
- [Helm Chart Best Practices — Versioning](https://helm.sh/docs/chart_best_practices/conventions/#versioning).
