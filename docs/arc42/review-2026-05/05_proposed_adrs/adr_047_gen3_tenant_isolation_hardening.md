# Gen 3 (aihub-k8s) Tenant Isolation Hardening

**Status**: Proposed (2026-05-29) **Severity**: P0+ (blocks shared multi-tenant SaaS for untrusted/regulated tenants)
**Drives**: Gen 3 `aihub-k8s` multi-tenancy; concretises ADR-NEW-002 (Tenant Data Isolation Strategy); pairs with
[`adr_040`](adr_040_k8s_chart_core_version_pinning.md), [`adr_020`](adr_020_document_acl_inheritance.md),
[`adr_012`](adr_012_usage_limits_enforcement.md)

## Context

Review 2026-05 inspected the actual Gen 3 implementation in the `aihub-k8s` repo (Helm charts `aihub-common` +
`aihub-tenant`, Terraform for AKS / Stoney Magnum). The tenancy model is **namespace-per-tenant for compute + a pooled
shared data layer**:

- **Per-tenant** (namespace `tenant-<name>`): API, Web, OpenWebUI, Dagster, bot, 9 agents, 2 RAG pipelines, Presidio,
  Jupyter, Playwright, rclone, OTEL collector, and — notably — **its own NATS, Redis, and Neo4j**. PgBouncer fronts the
  shared Postgres.
- **Shared** (namespace `aihub-common`): PostgreSQL (CloudNativePG, db-per-tenant **+ user-per-tenant** ✅), FerretDB/
  Mongo (db-per-tenant), Milvus (standalone, db-per-tenant), SeaweedFS (bucket + credential per tenant ✅), Keycloak
  (realm-per-tenant ✅), plus shared LiteLLM, Langfuse, MinerU, SearXNG.

The compute/namespace split, Postgres user-per-tenant, SeaweedFS credential-per-tenant, and Keycloak realm-per-tenant
are genuine isolation. **But the isolation is logical, not hardened.** Verified gaps:

1. **No NetworkPolicy anywhere** (`grep "kind: NetworkPolicy"` across the repo → 0). Tenant namespaces are not network-
   isolated: a pod in `tenant-a` can reach services in `tenant-b` and every shared service unrestricted. The tenant
   README says "Network policies (can be enabled)" but no template exists.
2. **Shared Milvus credential across all tenants** — `helm/aihub-tenant/values.yaml:105`: *"must match aihub-common
   milvus.user (same for all tenants)"*; `aihub-common/README.md`: *"shared user credential for tenant workloads in
   `milvus.user`"*. Vector isolation relies only on the app passing the correct per-tenant Milvus DB name; it is **not**
   enforced at the credential level → a tenant workload (or a compromised pod) can read another tenant's Milvus DB.
3. **No ResourceQuota / LimitRange per namespace** (grep → 0). Only per-pod requests/limits exist → noisy-neighbor: one
   tenant can starve the cluster; no per-tenant resource or cost ceiling.
4. **Shared single-instance data stores** (Postgres 1 cluster, FerretDB 1, Milvus standalone) serve all tenants → large
   blast radius; the Milvus "memory wall" is now a cluster-wide risk. HA is optional and off by default.
5. **Semi-manual provisioning**: adding a tenant = edit `values.secrets.yaml` + redeploy `aihub-common` (creates db/user/
   bucket/realm), then create agent instances in the UI. No self-service tenant provisioning API.

This is fine for trusted/internal tenants on one cluster, but not enterprise-grade for untrusted or regulated
(banking/healthcare) tenants.

## Decision Drivers

- **Hard isolation**: tenants must not reach each other's network, data, or compute without explicit allow.
- **Least privilege at the data layer**: vector/data access enforced by credentials, not by app convention.
- **Noisy-neighbor protection**: per-tenant resource and cost ceilings.
- **Blast-radius reduction**: a shared-store failure should not take down every tenant.
- **Operational scale**: onboarding a tenant should be an API call, not a manual values edit + UI clicks.
- **CNI reality**: NetworkPolicy enforcement depends on the CNI (Azure CNI / Calico on AKS; Calico on Stoney Magnum).

## Decision

Adopt four hardening workstreams before declaring Gen 3 ready for untrusted/regulated multi-tenancy:

