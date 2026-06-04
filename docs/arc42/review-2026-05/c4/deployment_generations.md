# C4 — Deployment Generations (Gen 1 / Gen 2 / Gen 3)

> Snapshot 2026-05-28. Source of truth: Overview §1, §5.8 (Gen 2 pattern), §References (Gen 3 stack), and the ecosystem
> diagram in [`../01_architecture_review_overview.en.md`](../01_architecture_review_overview.en.md). The three
> generations differ in *how a deployment is provisioned, configured, and run* — not in the application code.

Same colour key as the other `c4/` files: IaC/config repos (amber), app/stack services (blue), data & backup (teal),
external systems (grey), known gaps (red).

**At a glance**: Gen 1 = manual VM + docker-compose (**all 5 production customers today**). Gen 2 = Ansible Pull +
OpenStack Infomaniak (**infra ready; first customer `aihub-igs` onboarding as a pre-production pilot**). Gen 3 =
Kubernetes `aihub-k8s` (**emerging, test tenants only**).

## Gen 1 — Manual VM + docker-compose

How every production customer (B\*D, C\*C, W\*P, Dem\*scope, F\*H) runs today: a single VM, a docker-compose stack, and
shell scripts run by hand.

```mermaid
flowchart TB
  classDef repo fill:#fff4e1,stroke:#e8a33d,color:#000
  classDef svc fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef data fill:#d8f5f0,stroke:#2bb0a0,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  OPS["Sysadmin<br/>manual SSH · scp · copy-paste"]:::ext
  GH["GitHub / GHCR<br/>core images @ git tag / CORE_VERSION"]:::ext

  subgraph G1["Gen 1 — Manual VM + docker-compose · ALL 5 prod customers (B*D · C*C · W*P · Dem*scope · F*H)"]
    direction TB
    subgraph REPO["Customer repo"]
      DC["docker-compose.yml<br/>(+ agents / pipelines)"]:::repo
      SH["shell scripts / deploy.sh<br/>(F*H variant: Pulumi → Azure Container Apps)"]:::repo
    end
    subgraph VM["Single VM (Azure / on-prem)"]
      STACK["docker-compose stack<br/>core + custom agents/pipelines<br/>Traefik · OpenWebUI · API · NATS · Milvus · FerretDB · SeaweedFS"]:::svc
      BK["Backup on SAME VM<br/>⚠ violates 3-2-1 — VM dies = total loss"]:::warn
    end
    GAP["⚠ No auto-update: security patches applied by hand<br/>⚠ no rollback · no drift detection · no audit trail"]:::warn
  end

  OPS -->|edit + deploy| DC
  OPS -->|run by hand| SH
  SH -->|docker compose up| STACK
  GH -->|docker pull| STACK
  STACK -.snapshot.-> BK
  STACK -.->|operational gaps| GAP
```

**Read in one line**: a person SSHes in, copies a docker-compose file and runs a script; the stack pulls core images by
git tag; backups sit on the same VM and patches are manual. Simple, but **no HA, no off-site backup, no auto-update, no
audit trail** — the source of most Gen 1 customer findings (§3.2–§3.6).

## Gen 2 — Ansible Pull + OpenStack Infomaniak

Self-configuring VMs on Swiss-sovereign Infomaniak OpenStack, reconciled every 15 minutes by Ansible Pull. The
infrastructure is ready and **`aihub-igs` is the first customer onboarding on this pattern** (Ansible-Vault config repo
`aihub-igs` with `secrets/igs.yml.vault`) — currently **pre-production / pilot**, not yet a full production cutover. See
[`igs.md`](igs.md).

```mermaid
flowchart TB
  classDef repo fill:#fff4e1,stroke:#e8a33d,color:#000
  classDef svc fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef data fill:#d8f5f0,stroke:#2bb0a0,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  GH["GitHub REST API + GHCR<br/>core release tarball + images<br/>⚠ deploy SPOF — no local fallback if GitHub down"]:::warn

  subgraph G2["Gen 2 — Ansible Pull + OpenStack Infomaniak (Swiss) · infra ready · NO prod customer yet"]
    direction TB
    subgraph REPOS["3-repo coordination · ⚠ no version-compat matrix / CI gate"]
      OPSR["aihub-ops<br/>OpenStack VM provisioning<br/>setup-aihub.sh · cloud-init · nightly drift check"]:::repo
      PB["aihub-playbook<br/>Ansible Pull every 15 min · 7 roles<br/>docker_runtime · traefik_proxy · signoz · aihub_application<br/>os_backups · custom_vars_sync · restore_os_backup"]:::repo
      CR["aihub-{customer}<br/>Ansible Vault (AES256) · custom config + secrets<br/>⚠ vault password on VM filesystem"]:::repo
    end
    subgraph VM["Self-configuring VM · Infomaniak OpenStack (Swiss-sovereign)"]
      STACK["docker-compose stack (core + custom)<br/>Traefik · OpenWebUI · API · NATS · Milvus · FerretDB · SeaweedFS"]:::svc
      SIGNOZ["SigNoz<br/>OTEL observability"]:::svc
    end
    SWIFT[("OpenStack Swift · vol-backup<br/>Restic (encrypted)<br/>⚠ same Infomaniak — off-host but NOT off-provider")]:::warn
  end

  OPSR -->|provision VM + cloud-init| VM
  GH -->|tarball + images| PB
  PB -->|pull & reconcile every 15 min| STACK
  CR -.vault secrets.-> PB
  STACK --> SIGNOZ
  STACK -.Restic.-> SWIFT
```

**Read in one line**: VMs provision themselves on Swiss Infomaniak and re-pull config every 15 min — security patches
auto-deploy, secrets are vault-encrypted, backups go to Swift. Remaining gaps: **3-repo version coupling, GitHub as a
deploy SPOF, same-provider backup, and a 15-min cadence too slow for hot-fixes**. Still single-server (docker-compose).

## Gen 3 — Kubernetes (`aihub-k8s`, emerging)

Terraform-provisioned K8s on Azure AKS or Stoney OpenStack Magnum, with two Helm charts giving **namespace-per-tenant**
multi-tenancy and horizontal scale. Emerging — only test tenants exist.

```mermaid
flowchart TB
  classDef repo fill:#fff4e1,stroke:#e8a33d,color:#000
  classDef svc fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef data fill:#d8f5f0,stroke:#2bb0a0,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  TF["Terraform · one deploy.sh for both clouds<br/>Azure AKS (Switzerland North · OIDC + workload identity)<br/>+ Stoney OpenStack Magnum (Flannel · Cinder · floating IP)"]:::repo
  GH["GHCR<br/>core images via ${CORE_VERSION:-latest}<br/>⚠ chart does NOT pin core version (adr_040)"]:::warn

  subgraph G3["Gen 3 — Kubernetes aihub-k8s · emerging · chart appVersion 0.1.0 · ⚠ unproven in prod"]
    direction TB
    subgraph CLUSTER["K8s cluster (Azure AKS or Stoney Magnum)"]
      direction TB
      subgraph COMMON["Helm chart: aihub-common (shared infra)"]
        CNPG[("CloudNativePG<br/>PostgreSQL 17 + pgvector")]:::data
        KCOP["Keycloak Operator<br/>realm per tenant"]:::svc
        SW[("SeaweedFS (shared)<br/>bucket prefix per tenant")]:::data
        MV[("Milvus standalone<br/>DB per tenant · ⚠ shared credential across tenants (cross-tenant read risk)")]:::warn
        SHARED["FerretDB · Langfuse · LiteLLM · MinerU · SearXNG (shared)"]:::svc
      end
      subgraph TENANT["Helm chart: aihub-tenant · namespace tenant-NAME · NAME.k8s.ai-agents.ch"]
        SVCS["~27 services per tenant<br/>api · web · openwebui · dagster · bot · OTEL collector<br/>NATS · Redis · Neo4j (own, per-tenant, single-node — ⚠ NATS not clusterable as-is)<br/>PgBouncer→shared PG · Jupyter · Playwright · Presidio · rclone · 9 agents · 2 RAG pipelines"]:::svc
        ING["NGINX Ingress + cert-manager (Let's Encrypt)"]:::svc
      end
    end
    TEST["Test tenants only: tenant1 · jointcreate · postgres-test<br/>⚠ no prod customer migrated · HA optional · Stoney Magnum limitation"]:::warn
    ISO["⚠ Multi-tenancy NOT fully isolated · scaling NOT automated<br/>no NetworkPolicy (tenant namespaces freely reachable) · no ResourceQuota (noisy-neighbor)<br/>no HPA · 1 replica by default (only ingress=2) · node pool fixed<br/>per-tenant NATS/Redis/Neo4j single-node (NATS not clusterable as-is)<br/>shared single-instance data stores (Postgres / FerretDB / Milvus) = blast radius<br/>semi-manual provisioning (no self-service API)"]:::warn
  end

  TF -->|provision cluster| CLUSTER
  GH -->|image pull| SVCS
  ING --> SVCS
  TENANT -->|consumes shared infra| COMMON
```