1. **NetworkPolicy per tenant namespace** — default-deny ingress + egress, then allow only: (a) ingress from
   `ingress-nginx`, (b) egress to the specific `aihub-common` shared services (Postgres, FerretDB, Milvus, SeaweedFS,
   LiteLLM, Keycloak, Langfuse, MinerU, SearXNG) on their ports, (c) DNS. Block all tenant↔tenant traffic. Ship as a
   templated `NetworkPolicy` in `aihub-tenant` (enabled by default).

2. **ResourceQuota + LimitRange per tenant namespace** — cap CPU/memory/storage/pod-count per tenant; pair with a
   per-tenant LLM cost cap on the shared LiteLLM gateway ([`adr_012`](adr_012_usage_limits_enforcement.md)).

3. **Per-tenant Milvus credential** — provision a Milvus user per tenant (Milvus 2.4+ RBAC) with grants scoped to that
   tenant's database only; remove the shared `milvus.user`. Tenant workloads use their own credential. Aligns with
   document-ACL enforcement ([`adr_020`](adr_020_document_acl_inheritance.md)).

4. **Shared-store HA + self-service provisioning** — CNPG ≥ 2 instances, Milvus cluster mode (ADR-NEW-015), FerretDB HA;
   and a tenant provisioning API (ADR-NEW-008) that creates the namespace, db/user, bucket, realm, NetworkPolicy, and
   quota in one call — replacing the manual `values.secrets.yaml` + UI steps.

5. **Scaling + per-tenant stateful HA** — there is **no HPA** and every service defaults to **1 replica** (only the
   NGINX ingress runs 2; the node pool is fixed). Add HPA for the stateless tiers (API, agents, RAG pipelines, bot,
   Presidio, OTEL). For **NATS overload, scale consumers first** (durable consumer + queue group — the dispatcher is
   stateless), as that is usually the bottleneck, not the broker. The per-tenant NATS/Redis/Neo4j are single-node; the
   hand-rolled NATS chart is **not clusterable as-is** (hard-coded `server_name`, no `cluster{}`/routes, no headless
   service), so true NATS HA/throughput needs a clustered JetStream deployment (official NATS chart or chart fix) with
   stream replicas R=3. Redis (Sentinel/cluster) and Neo4j (Enterprise clustering) have the same single-node limitation.

## Consequences

**Positive**

- Real tenant isolation (network + data + resource) → viable for untrusted/regulated tenants.
- Vector data leakage path closed (per-tenant Milvus credential).
- Noisy-neighbor and cost-runaway bounded per tenant.
- Smaller blast radius once shared stores are HA.
- Onboarding becomes mechanical (API), not manual.

**Negative**

- More Helm surface (NetworkPolicy, quotas, per-tenant Milvus RBAC) and harder debugging (a missing egress rule breaks a
  service silently).
- HA for shared stores costs more compute/storage.
- Per-tenant Milvus RBAC adds credential lifecycle management.

**Open items**

- Confirm the CNI on each target (AKS Azure CNI / Calico; Stoney Magnum) enforces NetworkPolicy; Flannel alone does not.
- Whether to keep the pooled shared data layer or move high-sensitivity tenants to dedicated stores (per-customer tier,
  see [`adr_000`](adr_000_sovereignty_compliance_path.md) Option C analogue).
- Self-service provisioning API ownership and auth model.
- NATS scaling path: consumers-first (scale dispatcher/agent replicas) vs broker clustering — and whether to replace the
  hand-rolled NATS StatefulSet with the official NATS Helm chart for a JetStream cluster (R=3); decide whether HA is
  needed per-tenant or only for high-tier tenants.

## References

- `aihub-k8s` repo: `helm/aihub-tenant/values.yaml:105` (shared Milvus credential), `helm/aihub-common/README.md`
  (shared data layer), tenant + common `templates/` (no NetworkPolicy / ResourceQuota present).
- ADR-NEW-002 (Tenant Data Isolation Strategy) — this ADR is the Gen-3-specific concretisation.
- [`adr_040`](adr_040_k8s_chart_core_version_pinning.md) (chart core-version pin), ADR-NEW-008 (Tenant Provisioning
  Automation), ADR-NEW-015 (Milvus Cluster Mode).
- Gen 3 diagram: [`../c4/deployment_generations.md`](../c4/deployment_generations.md).
- [Kubernetes NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) ·
  [Milvus RBAC](https://milvus.io/docs/rbac.md).