**Read in one line**: Terraform stands up a cluster on AKS or Stoney Magnum; `aihub-common` runs the shared data layer
(CNPG Postgres, FerretDB, Milvus, SeaweedFS) + shared LiteLLM/Keycloak/Langfuse/MinerU/SearXNG, while `aihub-tenant`
gives each tenant its own namespace, subdomain, app stack and **its own NATS / Redis / Neo4j**. It is the only
generation with namespace-per-tenant multi-tenancy and horizontal scale — **but the isolation is logical, not
hardened**: no NetworkPolicy, no ResourceQuota, a **shared Milvus credential across all tenants**, shared
single-instance data stores (blast radius), HA optional, semi-manual provisioning, charts don't pin the core version
(adr_040), and it's unproven in prod (test tenants only). Good for trusted/internal tenants; **not yet enterprise-grade
for untrusted/regulated tenants**.

## Comparison

| Aspect        | Gen 1 (today)               | Gen 2 (ready, unused)                         | Gen 3 (emerging)                                                                   |
| ------------- | --------------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------- |
| Provisioning  | Manual (SSH / copy-paste)   | `aihub-ops` — OpenStack + cloud-init          | Terraform (AKS / Stoney Magnum)                                                    |
| Config mgmt   | Shell scripts (FMH: Pulumi) | Ansible Pull (15-min reconcile)               | Helm (`aihub-common` + `aihub-tenant`)                                             |
| Runtime       | docker-compose on 1 VM      | docker-compose on 1 VM                        | Kubernetes pods                                                                    |
| Cloud         | Azure / on-prem             | Infomaniak OpenStack (Swiss)                  | Azure AKS or Stoney OpenStack Magnum                                               |
| Secrets       | `.env` on VM                | Ansible Vault (AES256)                        | K8s secrets / operators                                                            |
| Multi-tenancy | 1 deployment per customer   | 1 deployment per customer                     | namespace-per-tenant — ⚠ logical only (no NetworkPolicy/quota; shared Milvus cred) |
| Scaling / HA  | None (single VM)            | None (single VM)                              | Horizontal scale; ⚠ HA optional + shared data stores single-instance               |
| Backup        | Same VM ⚠ (no 3-2-1)        | Restic → Swift (off-host, same provider ⚠)    | Operator-managed (CNPG) + object store                                             |
| Auto-update   | Manual ⚠                    | 15-min Ansible Pull (⚠ slow for hot-fix)      | GitOps-style image pull (⚠ no chart version pin)                                   |
| Status        | **All 5 prod customers**    | Infra ready; **`aihub-igs` pilot (pre-prod)** | **Emerging**, test tenants only                                                    |

## Cross-reference

- Gen 2 pattern detail + concerns:
  [`../01_architecture_review_overview.en.md` §5.8](../01_architecture_review_overview.en.md).
- Gen 3 stack references:
  [`../01_architecture_review_overview.en.md` §References](../01_architecture_review_overview.en.md).
- Chart core-version pin policy:
  [`../05_proposed_adrs/adr_040_k8s_chart_core_version_pinning.md`](../05_proposed_adrs/adr_040_k8s_chart_core_version_pinning.md).
- Off-site backup / 3-2-1:
  [`../05_proposed_adrs/adr_030_offsite_backup_replication.md`](../05_proposed_adrs/adr_030_offsite_backup_replication.md).
- Per-customer deployments (5 Gen 1 prod + 1 Gen 2 pilot): [`bmd.md`](bmd.md), [`ctc.md`](ctc.md),
  [`demoscope.md`](demoscope.md), [`wpe.md`](wpe.md), [`fmh.md`](fmh.md), [`igs.md`](igs.md) (Gen 2 pilot).
- Gen 3 tenant-isolation hardening (NetworkPolicy, ResourceQuota, per-tenant Milvus credential, HA):
  [`../05_proposed_adrs/adr_047_gen3_tenant_isolation_hardening.md`](../05_proposed_adrs/adr_047_gen3_tenant_isolation_hardening.md).
