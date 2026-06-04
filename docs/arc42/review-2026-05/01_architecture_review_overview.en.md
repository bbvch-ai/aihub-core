# Architecture Review: Overview

**Document type**: Executive Summary for stakeholders.

**Audience**: C-level, Product, Business, Compliance/Legal, Architects, Technical Leads.

**Scope**: Swiss AI Hub ecosystem covering:

- `aihub-core` - platform application stack
- **Customer deployments**:
  - `aihub-b*d`, `aihub-c*c` - Gen 1 (Azure VM + shell scripts), in production
  - `aihub-Dem*scope`, `aihub-W*P`, `aihub-F*H` - Gen 1 (Azure / manual VM), in production
  - `aihub-Ig*s` - **Gen 2 pilot** (Ansible Pull + Infomaniak), pre-production; deploy-only, core app images on
    `:latest` (unpinned)
  - `aihub-Balmer-E*` - TBD (deployment generation, version, status pending team input)
- **Infrastructure repos (Gen 2)**:
  - `aihub-playbook` - Ansible Pull infrastructure-as-code (every 15-min reconcile)
  - `aihub-ops` - VM provisioning automation for OpenStack (cloud-init + setup script)
  - `aihub-{customer_id}` - per-customer encrypted secrets + custom config repos (template pattern)
- **Kubernetes deployment (Gen 3, emerging)**:
  - `aihub-k8s` - Terraform (Azure AKS + Stoney OpenStack Magnum) + two Helm charts (`aihub-common`, `aihub-tenant`) for
    **namespace-per-tenant multi-tenancy** and horizontal scale-out. Both charts declare `appVersion: "0.1.0"` and pull
    images via `${CORE_VERSION:-latest}` — the chart does **not** pin a specific aihub-core version; the deployed core
    version is whatever `CORE_VERSION` is set to at apply time. Tenants `tenant1`, `jointcreate`, `postgres-test` are
    present as test/sample only - no production customer migrated yet.

The document structure is extensible for additional customer projects.

**Document objectives**:

1. **Assess the current high-level architecture** against production standards for enterprise / multi-customer
   (10-pillar framework, [WAF](https://learn.microsoft.com/en-us/azure/well-architected/),
   [STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats),
   [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/), [CNCF maturity](https://maturitymodel.cncf.io/),
   [GDPR](https://gdpr-info.eu/) and [revDSG](https://www.fedlex.admin.ch/eli/cc/2022/491/de)). Full references at the
   end of the document.
2. **List the concerns** that are blocking or slowing production readiness, with a clear `What → How → Direction` per
   concern.
3. **Propose high-level recommendations** so the team can plan an improvement roadmap.

**What this document does NOT do**:

- Does not prescribe implementation details (deep-dives belong in dedicated ADRs and planning sessions).
- Is not a gate / final NO-GO verdict - it is **input** for roadmap decisions on improvement priorities.
- Does not cover detailed code review or specific performance benchmarks.

## Component versions

_Snapshot as of 2026-05-28._

| Component                   | Version                                                                                                                | Note                                                                                                                                                                                                              |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| aihub-core (HEAD on `main`) | v0.290.4                                                                                                               | Application stack - Latest dev (`pyproject.toml:3`); 47 ADRs under `docs/arc42/decisions/`                                                                                                                        |
| aihub-b\*d using core       | v0.279.2                                                                                                               | Customer Gen 1 - Azure VM + shell scripts, 11 minors behind core                                                                                                                                                  |
| aihub-c\*c using core       | v0.274.3                                                                                                               | Customer Gen 1 - Azure VM + shell scripts, 16 minors behind core, 5 behind b\*d                                                                                                                                   |
| aihub-Ig\*s                 | core images `:latest` (unpinned)                                                                                       | Customer **Gen 2 pilot** (pre-production) - Ansible Pull + Infomaniak OpenStack; deploy-only (stock core images); core-aligned stack (FerretDB + Valkey + Docling); internal infosec-directive RAG ("IGS Guisan") |
| aihub-W\*P                  | v0.255.6                                                                                                               | Customer Gen 1 - manual VM (docker-compose copy-paste), 35 minors behind core                                                                                                                                     |
| aihub-Dem\*scope            | v0.246.4 [^1]                                                                                                          | Customer Gen 1 - Azure VM (Pulumi per README; IaC code not in repo), 44 behind                                                                                                                                    |
| aihub-F\*H                  | v0.186.0                                                                                                               | Customer Gen 1 - Azure VM (Pulumi committed in `.iac/iac_azure/`), 104 behind                                                                                                                                     |
| aihub-Balmer-E\*            | TBD                                                                                                                    | Customer - version + deployment gen details pending                                                                                                                                                               |
| aihub-playbook              | HEAD on `main`                                                                                                         | Infra Gen 2 - Ansible Pull (every 15 min), 3-repo coordination; **7 roles** (`docker_runtime`, `traefik_proxy`, `signoz`, `aihub_application`, `os_backups`, `custom_vars_sync`, `restore_os_backup`)             |
| aihub-ops                   | HEAD on `main`                                                                                                         | VM provisioning automation (OpenStack Infomaniak)                                                                                                                                                                 |
| aihub-\{customer_id}        | per-customer                                                                                                           | Encrypted Ansible Vault + custom config (template repo pattern)                                                                                                                                                   |
| aihub-k8s                   | HEAD on `main` (Helm chart `appVersion 0.1.0`; images via `${CORE_VERSION:-latest}` — chart does NOT pin core version) | Infra Gen 3 - Terraform (Azure AKS + Stoney OpenStack Magnum) + Helm (`aihub-common` + `aihub-tenant`); namespace-per-tenant; deployed core version is whatever operator sets at apply time                       |

Warnings:

- All five Gen 1 customers (B*D/C*C/W*P/Dem*scope/F*H) run different SDK versions, all older than core. No policy
  enforces upgrades. Drift spread: 11 → 104 minor versions (F*H at v0.186.0 is the largest drift, 104 minors behind).
- Security patches on `main` do not propagate automatically to Gen 1 customers; Gen 2 (Ansible Pull) auto-deploys within
  15 min.
- Gen 1 → Gen 2 migration path (Azure manual → Infomaniak OpenStack + Ansible) is not yet documented for any of B*D /
  C*C / W*P / Dem*scope / F\*H.
- **Gen 3 (`aihub-k8s`) partially closes the "No K8s migration path" gap** raised in §3.1 Item #20 of this review: Helm
  charts, Terraform for two cloud providers (Azure AKS + Stoney OpenStack Magnum), CloudNativePG + Keycloak Operator +
  cert-manager + NGINX Ingress are committed. **However**: no production customer is yet on this path (only `tenant1`,
  `jointcreate`, `postgres-test` test tenants exist); Stoney Magnum has a documented limitation that `node_count` is not
  updatable after cluster creation; Milvus runs standalone by default (scale-out cluster mode is documented but
  optional); the Keycloak Operator cross-namespace-watch trick is called out as a "community workaround, not a
  first-class Keycloak support statement"; **and the charts do not pin a specific aihub-core version** — they pull
  whatever image tag `CORE_VERSION` evaluates to (see `adr_040`).

______________________________________________________________________

## Table of Contents

1. [Summary](#1-summary)
2. [Ecosystem Diagram](#2-ecosystem-diagram)
3. [Priority items for go-live (CRITICAL + HIGH)](#3-priority-items-for-go-live-critical--high) 3.1.
   [aihub-core (Platform)](#31-aihub-core-platform) 3.2. [aihub-b\*d](#32-aihub-bd) 3.3. [aihub-c\*c](#33-aihub-cc) 3.4.
   [aihub-Dem\*scope](#34-aihub-demscope) 3.5. [aihub-W\*P](#35-aihub-wp) 3.6. [aihub-F\*H](#36-aihub-fh) 3.7.
   [aihub-Ig\*s](#37-aihub-igs)
4. [Assessment](#4-assessment) 4.1. [By 10-pillar framework](#41-by-10-pillar-framework) 4.2.
   [Business core values vs reality](#42-business-core-values-vs-reality)
5. [Concerns and Documentation Backlog](#5-concerns-and-documentation-backlog)
6. [Recommendations](#6-recommendations)

______________________________________________________________________

## 1. Summary

**Purpose of this section**: give stakeholders a fast overview of platform strengths and weaknesses before diving into
§3-§6.

| Strengths                                                                                                                                                                                                                                                                           | Weaknesses                                                                                                                                                                                                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event-driven architecture (NATS JetStream and Swiss AI Agent Protocol)                                                                                                                                                                                                              | Sovereignty violation across customers - B*D Azure Sweden, C*C Azure Foundry SUI+SWE, F*H Azure SUI + Azure AI Search; W*P region unverified (env-var only); Dem*scope partial (Azure SUI + local vLLM). Only Dem*scope shows any sovereign-LLM intent                                   |
| 47 ADRs documenting major decisions (under `docs/arc42/decisions/`)                                                                                                                                                                                                                 | Gen 1 customer backup on the same VM (violates [3-2-1 rule](https://www.cisa.gov/news-events/news/data-backup-options)); Gen 2 partial fix via Restic→Swift                                                                                                                              |
| OpenTelemetry observability stack (cross-service traces)                                                                                                                                                                                                                            | No HA architecture - every stateful service is single-instance (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd)                                                                                                                                                                             |
| Agent framework supports common enterprise AI patterns (conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution sandbox, browser automation)                                                                  | AI use case scope not documented in an ADR, coverage claim not defensible for audit; vision / predictive analytics / fine-tuning out of scope but not explicit                                                                                                                           |
| Full CI/CD (lint, semantic-pr, per-package build)                                                                                                                                                                                                                                   | UsageLimits partially wired (agent endpoints + OpenAI route) but no 4-layer enforcement, no pre-flight estimation, no hard cap → LLM cost runaway risk                                                                                                                                   |
| Hierarchical permission template with AccessChecker tenant-ceiling (BDD tested)                                                                                                                                                                                                     | AuditLogEntity missing, GDPR right-to-erasure unimplementable, false docs claims                                                                                                                                                                                                         |
| LiteLLM gateway abstracts the LLM provider (easy to swap)                                                                                                                                                                                                                           | Customer SDK drift across **5 production customers**: B*D 11, C*C 16, W*P 35, Dem*scope 44, F\*H 104 minors behind core - no versioning policy or CI gate                                                                                                                                |
| Dagster pipeline orchestration with asset lineage                                                                                                                                                                                                                                   | No customer-facing SLA, no alerting infra; only Slack notification on Ansible Pull failure                                                                                                                                                                                               |
| License compliance OK (402 Python + 993 npm + 33 Docker images approved)                                                                                                                                                                                                            | Single-server ceiling for Gen 1 / Gen 2 (Docker Compose only) - partially mitigated by emerging **Gen 3 `aihub-k8s`** (Helm + Terraform, namespace-per-tenant), but no prod customer migrated yet                                                                                        |
| 47 ADRs and existing arc42 chapters for the platform                                                                                                                                                                                                                                | Customer docs gap - **none of B*D / C*C / W*P / Dem*scope / F\*H have own arc42 or ADRs** (5 customers, 0 docs)                                                                                                                                                                          |
| Hierarchical scoping protocol (Thread → Display → Run)                                                                                                                                                                                                                              | Missing connector framework - every customer rebuilds (O(N×M) onboarding cost)                                                                                                                                                                                                           |
| Multi-language i18n for the UI (DE/EN/FR/IT)                                                                                                                                                                                                                                        | Presidio is DE-only, multilingual PII gap for Swiss FR/IT/EN                                                                                                                                                                                                                             |
| **Gen 2 deployment: Ansible Pull self-configuring VMs (15-min auto-reconcile)**                                                                                                                                                                                                     | **All 5 customers still Gen 1** (Azure manual or copy-paste VM) - no migration plan to Gen 2 or Gen 3 (`aihub-k8s`) for any customer                                                                                                                                                     |
| **Infomaniak OpenStack - Swiss-sovereign cloud for Gen 2**                                                                                                                                                                                                                          | Restic → Swift uses same provider Infomaniak; no cross-provider replication                                                                                                                                                                                                              |
| **3-repo coordination pattern (playbook/core/customer) - separation of concerns**                                                                                                                                                                                                   | 3-repo version compatibility has no matrix / CI gate testing combos                                                                                                                                                                                                                      |
| **Customer onboarding template (`setup-aihub.sh`)** automated VM provisioning                                                                                                                                                                                                       | Ansible Pull 15-min cadence too slow for hot-fix; GitHub dependency = deploy SPOF                                                                                                                                                                                                        |
| **Ansible Vault encrypted secrets + auto-gen random via vault-vars-routing.yml**                                                                                                                                                                                                    | Vault password stored on VM filesystem - VM compromise = full unlock                                                                                                                                                                                                                     |
| **Traefik + Let's Encrypt ACME** automated SSL cert lifecycle                                                                                                                                                                                                                       | Deploy key rotation policy implicit ("periodically"), no automation / audit                                                                                                                                                                                                              |
| **SigNoz OTEL collector role** (host metrics + OTLP traces + journald)                                                                                                                                                                                                              | SigNoz Cloud region "eu" - unclear data sovereignty implication                                                                                                                                                                                                                          |
| **Env vars drift detection CI** (`check_env_drift.py` nightly)                                                                                                                                                                                                                      | Drift check only for env vars, doesn't cover docs claims                                                                                                                                                                                                                                 |
| Langfuse cost tracking per LLM call                                                                                                                                                                                                                                                 | No per-tenant cost attribution → showback impossible                                                                                                                                                                                                                                     |
| Open-source self-hosted positioning                                                                                                                                                                                                                                                 | Open-source dependency lock-in (parser/embedding/reranker/vector store not abstracted)                                                                                                                                                                                                   |
| BDD test integration with real NATS                                                                                                                                                                                                                                                 | Test coverage across 5 customers: **ZERO in Dem*scope, W*P**; **C\*C has 3 files / 788 lines but only in `log_analysis_agent`** (other 3 agents + 6 pipelines + custom API + `lib/common` untested); 58 lines in B*D; 5 `test_*.py` + 5 BDD `.feature` in F*H                            |
| Trace context propagated via NATS message headers                                                                                                                                                                                                                                   | Bot scope lacks OTEL → trace breaks at the bot boundary                                                                                                                                                                                                                                  |
| Pulumi adopted as IaC framework (ADR `2024_12_18`) — superseded by Ansible Pull for Gen 2; **Gen 3 `aihub-k8s` adds Terraform + Helm + CloudNativePG + Keycloak Operator for AKS / Stoney Magnum**                                                                                  | K8s path is committed but unproven in production; Pulumi code still absent from `aihub-core`; no ADR yet adopts `aihub-k8s` as the official Gen 3 path; **Helm charts do NOT pin a core version** (`appVersion: "0.1.0"`, images via `${CORE_VERSION:-latest}`) — see proposed `adr_040` |
| **F\*H committed Pulumi IaC** (10 deploy units: agents / ai / api / bot / dagster / nats / network / openwebui / phoenix / stores) - best IaC of the 3 new customers                                                                                                                | **Dem\*scope claims Pulumi in README but `.iac/` code NOT committed** to repo; W\*P has no IaC at all (manual `cp docker-compose.latest.yml /opt/docker/config/bbv/`)                                                                                                                    |
| **`aihub-k8s` introduces real multi-tenancy** - namespace-per-tenant, realm-per-tenant (Keycloak), DB-per-tenant (CNPG), Milvus DB-per-tenant, bucket-prefix-per-tenant (SeaweedFS)                                                                                                 | F\*H **monkey-patches LlamaIndex** at import time (`lib/common/register_openai_models.py` modifies third-party globals to register GPT-5 names); behaviour depends on import order; drops on SDK upgrade                                                                                 |
| **`aihub-k8s` chart pulls via `${CORE_VERSION:-latest}`** — operators can match current core HEAD `v0.290.4` by setting that env at apply time (dramatically lower drift than Gen 1 if pinned to a recent version); no built-in chart-level pin policy yet (see proposed `adr_040`) | F\*H uses **Azure AI Search instead of Milvus** - vendor lock-in + double inference cost (AI Search query + LLM call); matches §3.3 C\*C "Azure stack triple redundancy" pattern (see proposed `adr_039`)                                                                                |
| Dem\*scope runs **local vLLM** (Gemma-3 12b/27b + gte-Qwen2 embedding + bge-reranker) - only customer with partial sovereign-LLM stack                                                                                                                                              | **W\*P TLS private key committed in git** (`wpe.ai-agents.ch+1-key.pem` tracked alongside the production-domain cert); only `.env` is in `.gitignore`                                                                                                                                    |
| F\*H has its own **evaluation framework** (`evaluation/` with own evaluators + testsets + Excel test catalogue)                                                                                                                                                                     | Stack divergence: Dem\*scope and F\*H still use **MongoDB + Redis + Phoenix v10.0.4** (pre-Langfuse ADR `2026_02_10`), divergent from core's FerretDB + Valkey + Langfuse                                                                                                                |
| Existing **C4 model** (`03_c4_diagrams.md`): L1 + 3×L2 + 4×L3 + 5 sequence diagrams + deployment + multi-customer topology covering Platform + B*D + C*C; per-customer C4 files for Platform / B*D / C*C / Dem*scope / W*P / F\*H now in `c4/`                                      | **C4 missing for Dem*scope / W*P / F\*H** previously (3 of 5 prod customers) — addressed by the new `c4/` per-customer folder in this review                                                                                                                                             |
| C\*C `log_analysis_agent` has its own test suite (3 files / 788 lines incl. integration + extract logs)                                                                                                                                                                             | C\*C deep-import violation: `agents/chat_agent/chat_agent/ChatAgent.py` reaches `swiss_ai_hub.core.generative_ai.{chat_history,guards}` and `swiss_ai_hub.core.i18n.locale_handler` (bypasses public API) — see proposed `adr_038`                                                       |

**Next steps**

1. §3 - priority CRITICAL + HIGH items for go-live (3 tables Core/B*D/C*C).
2. §4 - detailed 10-pillar assessment (table format) and business values vs reality.
3. §5 - every concern listed in `Concern → Direction` format (tactical) or trade-off block (strategic).
4. §6 - high-level recommendations grouped into Immediate / Strategic / Documentation / Process.
5. The team uses this document as input for the improvement roadmap.

______________________________________________________________________

## 2. Ecosystem Diagram

```mermaid
flowchart TB
    subgraph CORE["Swiss AI Hub Core (aihub-core v0.290.4)"]
        direction TB
        CorePkgs["packages/<br/>core • agent • api • pipeline<br/>bot • backup • web • process"]
        CoreADR["47 ADRs"]
        CoreInfra["30+ containers<br/>per deployment"]
    end

    subgraph B*D["aihub-b*d v0.279.2 (drift 11 minors)"]
        direction TB
        B*DAgents["Agents (3)<br/>b*d · expert_rag · expert_asking"]
        B*DPipes["Pipelines (4)<br/>customers × 2-stage<br/>suppliers × 2-stage"]
        B*DCfg["Configs (16 services)<br/>SMB path hardcoded<br/>SNK enrichment"]
        B*DExt["External: Azure OpenAI (Sweden)<br/>Cohere reranking<br/>SMB share"]
    end

    subgraph C*C["aihub-c*c v0.274.3 (drift 16 minors)"]
        direction TB
        C*CAgents["Agents (4)<br/>chat · jira · log<br/>retrieval_orchestrator"]
        C*CPipes["Pipelines (6)<br/>jira/confluence/sharepoint<br/>× 2-stage"]
        C*CAPI["Custom API<br/>Jira webhook<br/>Support Desk"]
        C*CLib["lib/common/<br/>events · types · ops"]
        C*CExt["External: Azure Foundry SUI+SWE<br/>Azure Doc Intelligence<br/>Azure AD B2C · Key Vault · VM<br/>Jira · Confluence · SharePoint"]
    end

    subgraph DEMOSCOPE["aihub-Dem*scope v0.246.4* (drift 44 minors, *SDK pin unverified)"]
        direction TB
        DemoAgents["Agents (2 pkg / 4 deployed)<br/>persona_agent · multi_personas_agent<br/>(each public + private variant)"]
        DemoPipes["Pipelines (1)<br/>personas (imputation + insertion jobs)"]
        DemoAPI["Custom API (mounts core controllers)"]
        DemoLib["lib/common/<br/>events · ops · schemas · persistence"]
        DemoExt["External: Azure OpenAI SUI<br/>+ local vLLM (Gemma-3 12b/27b)<br/>+ gte-Qwen2 embed · bge-rerank<br/>Azure AD · MongoDB · Milvus"]
    end

    subgraph WPE["aihub-W*P v0.255.6 (drift 35 minors)"]
        direction TB
        WPEDeploy["Deployment only<br/>(no custom agents / pipelines / API)<br/>uses core llm_wrapping_agent + rag_agent<br/>uses core default_rag_pipeline"]
        WPECfg["Configs: LiteLLM, Milvus, Postgres,<br/>SeaweedFS, OTEL→SigNoz<br/>manual VM deploy (docker-compose copy)"]
        WPEExt["External: Azure OpenAI (region via env)<br/>Azure AD / Entra (Microsoft v2.0)"]
    end

    subgraph FMH["aihub-F*H v0.186.0 (drift 104 minors)"]
        direction TB
        FMHAgents["Agents (3)<br/>handbook_agent · rules_agent · routing_agent"]
        FMHPipes["Pipelines (2)<br/>handbook_ingestion · position_ingestion<br/>(TARDOC / TARMED data)"]
        FMHAPI["Custom API + Bot (MS Bot Framework)"]
        FMHEval["evaluation/ framework<br/>own evaluators · testsets"]
        FMHExt["External: Azure OpenAI SUI<br/>(`*-openai-sui`) + Azure AI Search<br/>(NOT Milvus) · Azure Data Lake<br/>Azure AD · TARDOC/TARMED"]
    end

    IGS["aihub-Ig*s (Gen 2 pilot · pre-prod)<br/>deploy-only · core images @ :latest<br/>FerretDB · Valkey · Docling · Milvus<br/>core agents + bot · eval via Langfuse<br/>internal infosec-directive RAG (DE)<br/>LLM: Azure OpenAI + Swiss LLM Cloud"]
    Future["Other customers (TBD info):<br/>Balmer-E*<br/>(deployment gen + components pending)"]

    subgraph INFRA["Infrastructure Repos (Gen 2)"]
        direction TB
        Playbook["aihub-playbook<br/>Ansible Pull (every 15min)<br/>7 roles: docker_runtime · traefik_proxy<br/>signoz · aihub_application<br/>os_backups (Restic→Swift) · custom_vars_sync<br/>restore_os_backup"]
        Ops["aihub-ops<br/>OpenStack VM provisioning<br/>setup-aihub.sh · cloud-init<br/>vault-vars-routing.yml<br/>nightly drift check"]
        CustomerRepo["aihub-{customer_id}<br/>Ansible Vault (encrypted)<br/>Custom config + secrets"]
    end

    subgraph K8S["aihub-k8s (Gen 3, emerging) — chart appVersion 0.1.0; pulls via ${CORE_VERSION:-latest}"]
        direction TB
        K8STerraform["Terraform<br/>Azure AKS (Switzerland North, OIDC + workload identity)<br/>+ Stoney OpenStack Magnum (Flannel, Cinder, floating IP)<br/>one `deploy.sh` for both clouds"]
        K8SCommon["Helm chart: `aihub-common`<br/>CloudNativePG (PostgreSQL 17 + pgvector)<br/>Keycloak Operator (1 instance, **realm per tenant**)<br/>SeaweedFS (shared, **bucket prefix per tenant**)<br/>Milvus (standalone; **DB per tenant**; scale-out optional)<br/>FerretDB · Langfuse · LiteLLM · MinerU · SearXNG"]
        K8STenant["Helm chart: `aihub-tenant`<br/>**namespace `tenant-<name>`** · subdomain `<name>.k8s.ai-agents.ch`<br/>~27 services (api · web · openwebui · dagster · bot ·<br/>NATS · Redis · Neo4j · Phoenix · Jupyter · Playwright ·<br/>Presidio · rclone · 9 agents · 2 RAG pipelines)<br/>NGINX Ingress + cert-manager (Let's Encrypt)"]
        K8STenants["Test tenants only (no prod customer yet):<br/>tenant1 · jointcreate · postgres-test"]
    end

    CORE -.->|git tag<br/>v0.279.2| B*D
    CORE -.->|git tag<br/>v0.274.3| C*C
    CORE -.->|git tag<br/>v0.246.4| DEMOSCOPE
    CORE -.->|git tag<br/>v0.255.6| WPE
    CORE -.->|git tag<br/>v0.186.0| FMH
    CORE -.->|image pull<br/>:latest (unpinned)| IGS
    CORE -.->|git tag<br/>vX.Y.Z| Future
    CORE -.->|image pull via<br/>${CORE_VERSION}| K8S

    Playbook -->|pulls every 15min| IGS
    Ops -.->|provisions VM| IGS
    CustomerRepo -.->|vault secrets| IGS
    Playbook -.->|future| Future

    style CORE fill:#e8f0ff
    style B*D fill:#fff4e8
    style C*C fill:#fff4e8
    style DEMOSCOPE fill:#fff4e8
    style WPE fill:#fff4e8
    style FMH fill:#fff4e8
    style IGS fill:#fff4e8,stroke:#3da35a,stroke-width:2px
    style Future stroke-dasharray: 5 5,stroke:#888,fill:#f5f5f5
    style INFRA fill:#e8ffe8
    style K8S fill:#f0e8ff
```

**Customer Registry** (extend when new customers join)

Components format: `A` = agents, `P` = pipelines, `API` = custom API. Drift = number of minor versions behind core
latest. Sovereignty annotation inline in LLM Provider. **Deployment Gen**: Gen 1 = Azure VM + shell scripts (manual);
Gen 2 = OpenStack Infomaniak + Ansible Pull (aihub-playbook/aihub-ops).

| Customer              | Status                          | Core ver (drift)                 | Components                         | Deployment Gen                                                         | Data sources                                                                                | LLM Provider                                                                                                         | Identity                                        |          Off-site Backup          | Own arc42 + ADRs  | Test coverage                                              |
| --------------------- | ------------------------------- | -------------------------------- | ---------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | :-------------------------------: | :---------------: | ---------------------------------------------------------- |
| aihub-b\*d            | Production 4/2026               | v0.279.2 (11 behind)             | 3A / 4P / -                        | **Gen 1** - On-prem (SMB share)                                        | SMB share (customer + supplier docs)                                                        | Azure OpenAI Sweden - **sovereignty violated**                                                                       | Keycloak SaaS                                   |           No (same VM)            |        No         | Minimal (58 lines / 1 util)                                |
| aihub-c\*c            | Production                      | v0.274.3 (16 behind)             | 4A / 6P / 1 API                    | **Gen 1** - Azure VM (SUI+SWE)                                         | Jira / Confluence / SharePoint                                                              | Azure AI Foundry SUI+SWE - **sovereignty violated**                                                                  | Keycloak + Azure AD B2C                         |           No (same VM)            |        No         | Minimal (3 files / 788 lines in `log_analysis_agent` only) |
| aihub-Ig\*s           | **Pilot / pre-production**      | core images `:latest` (unpinned) | - (deploy-only; core agents + bot) | **Gen 2** - Infomaniak OpenStack + Ansible Pull (first Gen 2 customer) | Internal infosec / data-protection directives (ICT-Sicherheitsweisung, KI-Weisung) - German | Azure OpenAI + Swiss LLM Cloud (both wired; routing not in repo) - **partial / unverified**                          | Azure AD / Entra ID (OIDC)                      | Via Gen 2 Restic → Swift (verify) | No (empty README) | None (eval harness only - Langfuse `Citation Quality`)     |
| aihub-W\*P            | Production                      | v0.255.6 (35 behind)             | - (deploy only)                    | **Gen 1** - manual VM (docker-compose copy-paste)                      | OpenWebUI knowledge / RAG (Milvus + SeaweedFS, user-uploaded)                               | Azure OpenAI (region not in repo - configured via env var) - **sovereignty unverified**                              | Azure AD / Entra ID (Microsoft v2.0)            |         No (none in repo)         |        No         | N/A (no custom code)                                       |
| aihub-Dem\*scope      | Production                      | v0.246.4 (44 behind)[^1]         | 2A / 1P / 1 API                    | **Gen 1** - Azure VM (Pulumi per README; IaC code not in repo)         | MongoDB persona data + Milvus (questions, personas)                                         | Azure OpenAI Switzerland + local vLLM (Gemma-3-12b/27b, gte-Qwen2 embedding, bge-reranker) - **partial sovereignty** | Azure AD / Entra ID (login.microsoftonline.com) |        No (MinIO same VM)         |        No         | Zero (no test files)                                       |
| aihub-F\*H            | Production (last commit 4/2026) | v0.186.0 (104 behind)            | 3A / 2P / 1 API / 1 bot            | **Gen 1** - Azure (Pulumi committed: 10 deploy units)                  | Azure Data Lake Storage (TARDOC / TARMED: handbook + positions)                             | Azure OpenAI Switzerland North (`*-openai-sui`) + Azure AI Search (not Milvus) - **sovereignty Switzerland**         | Azure AD (AUTH_AZURE_AD\_\*)                    |         No (none in repo)         |        No         | Minimal (5 tests + 5 BDD)                                  |
| aihub-Balmer-E\*      | TBD                             | TBD                              | TBD                                | TBD                                                                    | TBD                                                                                         | TBD                                                                                                                  |                                                 |                                   |                   |                                                            |
| Customer #N+ (future) | Template ready                  | TBD                              | TBD                                | **Gen 2** - OpenStack Infomaniak (Swiss) + Ansible Pull                | TBD                                                                                         | TBD                                                                                                                  | TBD                                             |  Restic → Swift (partial 3-2-1)   | TBD via template  | TBD                                                        |

______________________________________________________________________

## 3. Priority items for go-live (CRITICAL + HIGH)

This section highlights items to prioritize for go-live preparation, grouped by scope (Core / B*D / C*C / Dem*scope /
W*P / F*H / Ig*s). Severity:

- **CRITICAL**: blocks go-live; causes data loss / security breach / compliance violation / fatal scenario if not
  addressed
- **HIGH**: significant impact on scale, reliability, or compliance; should be addressed before expanding the customer
  base

**Severity note**: Severity assumes the scenario "new customer onboarding with mid-to-high compliance requirement"
(Swiss enterprise / regulated industry such as banking, healthcare, gov). For other scenarios (e.g., internal-only
customer with low regulation, or shared multi-tenant SaaS), review severity individually; many items may downgrade or
upgrade depending on context.

Use this list as input for the team to prioritize go-live roadmap tasks. Full technical details in §4 Assessment and §5
Concerns. MEDIUM-severity items (business / scoping / nice-to-have) are tracked in §6 Recommendations instead of this
list.

### 3.1. aihub-core (Platform)

| #   | Item                                                                                                                                                                                                                                                                                                                                                                                           |   Severity   | Recommendation actions                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Sovereignty path not yet decided                                                                                                                                                                                                                                                                                                                                                               | **CRITICAL** | Choose Option A (self-hosted local LLM) / B (hybrid with updated ADR allowing Azure-EU) / C (per-customer sovereignty tier); update ADR `2026_02_24`                                                                                                                                                                                                                                                                                                                                          |
| 2   | UsageLimits enforcement incomplete (wired at agent endpoints + OpenAI route, missing 4-layer + hard cap)                                                                                                                                                                                                                                                                                       | **CRITICAL** | Extend to 4-layer enforcement (per-user/tenant/model/global) across all routes; pre-flight cost estimation; hard cap with circuit breaker (see `adr_012`)                                                                                                                                                                                                                                                                                                                                     |
| 3   | Multi-tenant data layer not isolated                                                                                                                                                                                                                                                                                                                                                           | **CRITICAL** | Add required `tenant_id` field; per-tenant Milvus collection; NATS subject namespace `aihub.tenant.{id}.*`; Valkey key prefix; auto-filter repository wrapper                                                                                                                                                                                                                                                                                                                                 |
| 4   | Document ACL not inherited into Milvus                                                                                                                                                                                                                                                                                                                                                         | **CRITICAL** | ACL metadata field in Milvus + retrieval-time filter by `user_groups` (see `adr_020`)                                                                                                                                                                                                                                                                                                                                                                                                         |
| 5   | MCP tool args bypass Presidio                                                                                                                                                                                                                                                                                                                                                                  | **CRITICAL** | Implement `SecureMCPExecutor` with Presidio sanitization + tool authorization (see `adr_019`)                                                                                                                                                                                                                                                                                                                                                                                                 |
| 6   | `AuditLogEntity` missing                                                                                                                                                                                                                                                                                                                                                                       | **CRITICAL** | Write-once entity with retention policy + tamper-evident hash chain (see `adr_011`); fixes GDPR Art. 30 / ISO 27001 A.12.4 / SOC2 violation                                                                                                                                                                                                                                                                                                                                                   |
| 7   | GDPR right-to-erasure unimplementable                                                                                                                                                                                                                                                                                                                                                          | **CRITICAL** | Implement cascade DELETE endpoint for user/tenant across Mongo/Milvus/Neo4j/Valkey/SeaweedFS; document compliance procedure                                                                                                                                                                                                                                                                                                                                                                   |
| 8   | No DLQ for JetStream poison messages                                                                                                                                                                                                                                                                                                                                                           | **CRITICAL** | DLQ subject `aihub.dlq.*` with max-retry policy + alerting; avoid consumer crash loop blocking downstream                                                                                                                                                                                                                                                                                                                                                                                     |
| 9   | No circuit breaker for external deps                                                                                                                                                                                                                                                                                                                                                           | **CRITICAL** | `pybreaker` per LiteLLM/Keycloak/Milvus with threshold + half-open recovery; avoid outage cascade across the platform                                                                                                                                                                                                                                                                                                                                                                         |
| 10  | No HA architecture (every stateful service single instance)                                                                                                                                                                                                                                                                                                                                    |     HIGH     | HA roadmap per service: Postgres streaming replication, NATS 3-node cluster, Valkey Sentinel, Milvus cluster mode, Keycloak Infinispan, etcd 3-node                                                                                                                                                                                                                                                                                                                                           |
| 11  | No DB migration framework                                                                                                                                                                                                                                                                                                                                                                      |     HIGH     | Versioned migration framework (Alembic-like) + metadata collection tracking applied migrations                                                                                                                                                                                                                                                                                                                                                                                                |
| 12  | False docs claims (Presidio, GDPR right-to-erasure, audit immutable)                                                                                                                                                                                                                                                                                                                           |     HIGH     | Remove false claims from CLAUDE.md + GDPR docs; sync with reality; add doc-code drift detection CI                                                                                                                                                                                                                                                                                                                                                                                            |
| 13  | Presidio DE-only multilingual gap                                                                                                                                                                                                                                                                                                                                                              |     HIGH     | Per-language Presidio routing (DE/FR/IT/EN) + Swiss custom recognizers (AHV, CHE-UID, +41 phone)                                                                                                                                                                                                                                                                                                                                                                                              |
| 14  | No mTLS service-to-service                                                                                                                                                                                                                                                                                                                                                                     |     HIGH     | mTLS for NATS/Mongo/Redis with automated cert rotation (cert-manager / Vault)                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 15  | No supply chain security (SBOM/signing/scan)                                                                                                                                                                                                                                                                                                                                                   |     HIGH     | syft/CycloneDX (SBOM) + cosign (image signing) + trivy (vuln scan) in CI. Verified: today only Dependabot exists — no SBOM/signing/scan. Process side (SAST/DAST/CVSS) in #34 / proposed `adr_052`                                                                                                                                                                                                                                                                                            |
| 16  | No API rate limiting                                                                                                                                                                                                                                                                                                                                                                           |     HIGH     | Redis-backed rate limiter middleware per user + per tenant                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 17  | Milvus single-node memory wall (122 GB for 10M × 3072d)                                                                                                                                                                                                                                                                                                                                        |     HIGH     | Milvus cluster mode + DISKANN benchmark for disk-backed index                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 18  | No formal alerting infrastructure                                                                                                                                                                                                                                                                                                                                                              |     HIGH     | **Partially mitigated**: OTLP→SigNoz Cloud pipeline wired, but **no alert rules as-code, no AlertManager/on-call routing in repo**; SigNoz is an external Cloud (EU) sink, not self-hosted in core. Still need: alert rules as-code + PagerDuty/OpsGenie on-call + per-service severity rules (see proposed `adr_050`, `adr_032`)                                                                                                                                                             |
| 19  | No business metrics + formal SLI/SLO                                                                                                                                                                                                                                                                                                                                                           |     HIGH     | **Partially mitigated**: collector has traces/logs/metrics pipelines, but **core (API/agents/pipelines/dispatcher) emits NO metrics** (no `MeterProvider` in `packages/core`; only OpenWebUI/LiteLLM self-emit); **bot has no OTEL** (trace breaks at bot); host metrics/journald only via Gen 2 playbook (absent on all 5 Gen 1 customers). Still need: business metrics export (agent_runs, HITL escalations, RAG latency) + bot OTEL + formal SLI/SLO per service (see proposed `adr_050`) |
| 20  | No K8s migration path **(partially addressed: `aihub-k8s` Gen 3 exists)**                                                                                                                                                                                                                                                                                                                      |     HIGH     | `aihub-k8s` already provides Terraform (AKS + Stoney Magnum) + Helm (`aihub-common` + `aihub-tenant`). Charts declare `appVersion: "0.1.0"` and pull images via `${CORE_VERSION:-latest}` — no chart-level pin yet (see proposed `adr_040`). Remaining: ADR adopting Gen 3 as official path; chart-level core version pin policy; migrate ≥ 1 prod customer; cluster-mode Milvus + HPA validation; document Gen 1 → Gen 3 migration                                                           |
| 21  | No load test baseline                                                                                                                                                                                                                                                                                                                                                                          |     HIGH     | Load test suite (k6/Locust) in CI with baseline numbers per critical path                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 22  | Connector framework missing                                                                                                                                                                                                                                                                                                                                                                    |     HIGH     | `BaseSourceConnector` framework + 12 built-in connectors (SMB, S3, SharePoint, Confluence, Jira, GitHub, Notion, Drive, Box, Salesforce, IMAP)                                                                                                                                                                                                                                                                                                                                                |
| 23  | Code RAG semantic-only (missing structural chunks)                                                                                                                                                                                                                                                                                                                                             |     HIGH     | tree-sitter AST chunking + code-specific embedding (CodeBERT/UniXcoder) + hybrid index (vector + symbol + Neo4j call-graph)                                                                                                                                                                                                                                                                                                                                                                   |
| 24  | OSS dependency churn, EOL & lock-in (fast-moving AI stack) — heavy dependence on many external libs/systems; as volume grows, security/maintenance/**End-of-Life** topics surface; even OSS can lock-in (proprietary functions, protocols)                                                                                                                                                     |     HIGH     | Hexagonal Ports & Adapters for the 6 swappable layers + contract tests; **plus** Renovate auto-updates + **EoL tracking** + **continuous component-health monitoring** (manual or automated) + eval gate on swaps (see proposed `adr_043`, `adr_024`)                                                                                                                                                                                                                                         |
| 25  | Workflow architecture Process vs Agentic undecided                                                                                                                                                                                                                                                                                                                                             |     HIGH     | Strategic decision: Option A (activate hybrid Process+Agentic with routing criteria) or Option B (deprecate process cleanly + migration guide); the **marketing architecture diagram (.drawio) also depicts the process engine** — remove or align with the decision                                                                                                                                                                                                                          |
| 26  | No run / AITL timeout                                                                                                                                                                                                                                                                                                                                                                          |     HIGH     | Explicit timeout per agent run + `MAX_AITL_DEPTH = 5` hardcap for recursive escalation                                                                                                                                                                                                                                                                                                                                                                                                        |
| 27  | Container resource limits in production                                                                                                                                                                                                                                                                                                                                                        |     HIGH     | Explicit `deploy.resources.limits` (CPU/memory) per service in docker-compose; profile-based sizing; avoid 1 container OOM = host crash                                                                                                                                                                                                                                                                                                                                                       |
| 28  | Backup encryption at rest not verified                                                                                                                                                                                                                                                                                                                                                         |     HIGH     | Verify Restic encryption is enabled for off-host backup; document encryption key management; key rotation procedure                                                                                                                                                                                                                                                                                                                                                                           |
| 29  | Keycloak signing key rotation procedure missing                                                                                                                                                                                                                                                                                                                                                |     HIGH     | Document JWT signing key rotation (every 6 months); automation script; audit log; avoid compromised key = unlimited token forgery                                                                                                                                                                                                                                                                                                                                                             |
| 30  | Image vulnerability remediation SLA missing                                                                                                                                                                                                                                                                                                                                                    |     HIGH     | SLA for critical CVE (7 days), high (30 days), medium (90 days); track in dashboard; separate from supply chain detection (scanning)                                                                                                                                                                                                                                                                                                                                                          |
| 31  | Marketing architecture diagram advertises **Meltano** — not present in the codebase (`docs/media/architecture/architecture.drawio` has `meltano` nodes; pipelines are actually Dagster + rclone/SharePoint connectors; the review itself cites Meltano only as a *competitor* in #22)                                                                                                          |     HIGH     | Remove Meltano from the marketing diagram or add it as a real roadmap item; extend doc-code drift detection to marketing diagrams (false-claim family, ties #12 and #22)                                                                                                                                                                                                                                                                                                                      |
| 32  | **No accuracy/quality evaluation & performance benchmark process** (platform-wide) — quality issues surface only as customer complaints                                                                                                                                                                                                                                                        |     HIGH     | Standing eval methodology (golden datasets + LLM-as-judge metrics in CI) + performance-benchmark gate per release; promote IGS `Citation Quality` + F\*H eval framework to a core capability. **Root NFR behind §3.6 #12 (F\*H) and §3.5 #11 (W\*P)** (see proposed `adr_051`, `adr_044`, `adr_046`)                                                                                                                                                                                          |
| 33  | **Supported use cases not authoritatively documented** — no canonical "is X supported?" answer for sales/audit                                                                                                                                                                                                                                                                                 |     HIGH     | Authoritative ADR with a Full/Partial/Out-of-scope matrix; reference from marketing + pre-sales. Already raised in §1 Weaknesses / §5 "AI use case scope undefined" (see proposed `adr_037`)                                                                                                                                                                                                                                                                                                  |
| 34  | **No recurring security testing / DevSecOps process** — verified: only Dependabot in CI; no SAST/DAST, no OWASP dependency-check, no CVSS triage, no periodic pentest, threat model (§17) has no refresh cadence                                                                                                                                                                               |     HIGH     | DevSecOps process: SAST (CodeQL/semgrep/bandit) + DAST (OWASP ZAP) in CI; OWASP Dependency-Check + pip-audit/trivy; CVSS-based triage feeding the #30 SLA; scheduled threat-model refresh + periodic pentest; CycloneDX SBOM (closes #15) (see proposed `adr_052`)                                                                                                                                                                                                                            |
| 35  | **No defined quality attributes / NFR scenarios to drive architecture** — decisions made functionally; non-functional targets reconstructed after the fact                                                                                                                                                                                                                                     |     HIGH     | Author arc42 ch10 quality scenarios as **architecture gates**; sequence tenant-isolation (`adr_002`) + DB migration framework (`adr_003`) **early**. Concretely: multi-tenancy was deferred (#3 not isolated) → late retrofit forces tenant **data migration** with large customer impact (C\*C §3.3 #18). NFRs must drive architecture, not follow it (see proposed `adr_053`)                                                                                                               |
| 36  | **Insecure code execution (Jupyter)** — user-supplied Python runs in a **shared** jupyter-lab on the `backend` network (token auth, shared workspace); verified no `cap_drop`/`read_only`/`security_opt`/`pids_limit`/resource limits, no per-user isolation; reaches backend peers (LiteLLM holds LLM keys). "Code execution **sandbox**" is advertised but hardening is container-level only |     HIGH     | Ephemeral per-session sandbox (gVisor/Kata or nsjail) + drop caps + read-only FS + no-new-privileges + cpu/mem/pids quotas + dedicated locked-down network (no backend reach, no egress) + per-user workspace; correct the "sandbox" claim (see proposed `adr_054`, ties #12)                                                                                                                                                                                                                 |
| 37  | **Agent permissions / bus access not scoped** — NATS uses a single shared token with **no subject-level ACL** → any agent/bot/service can pub/sub `agent.>` / `process.>` across all tenants & threads (confirms §4.0 V3); agents hold broad DB/S3 creds; no per-agent least-privilege; no per-tenant tool auth (§13.2)                                                                        |     HIGH     | NATS per-account/user permissions scoped by subject incl. tenant segment (`aihub.tenant.{id}.*`); least-privilege creds per agent; per-tenant tool authorization (see `adr_002`, `adr_047`)                                                                                                                                                                                                                                                                                                   |
| 38  | **Event bus (NATS/JetStream) not monitored** — the `http: 8222` monitoring endpoint exists but is **not scraped**; no prometheus-nats-exporter, no JetStream metrics (consumer lag, redelivery, stream bytes), no alerts → poison messages (#8) / stuck consumers are invisible                                                                                                                |     HIGH     | Scrape 8222/JetStream metrics into SigNoz (prometheus-nats-exporter or OTLP); alert on consumer lag, redelivery, DLQ depth, stream storage; dashboards (folds into `adr_050` + #8)                                                                                                                                                                                                                                                                                                            |

### 3.2. aihub-b\*d

| #   | Item                                                            |   Severity   | Recommendation actions                                                                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------- | :----------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Backup destination on the same VM (FATAL: VM dies = total loss) | **CRITICAL** | Emergency cron sync to Swiss-sovereign off-site (Infomaniak CH / Exoscale CH / Hetzner); long-term migrate to Gen 2 (Restic→Swift)                                                                                                                                      |
| 2   | Azure OpenAI (Sweden) sovereignty violation                     |     HIGH     | Tied to Core sovereignty path decision (Option A/B/C); ADR documenting trade-off or migration plan. Severity depends on customer compliance contract                                                                                                                    |
| 3   | Test coverage near-zero (59 lines / 1 utility)                  |     HIGH     | Baseline test plan (smoke tests per agent / pipeline); integration test with staging data; coverage threshold 60% for new code                                                                                                                                          |
| 4   | SDK drift 11 minor versions (v0.279.2 vs v0.290.4)              |     HIGH     | SDK upgrade plan with security delta audit; extract reusable patterns (`resolve_selection`, HITL helpers) to core; CI gate blocking drift > N versions. **Near-latest pin — lowest-risk upgrade of all customers; do first as a quick win (bump straight to core tip)** |
| 5   | Cohere reranking US/Canada vendor                               |     HIGH     | ADR documenting sovereignty trade-off or migrate to sovereign alternative (local BGE, local Jina)                                                                                                                                                                       |
| 6   | Storage multiplier 3.9x (1.9 TB insufficient for 2+ customers)  |     HIGH     | Data partitioning strategy (sharding / time-based / customer-based / cold storage); ADR documenting strategy                                                                                                                                                            |
| 7   | Hardcoded customer config (SNK_ANCHOR, BASE_PATH SMB)           |     HIGH     | Pydantic Settings from env per deployment; documented config matrix                                                                                                                                                                                                     |
| 8   | Weak model malformed JSON breaks workflow                       |     HIGH     | Structured output / JSON mode (`response_format`) + Pydantic validation + fallback chain weak→strong model + golden test suite in CI                                                                                                                                    |
| 9   | No resource limits in docker-compose                            |     HIGH     | Explicit CPU/memory limits per service; profile-based sizing                                                                                                                                                                                                            |
| 10  | Internal import violation `pipelines/snk_enrichment.py:2`       |     HIGH     | Fix import via core public API (`__init__.py`); lint rule blocking internal imports                                                                                                                                                                                     |
| 11  | No own arc42 + ADRs                                             |     HIGH     | arc42 12 chapters skeleton + C4 L1/L2 + 10 ADRs answering design questions (sovereignty, partitioning, SMB path, SNK enrichment, regex utils, Cohere choice, etc.)                                                                                                      |

### 3.3. aihub-c\*c

| #   | Item                                                                                                                                                                                   |   Severity   | Recommendation actions                                                                                                                                                                                                                                                                                                                                                                                                                    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Backup destination on the same Azure VM (FATAL)                                                                                                                                        | **CRITICAL** | Tier 1 emergency cron sync to Swiss off-site; plan migration to Gen 2 with cross-region replication                                                                                                                                                                                                                                                                                                                                       |
| 2   | Azure AI Foundry + Azure DI sovereignty violation                                                                                                                                      | **CRITICAL** | Standardize on core stack (MinerU + LiteLLM gateway); migration roadmap DI → MinerU, Foundry → vLLM/Swiss LLM Cloud via LiteLLM                                                                                                                                                                                                                                                                                                           |
| 3   | Per-user data access control missing (3 manifestations, same root cause)                                                                                                               | **CRITICAL** | Holistic fix: (a) per-user OAuth delegated permissions for Jira/SharePoint/Confluence instead of service account shared keys; (b) move isolation down to the data layer (per-tenant Milvus collection, per-user ACL filter at retrieval query, pre-filter chunks before LLM context); (c) ACL inheritance into Milvus metadata + retrieval-time filter; (d) documented user access matrix; forensic audit log. GDPR Art. 32/25 compliance |
| 4   | Test coverage minimal — 3 files / 788 lines in `log_analysis_agent` only; chat / jira_issue / retrieval_orchestrator agents + 6 pipelines + custom API + `lib/common` untested         |     HIGH     | Extend `log_analysis_agent` style coverage to all components; smoke tests per agent; integration test with staging Jira/Confluence/SharePoint; coverage threshold 60% for new code                                                                                                                                                                                                                                                        |
| 5   | SDK drift 16 minor versions                                                                                                                                                            |     HIGH     | SDK upgrade with security delta audit; standardize uv workflow; deprecate poetry.lock; CI gate blocking drift                                                                                                                                                                                                                                                                                                                             |
| 6   | SharePoint over-permissioned `Sites.Read.All` tenant-wide                                                                                                                              |     HIGH     | Scoped permission `Sites.Selected` per site; documented access matrix per site (sub-aspect of item #3)                                                                                                                                                                                                                                                                                                                                    |
| 7   | Hardcoded Jira config (URL/IDs)                                                                                                                                                        |     HIGH     | Pydantic Settings from env per deployment                                                                                                                                                                                                                                                                                                                                                                                                 |
| 8   | Naming camouflage (gpt-oss-120b → azure/gpt-5-nano)                                                                                                                                    |     HIGH     | Transparent naming convention (e.g., `azure-eu/gpt-5-nano`); ADR documenting trade-off                                                                                                                                                                                                                                                                                                                                                    |
| 9   | Jira webhook not idempotent (`JiraWebhookController`)                                                                                                                                  |     HIGH     | Idempotency key from webhook event ID; Redis lock pattern                                                                                                                                                                                                                                                                                                                                                                                 |
| 10  | Custom API not yet contributed to core                                                                                                                                                 |     HIGH     | Extract Jira webhook + Support Desk endpoint to core as extension points; ADR decision on when to extract                                                                                                                                                                                                                                                                                                                                 |
| 11  | External services cascade risk (Jira/Confluence/SharePoint/Azure outage)                                                                                                               |     HIGH     | Circuit breaker per source; cached fallback for read paths; documented DR plan                                                                                                                                                                                                                                                                                                                                                            |
| 12  | Azure stack triple redundancy (DI + Foundry + core MinerU+LiteLLM)                                                                                                                     |     HIGH     | Standardize on core stack; ADR documenting Azure-specific justification; migration roadmap                                                                                                                                                                                                                                                                                                                                                |
| 13  | Azure AD B2C vendor lock-in                                                                                                                                                            |     HIGH     | ADR documenting trade-off; evaluate pure Keycloak federation alternative                                                                                                                                                                                                                                                                                                                                                                  |
| 14  | Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`                                                                                                            |     HIGH     | Fix import via core public API; lint rule blocking                                                                                                                                                                                                                                                                                                                                                                                        |
| 15  | Dual lock files (poetry.lock 84KB + uv.lock)                                                                                                                                           |     HIGH     | Migrate to uv-only workflow; deprecate poetry.lock; standard uv commands                                                                                                                                                                                                                                                                                                                                                                  |
| 16  | No own arc42 + ADRs                                                                                                                                                                    |     HIGH     | arc42 12 chapters skeleton + C4 L1/L2 + 13 ADRs answering design questions (Azure Foundry, DI vs MinerU, naming camouflage, service account, AD B2C, etc.)                                                                                                                                                                                                                                                                                |
| 17  | Deep-import violations in `ChatAgent.py` reach `swiss_ai_hub.core.generative_ai.{chat_history,guards}` and `swiss_ai_hub.core.i18n.locale_handler` — bypasses public `__init__.py` API |     HIGH     | Refactor to import via `from swiss_ai_hub.core import …` after promoting needed symbols to package public interface; add ruff/lint rule blocking deep imports across scope boundary; CI gate (see proposed `adr_038`)                                                                                                                                                                                                                     |
| 18  | MongoDB tenant-entry schema changed between the pinned and current core → migration required before SDK upgrade (the biggest upgrade risk for C\*C)                                    | **CRITICAL** | Build on the DB migration framework (ADR-NEW-003); author a forward + rollback migration; reconcile tenant docs against the Keycloak source of truth; dry-run on a restored copy in a maintenance window (see proposed `adr_045`)                                                                                                                                                                                                         |

### 3.4. aihub-Dem\*scope

Evidence base: code, configs, scripts, and README in `aihub-demoscope` repo (HEAD commit `abe968f 2026-01-13`).

| #   | Item                                                                                                                                                     |   Severity   | Recommendation actions                                                                                                                                                                                    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | SDK drift 44 minor versions (v0.246.4\* vs v0.290.4) - 4.5+ months behind (\*SDK pin not in `pyproject.toml`)                                            | **CRITICAL** | Confirm actual SDK pin via deploy manifests / CI; SDK upgrade plan with security delta audit (covers 44 minors of fixes); CI gate blocking drift > N versions; coordinate breaking-change migration       |
| 2   | Backup destination on the same VM (MinIO same host as Milvus / Mongo)                                                                                    | **CRITICAL** | Emergency cron sync to Swiss off-site (Infomaniak / Exoscale / Hetzner); replace ad-hoc `backup_updater_script.py` with official `milvus-backup` to off-host bucket; documented restore drill             |
| 3   | Pulumi mentioned in README but **IaC code not committed** (no `.iac/` folder in repo)                                                                    | **CRITICAL** | Commit the actual Pulumi code or remove the README sections; pick one IaC approach (Pulumi vs Terraform); document the real deployment process - currently undocumented and irreproducible from this repo |
| 4   | Test coverage ZERO (no `test_*.py`, no `.feature` files in 2 agents + 1 pipeline)                                                                        |     HIGH     | Baseline test plan (smoke tests per agent + pipeline); BDD `.feature` for hash-partitioned questions flow; integration test against staging Milvus                                                        |
| 5   | Manual production migration via SSH + `screen` + `scp`                                                                                                   |     HIGH     | Replace `scp migrate_questions.py demoscope:aihub/scripts/...` + `screen -r migration` workflow with Dagster job or k8s Job; track migration progress in DB, not `migration_log.json` on the VM           |
| 6   | Hash-partitioned Milvus design hardcoded in 3 places (drift risk)                                                                                        |     HIGH     | Single source of truth (already partially done in `lib/common/partition_utils.py`); CI test asserting agent + pipeline + migration script use the same hash function                                      |
| 7   | 4 agent variants deployed (persona / multi_personas × public / private)                                                                                  |     HIGH     | Document the public/private split rationale in ADR; verify the 4 instances run the same code or merge into 1 binary with config flag; reduce operational surface                                          |
| 8   | Stack divergence from core: MongoDB + Redis instead of FerretDB + Valkey                                                                                 |     HIGH     | ADR documenting why Demoscope diverged from core stack; migration plan or accept divergence; check whether Demoscope-specific Mongo features (BSON types, transactions) prevent migration                 |
| 9   | Phoenix v10.0.4 + LiteLLM v1.77.7 - pre-Langfuse (ADR `2026_02_10`) and older LiteLLM                                                                    |     HIGH     | Plan migration Phoenix → Langfuse following ADR `2026_02_10`; bump LiteLLM to current stable (v1.79+) for security patches                                                                                |
| 10  | Mixed sovereignty: Azure OpenAI SUI + local vLLM (Gemma-3, gte-Qwen2, bge-reranker)                                                                      |     HIGH     | Document the partial-sovereignty position in an ADR; clarify which workloads route to Azure SUI vs local vLLM; tied to Core sovereignty path decision (Option A/B/C)                                      |
| 11  | No own arc42 + ADRs                                                                                                                                      |     HIGH     | arc42 12 chapters + C4 L1/L2 + ADRs for: stack divergence (Mongo/Redis), hash partitioning, 4-variant split, sovereignty position, MinIO same-VM backup, hashed `persona_id` mod 1000                     |
| 12  | Agent crashes on start when upgrading the SDK (pin is very old)                                                                                          | **CRITICAL** | Reproduce the crash on a staging copy; decide remediate-in-place vs rebuild on the current core generation; sequence after a verified backup (PO roadmap Q4)                                              |
| 13  | No backup/restore actually built (only an ad-hoc `backup_updater_script.py`); no token/key renewal management — customer formally accepts responsibility | **CRITICAL** | Record as a customer-accepted risk (RACI) with explicit sign-off and documented data-loss exposure; still provide a minimal backup + key/token renewal runbook (see `adr_030`)                            |
| 14  | Vectors held in-memory (works only because the box has 200 GB RAM) — cost wall as data grows                                                             |   **HIGH**   | Plan move to disk-backed Milvus / DISKANN before data growth; add a capacity projection; run the RAG/vector-design gate (see proposed `adr_044`, `adr_046`)                                               |

### 3.5. aihub-W\*P

Evidence base: docker-compose, configs, README in `aihub-wpe` repo (HEAD commit `c4b1527 2025-12-18`). Note: `.env.prod`
is sensitive-file-guarded; only env-var **names** were inspected, not values.

| #   | Item                                                                                                                                                                     |   Severity   | Recommendation actions                                                                                                                                                                                                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **TLS private key committed to git** (`wpe.ai-agents.ch+1-key.pem` tracked, only `.env` is ignored)                                                                      | **CRITICAL** | Rotate the cert + key **immediately** (Let's Encrypt re-issue via Traefik); add `*.pem`, `*-key.pem`, `secrets/` to `.gitignore`; rewrite git history (BFG / `git filter-repo`) to purge the key; audit who pulled the repo since                                                  |
| 2   | Manual VM deployment via copy-paste (README: `cp docker-compose.latest.yml /opt/docker/config/bbv/`)                                                                     | **CRITICAL** | Add minimum reproducible deploy: bash script + checksums, or migrate to Gen 2 (Ansible Pull) / Gen 3 (`aihub-k8s`); current workflow has no rollback, no audit trail, no drift detection                                                                                           |
| 3   | LLM region not in repo (Azure OpenAI base URL is env-var only) → **sovereignty unverified**                                                                              |     HIGH     | Commit a non-secret `litellm-region.md` or `.env.example` stating Azure region; ADR aligning with Core sovereignty path; the choice must be explicit, not buried in a sysadmin's `/opt/bbv/.env`                                                                                   |
| 4   | SDK drift 35 minor versions (v0.255.6 vs v0.290.4)                                                                                                                       |     HIGH     | Bump `CORE_VERSION` in `.env.prod` with security delta review; CI gate blocking drift > N versions; pin via tag, not `latest` fallback                                                                                                                                             |
| 5   | `${CORE_VERSION:-latest}` fallback to `latest` if env var missing                                                                                                        |     HIGH     | Remove `:-latest` default - force explicit pinning; deployment must fail-fast if `CORE_VERSION` is unset; reproducible builds require explicit versions                                                                                                                            |
| 6   | `VOLUME_ROOT:-./.docker-volumes` defaults to local relative dir in production                                                                                            |     HIGH     | Force `VOLUME_ROOT` to be set (no `:-` fallback); document the production volume root (e.g. `/var/lib/aihub`) and snapshot strategy                                                                                                                                                |
| 7   | Off-site backup not in repo (no evidence of Restic / Swift / cross-region sync)                                                                                          |     HIGH     | Add backup config to repo (cron + Restic to Swiss off-site); follow 3-2-1 rule; document RTO/RPO; if backup exists out-of-repo, document where                                                                                                                                     |
| 8   | No own arc42 + ADRs - deployment-only repo with no design docs                                                                                                           |     HIGH     | Minimal arc42 (context + deployment + crosscutting); ADRs for: manual VM choice, identity provider choice, LLM region, sovereignty position; explain why WPE differs from core defaults                                                                                            |
| 9   | No tests of any kind (deployment-only repo, but no smoke / health validation scripts)                                                                                    |     HIGH     | Add post-deploy smoke test (curl health endpoints, OAuth round-trip, LiteLLM ping, OpenWebUI login); fail fast on broken deploy                                                                                                                                                    |
| 10  | SigNoz Cloud "EU" region for OTEL - same caveat as core (sovereignty unclear)                                                                                            |     HIGH     | Inherit core ADR on SigNoz region once written; document the choice locally in WPE README                                                                                                                                                                                          |
| 11  | Customer reports poor platform performance — root cause unknown, customer unresponsive                                                                                   |   **HIGH**   | Review Langfuse/OTEL traces + run a load-test baseline (Locust) against a config/hardware replica to locate the bottleneck; investigation BLOCKED pending customer input/data (see proposed `adr_046`)                                                                             |
| 12  | **Platform unused by the customer (no use / no run)** — adoption near zero; ops/hosting cost continues with no value delivered and no production validation for upgrades |   **HIGH**   | Clarify customer intent with account management (continue / pause / sunset); if continuing: resolve the #11 performance blocker + onboarding push; if not: controlled decommission to stop ops cost. While unused, the ROI of the #4 SDK upgrade is unclear — sequence accordingly |

### 3.6. aihub-F\*H

Evidence base: code, configs, Pulumi IaC, evaluation framework, and README in `aihub-fmh` repo (HEAD commit
`5509d39 2026-04-07`).

| #   | Item                                                                                                                                                                                                  |   Severity   | Recommendation actions                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | SDK drift 104 minor versions (v0.186.0 vs v0.290.4) - **largest of all customers**; upgrade to latest assessed as **very complex**                                                                    | **CRITICAL** | Multi-step SDK upgrade plan with security delta audit (104 minors = 10+ months of patches missed); incremental upgrades v0.186 → v0.220 → v0.260 → v0.290; CI gate blocking drift > N versions. If upgrade-in-place proves impractical (104 minors + LlamaIndex monkey-patch #2 + Mongo/Redis/Phoenix divergence #5), evaluate **rebuilding the 3 agents from scratch** on the current core generation (same remediate-vs-rebuild decision as Dem\*scope §3.4 #12) |
| 2   | LlamaIndex **monkey-patch** for GPT-5 (`lib/common/register_openai_models.py` modifies third-party globals at import time)                                                                            | **CRITICAL** | Replace with first-class core support (PR to `aihub-core` adding GPT-5 model registry); SDK upgrade will drop this patch automatically; document the workaround in ADR until removed                                                                                                                                                                                                                                                                               |
| 3   | Azure AI Search **instead of** Milvus - stack divergence from core                                                                                                                                    | **CRITICAL** | ADR justifying Azure AI Search vs core Milvus (vendor lock-in, double inference cost, sovereignty); migration plan to Milvus or formal acceptance of divergence with cost analysis; matches §3.3 C\*C "Azure stack triple redundancy" pattern                                                                                                                                                                                                                      |
| 4   | Backup status not in repo (Pulumi `stores/` deploys infra but no backup workload visible)                                                                                                             | **CRITICAL** | Verify Azure backup policy on `Storage Account` + `CosmosDB`/Mongo; cross-region replication for TARDOC/TARMED handbook data; documented restore drill; if backup exists out-of-Pulumi, document where                                                                                                                                                                                                                                                             |
| 5   | Stack divergence from core: MongoDB + Redis + Phoenix (pre-Langfuse) - same as Dem\*scope                                                                                                             |     HIGH     | Plan migration Phoenix → Langfuse (ADR `2026_02_10`); plan MongoDB → FerretDB; tied to SDK upgrade #1                                                                                                                                                                                                                                                                                                                                                              |
| 6   | Minimal test coverage (5 `test_*.py` + 5 BDD `.feature` for 3 agents + 2 pipelines)                                                                                                                   |     HIGH     | Coverage threshold 60% for new code; BDD feature files for the 3-agent routing flow (routing → handbook + rules); integration test against TARMED test fixtures                                                                                                                                                                                                                                                                                                    |
| 7   | Azure OpenAI Switzerland North + Azure AD - vendor lock-in (similar to C\*C)                                                                                                                          |     HIGH     | ADR documenting Azure choice rationale (TARDOC/TARMED is Swiss-only data, so Switzerland North is defensible); evaluate Keycloak federation as identity alternative                                                                                                                                                                                                                                                                                                |
| 8   | Bot uses MS Bot Framework + dev tunnel - dev/prod parity risk                                                                                                                                         |     HIGH     | Document the MS Teams integration deployment path; remove `agents/playground/bot_emulator/` references from prod docs; ensure prod doesn't depend on `devtunnel` workflow                                                                                                                                                                                                                                                                                          |
| 9   | Pulumi state in **Azure storage account** - single-cloud dependency                                                                                                                                   |     HIGH     | Document the Pulumi state account name / region in repo (not just credentials); plan state backup; if Azure account compromised, deployment is unrecoverable                                                                                                                                                                                                                                                                                                       |
| 10  | No own arc42 + ADRs - has good IaC + evaluation framework but no design docs                                                                                                                          |     HIGH     | arc42 12 chapters + C4 L1/L2 + ADRs for: Azure AI Search vs Milvus (#3), GPT-5 monkey-patch (#2), 3-agent routing design, TARDOC/TARMED data ingestion, MS Bot Framework choice                                                                                                                                                                                                                                                                                    |
| 11  | Hardcoded handbook namespace (`handbook_02_2026`) in pipeline `__init__.py`                                                                                                                           |     HIGH     | Pydantic Settings from env; allow multiple snapshots in parallel; document the versioning convention (`handbook_MM_YYYY`)                                                                                                                                                                                                                                                                                                                                          |
| 12  | Customer dissatisfied with answer quality — structured TARDOC/TARMED data not ingested with a designed vector schema; no RAG testing/eval strategy (the `evaluation/` framework exists but is unused) | **CRITICAL** | Run the RAG/vector-design gate (see proposed `adr_044`): field-aware chunking + metadata schema for the structured data; wire an eval harness on the existing `evaluation/` framework + Langfuse datasets; baseline then tune; tie to the AI-Search-vs-Milvus decision (`adr_039`)                                                                                                                                                                                 |

### 3.7. aihub-Ig\*s

Evidence base: `docker-compose.latest.yml` (generated), `Makefile`, `eval/` (Langfuse eval framework), and
`secrets/igs.yml.vault` in `aihub-igs` repo (HEAD `8eb4237`, 2026). **Status: pre-production / pilot.** **First customer
on the Gen 2 pattern** (Ansible-Vault config repo → Ansible Pull on Infomaniak OpenStack). **Deploy-only** (no custom
agents/pipelines/API; stock core images). Use case: internal **information-security & data-protection directive** RAG
assistant ("IGS Guisan", German). See [`C4`](../03_c4_diagrams.md) per-customer file `c4/igs.md`.

| #   | Item                                                                                                                                           |   Severity   | Recommendation actions                                                                                                                                                                                               |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Bot ships `DANGEROUS_DEV_ONLY_AUTH_FAKE_*` (name/email/oid/roles) in the **production** compose                                                | **CRITICAL** | Gate dev fake-auth behind the `dev` stage only; core hard-guard refusing the path in non-dev; remove `BOT_AUTH_FAKE_*` from the vault; CI gate. Confirm the live vault is not populating it (see proposed `adr_048`) |
| 2   | Core **app images pinned to `:latest`** (api/web/bot/agents/pipelines) — unbounded drift, non-reproducible                                     |   **HIGH**   | Pin a specific `CORE_VERSION` tag; fail-fast if unset; CI gate blocking drift. Same family as `adr_040` (chart pin) and `adr_001` (SDK versioning policy)                                                            |
| 3   | Sovereignty mixed / unverifiable — LiteLLM wired for Azure OpenAI **and** Swiss LLM Cloud (+ Cohere/Gemini/HF); routing not in repo            |   **HIGH**   | Confirm active routing in `litellm-config`; document the (partial) sovereignty position in an ADR; tie to the Core sovereignty path (Option A/B/C, `adr_000`)                                                        |
| 4   | Observability drift — compose runs **Phoenix v10.0.4** (pre-Langfuse) + OTEL→SigNoz Cloud, but eval docs name **Langfuse** as system of record |   **HIGH**   | Reconcile to a single backend (Langfuse, per ADR `2026_02_10`); add it to the tracked compose/playbook; decide SigNoz-region sovereignty (see proposed `adr_049`)                                                    |
| 5   | `CORS_ALLOW_ORIGIN: "*"` in OpenWebUI (explicit `# TODO: Make this more secure`)                                                               |     HIGH     | Restrict CORS to the known frontend origin(s); remove the wildcard before production cutover                                                                                                                         |
| 6   | Off-site backup not visible in repo (expected via Gen 2 `os_backups` Restic→Swift role)                                                        |     HIGH     | Verify the Gen 2 backup role is active for IGS; document RTO/RPO and a restore drill; follow 3-2-1 (see `adr_030`)                                                                                                   |
| 7   | No own arc42 + ADRs; `README.md` is empty                                                                                                      |     HIGH     | Minimal arc42 (context + deployment + crosscutting) + ADRs for: Gen 2 pilot, Docling parser choice, sovereignty position, Phoenix→Langfuse, `:latest` pinning                                                        |
| 8   | No unit/integration tests (only the Langfuse eval harness)                                                                                     |     HIGH     | Add post-deploy smoke tests (health endpoints, OAuth round-trip, LiteLLM ping, OpenWebUI login); keep the eval harness as answer-quality gate                                                                        |

> **Positives (vs other customers):** the most **core-aligned stack** — FerretDB + Valkey (not Mongo + Redis),
> **Docling** parser (matches `adr_042`), Milvus v2.6.7 + LiteLLM v1.80.5; a working **eval framework** (custom
> `Citation Quality` judge + `igs_guisan` dataset); **Swiss LLM Cloud** already wired (sovereign-LLM intent); and the
> **first adopter of Gen 2** (Ansible Pull, auto-reconcile, vault-encrypted secrets).

______________________________________________________________________

## 4. Assessment

Two parallel perspectives. Coverage now includes **5 Gen 1 production customers** (B*D / C*C / Dem*scope / W*P / F*H)
plus **1 Gen 2 pre-production pilot** (Ig*s); per-customer go-live items are detailed in **§3.4 (Dem\*scope)**, **§3.5
(W\*P)**, **§3.6 (F\*H)**, and **§3.7 (Ig\*s)**. In the two matrices below the `Ig*s` column is summarized as *pilot →
see §3.7* and [`c4/igs.md`](c4/igs.md) (its findings are catalogued there rather than duplicated per cell);
**Balmer-E\*** remains TBD pending team input.

### 4.1. By 10-pillar framework

10 pillars based on the [Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/),
extended with platform-specific pillars for multi-customer platforms (Multi-Tenancy, SDK Versioning, Observability,
Quality Assurance). Each cell lists findings for that scope. A cell marked `-` means that scope has no specific finding.

| #   | Pillar - Status                                                              | Core                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | B\*D                                                                                                                                                                                                                                                   | C\*C                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Ig\*s | Dem\*scope                                                                                                                                            | W\*P                                                                                                                                                               | F\*H                                                                                                                                                             | Balmer-E\* | Cross-cutting                                                                                                                                                                                                                   |
| --- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Multi-Tenancy & Customer Isolation** - Critical                            | • NATS subjects lack hierarchy `aihub.tenant.{id}.*`<br>• Milvus collections not namespaced per-tenant<br>• MongoDB entities lack required `tenant_id` field<br>• Valkey keys lack per-tenant prefix<br>• Neo4j graphs single, not namespaced<br>• No tenant provisioning workflow / automation API<br>• No per-tenant feature flags<br>• No per-tenant resource quotas (rate limit, storage, LLM budget)<br>• Tenant exists only at Keycloak layer (groups `/tenants/{id}`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | -                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | TBD   | Single-tenant deploy; 4-variant agent split (public/private), not true multi-tenancy                                                                  | Single-tenant deploy; inherits core gaps                                                                                                                           | Single-tenant deploy; Pulumi has no `tenants/` deploy unit                                                                                                       | TBD        | • Each customer = separate Docker stack<br>• Cannot run shared multi-tenant SaaS<br>• Operational cost grows linearly with customers<br>• No cross-tenant isolation test in CI                                                  |
| 2   | **SDK Versioning & Extension Contract** - Gap                                | • No public SDK release (PyPI/internal registry), only git+ssh<br>• No policy on breaking change, deprecation window<br>• No CHANGELOG categorization<br>• No downstream CI integration test with customers<br>• No lint rule blocking imports from internal modules                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | • Drift 11 minor versions (v0.279.2 vs v0.290.4)<br>• Internal import violation `pipelines/snk_enrichment.py:2`<br>• Patterns not extracted to core (`resolve_selection()`, HITL helpers)                                                              | • Drift 16 minor versions (v0.274.3 vs v0.290.4)<br>• Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`<br>• Deep imports in `agents/chat_agent/chat_agent/ChatAgent.py` to `swiss_ai_hub.core.generative_ai.{chat_history,guards}` + `swiss_ai_hub.core.i18n.locale_handler`<br>• Custom `switch_dependencies.py` instead of standard uv workflow<br>• Dual lock files `poetry.lock` (84KB) + `uv.lock`<br>• Multi-agent orchestrator and Jira/Confluence/SharePoint connectors not extracted | TBD   | • Drift 44 minor (v0.246.4\*)<br>• \*SDK pin not found in repo `pyproject.toml`<br>• Poetry + custom `switch_dependencies.py`                         | • Drift 35 minor (v0.255.6)<br>• Image-only via `CORE_VERSION` env (no SDK code)                                                                                   | • Drift 104 minor (v0.186.0) — **largest**<br>• **Monkey-patches LlamaIndex** for GPT-5 (`register_openai_models.py`)                                            | TBD        | -                                                                                                                                                                                                                               |
| 3   | **Security & Compliance** - Partial                                          | **Strengths**: 5 auth handlers (Keycloak/Token/Bearer/OAuth2/OpenWebUI) with JWKS 6h cache; hierarchical permission template with wildcards; AccessChecker tenant-ceiling + BDD tests; two-stage access control tested.<br>**Gaps**:<br>• UsageLimits partially wired (agent endpoints + OpenAI route only); no 4-layer enforcement or hard cap<br>• No `AuditLogEntity` (violates GDPR Art. 30, ISO 27001 A.12.4, SOC2)<br>• Event payloads not signed (JetStream unsigned JSON)<br>• NATS token-only auth, no mTLS; MongoDB/Redis connection string<br>• Presidio claim ≠ reality (code uses fragile LLM-based guard)<br>• MCP tool args bypass LiteLLM → Presidio guards bypassed 100%<br>• File upload trusts mime-type, no content sniffing<br>• OpenWebUI renders model list bypassing RBAC<br>• Docker volume not encrypted at rest<br>• No rate limiting per user/tenant at API<br>• No SAST / dep vuln scan / SBOM / image signing / container vuln scan                                                                                                                                                                                                                  | • Cohere reranking (US/Canada vendor)<br>• Hardcoded customer-specific config (SNK_ANCHOR, BASE_PATH)<br>• No secrets rotation policy                                                                                                                  | • Service account shared keys for Jira/SharePoint/Confluence (violates least-privilege)<br>• SharePoint Azure AD app-only `Sites.Read.All` tenant-wide<br>• Hardcoded Jira IDs (URL, Service Desk, Request Type, Project)<br>• Azure AD B2C federation instead of pure Keycloak (vendor lock-in)                                                                                                                                                                                                                         | TBD   | • Azure AD<br>• Presidio containers present in compose; LiteLLM Presidio guard config not verified<br>• Mixed sovereignty (Azure SUI + local vLLM)    | • **TLS private key committed in git** (`wpe.ai-agents.ch+1-key.pem` tracked)<br>• Azure AD<br>• Inherits core Presidio config (mask + block, `default_on: false`) | • Azure AD (`AUTH_AZURE_AD_*`)<br>• LlamaIndex monkey-patch modifies third-party globals at import time<br>• Pulumi state in single Azure storage account (SPOF) | TBD        | • Document ACL not inherited from Jira/SharePoint/Confluence into Milvus<br>• Service account ingests everything, users query everything (cross-user leak)<br>• Presidio is DE-only, Swiss multilingual FR/IT/EN PII not masked |
| 4   | **Reliability & Data Integrity** - Critical (Gen 2 partial fix)              | • No DB migration framework (schemas created implicitly by Pydantic + MongoEngine at startup)<br>• Cross-store consistency not guaranteed (NATS + Mongo + Valkey)<br>• No documented RTO/RPO<br>• No automated DR test / restore drill<br>• Backup encryption at rest unclear for Gen 1<br>• Milvus has no upsert-by-id → re-ingest = duplicate vectors<br>• Agent config schema evolution has no versioning<br>• No agent versioning for in-flight runs<br>• No run / delegation timeout<br>• No circuit breaker for external deps (LiteLLM, Keycloak, Milvus cascade)<br>• No DLQ for JetStream poison messages<br>• No HA architecture (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd all single-instance)<br>• **Gen 2 partial fix**: Ansible Pull auto-reconciles container drift; Restic backup to OpenStack Swift container (off-host)<br>• Still missing: cross-provider replication, HA stateful services, no automated DR drill                                                                                                                                                                                                                                            | • **Gen 1 fatal**: Backup destination on same SeaweedFS, same VM → VM dies = total loss<br>• No off-site replication<br>• Production 3.9x storage multiplier (1 TB → 5.1 TB)<br>• Not yet migrated to Gen 2 (Restic→Swift)                             | • **Gen 1 fatal**: Backup destination on same Azure VM<br>• Jira webhook not idempotent (`JiraWebhookController`): same event 2x = 2 agent runs<br>• External services cascade (Jira/Confluence/SharePoint/Azure outage)<br>• Not yet migrated to Gen 2 (Restic→Swift)                                                                                                                                                                                                                                                   | TBD   | • **Gen 1 fatal**: MinIO backup same VM<br>• Manual SSH+screen migration workflow<br>• No off-site replication                                        | • No off-site backup in repo<br>• `VOLUME_ROOT:-./.docker-volumes` defaults to local relative dir in prod                                                          | • No backup workload visible in Pulumi `stores/`<br>• Pulumi state SPOF (single Azure storage account)                                                           | TBD        | • Gen 2 Restic→Swift is off-host but **same cloud provider** (Infomaniak) - Infomaniak region outage = loses both primary and backup<br>• No cross-provider replication yet                                                     |
| 5   | **Operational Excellence** - Partial (improved with Gen 2)                   | **Strengths**: Full CI/CD (lint-pr, semantic-pr, build-\* per package, deploy-docs, auto-tag); pre-commit hooks; 47 ADRs; Docker Compose Jinja2 templates; **Gen 2 Ansible Pull pattern** (aihub-playbook every 15min auto-reconcile); **customer onboarding automation** (`setup-aihub.sh`); **Ansible Vault encrypted secrets** with auto-gen via `vault-vars-routing.yml`; **Traefik + Let's Encrypt ACME** automated SSL; **env vars drift detection CI** (`check_env_drift.py` nightly).<br>**Gaps**:<br>• No Operations Guide / Runbook for incident response<br>• No Incident Response Process (severity, escalation)<br>• No Upgrade Procedure documented<br>• No K8s/Helm chart for production<br>• Health checks don't distinguish liveness vs readiness<br>• arc42 ch.11 (Risks) needs update with new findings<br>• CLAUDE.md has false claims (Presidio integration)<br>• GDPR docs have false claims (right to erasure, audit logs immutable)<br>• Ansible Pull 15-min cadence too slow for hot-fix<br>• GitHub is a deploy SPOF (no local mirror)<br>• 3-repo version compatibility has no matrix / CI gate<br>• Deploy key rotation policy implicit, no automation | • Gen 1 deployment (Azure manual, not yet Gen 2)<br>• Own CI (build-agents, build-pipelines, auto-tag)<br>• No own arc42 docs (12 chapters required)<br>• No own ADRs (8+ key decisions)<br>• 6 docker-compose files separation rationale undocumented | • Gen 1 deployment (Azure VM + shell scripts, not yet Gen 2)<br>• Own CI (build-agents, build-pipelines, build-api, lint-pr)<br>• No own arc42 docs (12 chapters required)<br>• No own ADRs (13+ key decisions)<br>• Azure IaC `.iac/scripts/` shell scripts instead of Pulumi<br>• Custom API deployment monitoring undocumented                                                                                                                                                                                        | TBD   | • Gen 1; **Pulumi README-only, IaC code NOT committed** in repo<br>• Own CI (build-agents, build-api-and-bot, build-dagster)<br>• No own arc42 / ADRs | • Gen 1 manual VM (copy-paste docker-compose)<br>• No IaC, no CI for deploy<br>• No own arc42 / ADRs                                                               | • Gen 1 with **Pulumi committed (10 deploy_units — best IaC of the new 3)**<br>• Own CI for builds<br>• No own arc42 / ADRs                                      | TBD        | • No formal alerting infrastructure (only Slack on Ansible Pull failure)<br>• Customer documentation gate before go-production undefined<br>• B*D/C*C migration path from Gen 1 → Gen 2 missing                                 |
| 6   | **Performance & Scalability** - Critical                                     | • Single-server ceiling (Docker Compose only, no K8s)<br>• Milvus single-node, HNSW memory wall (122 GB RAM for 10M × 3072d × 4B)<br>• PostgreSQL single instance (no replica, no failover)<br>• SeaweedFS single master/volume/filer (no HA, replication="000")<br>• NATS single node, `max_memory_store: 512MB`, `max_file_store: 10GB` (dev config)<br>• Valkey single instance (SPOF)<br>• Pipeline ops use `in_process_executor` (single-thread)<br>• Dagster dynamic partition explosion risk (1 partition per file)<br>• Embedding batch size not tuned (recursive bisection fallback)<br>• LiteLLM throughput limit undocumented<br>• Tenant membership not cached (Keycloak call per request)<br>• GPU pinned to device 0, multi-GPU not utilized<br>• No resource limits in docker-compose                                                                                                                                                                                                                                                                                                                                                                               | • Production sizing (4/2026): 16 CPU + 64 GiB RAM + 1.9 TB disk<br>• 1.9 TB disk insufficient for 2+ shared customers                                                                                                                                  | -                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | TBD   | • vLLM GPU containers (Gemma-3 12b/27b)<br>• Hash-partitioned Milvus (1000 partitions for personas)                                                   | • Standard core single-VM<br>• No custom scaling                                                                                                                   | • Azure AI Search (managed)<br>• Azure Data Lake (managed)                                                                                                       | TBD        | • No Load Test Baseline (k6, Locust)<br>• No Performance Baseline document<br>• No Horizontal Scaling Guide                                                                                                                     |
| 7   | **Observability** - Traces strong, metrics weak (improved with Gen 2 SigNoz) | **Strengths**: Comprehensive OTEL (NATS/Mongo/Redis/Milvus/HTTP/asyncio); `SmartTracer` + `@trace_fn`; trace context cross-service via NATS headers; Langfuse LLM observability (prompt/response, cost); Docker healthchecks; HealthController; **Gen 2 SigNoz OTEL collector role** (host metrics, OTLP traces, journald log collection); **Slack failure notifications** from Ansible Pull.<br>**Gaps**:<br>• Bot scope (`packages/bot`) lacks OTEL → trace broken at bot boundary<br>• No business metrics (agent_runs, HITL escalations, ingestion rate, RAG latency)<br>• No formal SLO/SLI<br>• No Prometheus AlertManager with per-service severity rules<br>• No Grafana dashboards<br>• No on-call routing (PagerDuty/OpsGenie)<br>• Logs unstructured, default WARNING level<br>• No centralized log aggregation (self-hosted ELK/Loki)<br>• No per-tenant cost attribution in Langfuse<br>• No synthetic monitoring<br>• **SigNoz Cloud region "eu"** - observability data leaves tenant infra; sovereignty implication unclear<br>• SigNoz only on Gen 2; Gen 1 (B*D/C*C) doesn't have it                                                                              | • Gen 1 - no SigNoz<br>• Business-level metrics missing                                                                                                                                                                                                | • Gen 1 - no SigNoz<br>• Business-level metrics missing<br>• Custom API endpoints lack monitoring                                                                                                                                                                                                                                                                                                                                                                                                                        | TBD   | • Phoenix v10.0.4 (pre-Langfuse, ADR `2026_02_10`)<br>• LiteLLM v1.77.7 (older)                                                                       | • OTEL → SigNoz Cloud "EU"<br>• Phoenix v10.0.4                                                                                                                    | • Phoenix v10.0.4 (pre-Langfuse)<br>• OTEL configured                                                                                                            | TBD        | -                                                                                                                                                                                                                               |
| 8   | **Quality Assurance** - Gap                                                  | **Strengths**: ~69 test files in `packages/core`, ~35 `packages/api`, ~33 `packages/agent`; BDD via pytest-bdd; integration tests with real NATS (`SimulatedAgentApiTestRunner`); E2E for key flows.<br>**Gaps**:<br>• No Load test in CI<br>• No Chaos engineering<br>• No coverage threshold enforcement (no 80% gate)<br>• No SAST in CI<br>• No dependency audit (pip-audit, trivy)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | • Test coverage: 59 lines total (`tests/test_snk_enrichment.py`)<br>• 9 parametrized tests for 1 utility function only<br>• Agents and pipelines have no tests                                                                                         | • Test coverage minimal — 3 files / 788 lines in `agents/log_analysis_agent/log_analysis_agent/tests/` only<br>• `chat_agent`, `jira_issue_agent`, `retrieval_orchestrator_agent` + 6 pipelines + custom API + `lib/common` still untested                                                                                                                                                                                                                                                                               | TBD   | Test coverage **ZERO** (no `test_*.py`, no `.feature`)                                                                                                | No tests (deploy-only repo, no smoke validation)                                                                                                                   | 5 `test_*.py` + 5 BDD `.feature` for 3 agents + 2 pipelines                                                                                                      | TBD        | • No integration test between core release and customer projects<br>• No E2E test for multi-tenant isolation                                                                                                                    |
| 9   | **Cost Optimization** - Critical                                             | • LLM cost tracking via `LLMCostEvent` (per-model, per-token rates)<br>• Per-agent run cost attribution via Langfuse<br>• S3 file expiration 7 days (`FILE_EXPIRATION_DAYS = 7`)<br>• Backup retention configured<br>• `UsageLimits` partially wired (agent endpoints + OpenAI route only); no 4-layer enforcement → LLM cost unbounded for non-covered paths<br>• No pre-flight cost estimation<br>• No hard per-tenant cost cap<br>• No per-tenant storage quota<br>• No showback mechanism<br>• No budget alert<br>• MCP tool costs NOT tracked (external API costs invisible)<br>• Mongo collections unbounded (no TTL) = storage cost growth                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | -                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | TBD   | • LiteLLM cost tracking; vLLM per-token cost configured<br>• BBV Greece collaboration (offshore)                                                      | • Inherits core defaults<br>• No per-tenant cost attribution                                                                                                       | • **Azure AI Search per-query cost** (additional vs Milvus self-host)                                                                                            | TBD        | • No per-tenant cost attribution in Langfuse<br>• No cold storage tier (all data in hot storage)                                                                                                                                |
| 10  | **Sustainability** - Critical                                                | • Cloud-native capable in theory (containerized, stateless)<br>• License compliance OK (402 Python + 993 npm + 33 Docker all approved)<br>• Python 3.13 slim base images<br>• No Region/Data-Residency strategy<br>• No carbon footprint metrics<br>• No energy consumption tracking<br>• No sustainability reporting<br>• LLM calls not optimized (no aggressive caching, batching, prompt compression)<br>• No hardware lifecycle management<br>• No efficient algorithm benchmarking (HNSW vs DISKANN)<br>• Compute-heavy LLM calls not scheduled for off-peak                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | -                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | TBD   | • Local GPU vLLM = on-prem energy<br>• No carbon metrics                                                                                              | • Azure-dependent (region renewables claim inherited)<br>• No metrics                                                                                              | • Azure SUI region<br>• No own metrics                                                                                                                           | TBD        | -                                                                                                                                                                                                                               |

### 4.2. Business core values vs reality

| Core value                         | Statement / Source                                                            | Core (Platform)                                                                                                                                                                                                                                                             | b\*d                                         | c\*c                                                                                         | Ig\*s | Dem\*scope                                               | W\*P                                                    | F\*H                                                     | Balmer-E\* |        Status        |
| ---------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------- | ----- | -------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------- | ---------- | :------------------: |
| Swiss data sovereignty             | ADR `2026_02_24`: "All cloud inference must stay within Swiss infrastructure" | Declared via ADR, enforced via self-hosted local LLM or Swiss LLM Cloud                                                                                                                                                                                                     | 100% Azure OpenAI (Sweden region)            | 100% Azure AI Foundry (SUI+SWE) + Azure Document Intelligence                                | TBD   | Azure OpenAI SUI + local vLLM                            | Azure region not in repo (env-var only)                 | Azure OpenAI SUI + Azure AI Search                       | TBD        |       VIOLATED       |
| No vendor lock-in                  | Platform principle                                                            | OK (no lock-in in core)                                                                                                                                                                                                                                                     | Cohere reranking (US/Canada vendor)          | Lock-in to Azure across 5 layers (VM, Key Vault, AD B2C, OpenAI, Doc Intelligence) + Jina AI | TBD   | Azure OpenAI + Entra + local vLLM stack                  | Heavy Azure (OpenAI + Entra)                            | Heaviest Azure (OpenAI + AI Search + AD + Storage state) | TBD        |       VIOLATED       |
| Self-hosted, on-premise capable    | Marketing claim                                                               | Infrastructure self-hosted OK                                                                                                                                                                                                                                               | Infra self-hosted, LLM via Azure cloud       | Infra Azure VM, LLM Azure cloud                                                              | TBD   | Infra Azure VM, LLM mixed (Azure + local vLLM)           | Azure VM + Azure LLM (region unverified)                | Azure VM + Azure OpenAI + Azure AI Search                | TBD        |       PARTIAL        |
| "Swiss Sovereign AI" marketing     | Public positioning                                                            | Infrastructure-level correct                                                                                                                                                                                                                                                | B\*D uses Azure LLM → claim scope misaligned | C\*C uses Azure LLM → claim scope misaligned                                                 | TBD   | Local vLLM helps; Azure dependency persists              | Azure region unknown — claim risk                       | Azure SUI defensible for LLM; AI Search adds dependency  | TBD        | Needs wording review |
| Open-source platform               | License declaration                                                           | OK (BSD/MIT/Apache verified)                                                                                                                                                                                                                                                | OK                                           | OK                                                                                           | TBD   | OK                                                       | OK (deploy-only)                                        | OK                                                       | TBD        |          OK          |
| Multi-tenant SaaS support          | ADRs 2026_03_30, 2026_02_20                                                   | Tenant only at Keycloak; data layer not namespaced                                                                                                                                                                                                                          | Single-tenant deployment                     | Single-tenant deployment                                                                     | TBD   | Single-tenant deployment                                 | Single-tenant deployment                                | Single-tenant deployment                                 | TBD        |      NOT READY       |
| GDPR Art. 17 right to erasure      | Compliance docs claim "implemented"                                           | No user/tenant DELETE endpoint                                                                                                                                                                                                                                              | N/A                                          | N/A                                                                                          | TBD   | N/A (inherits core gap)                                  | N/A (inherits core gap)                                 | N/A (inherits core gap)                                  | TBD        |     FALSE CLAIM      |
| Audit log immutability             | GDPR docs claim "audit logs remain immutable"                                 | No `AuditLogEntity` in codebase                                                                                                                                                                                                                                             | N/A                                          | N/A                                                                                          | TBD   | N/A (inherits core gap)                                  | N/A (inherits core gap)                                 | N/A (inherits core gap)                                  | TBD        |     FALSE CLAIM      |
| Presidio PII protection            | CLAUDE.md claims integrated                                                   | Code uses fragile LLM-based guard, not Presidio                                                                                                                                                                                                                             | N/A                                          | N/A                                                                                          | TBD   | Containers in compose; LiteLLM guard config not verified | Core config in repo (mask + block, `default_on: false`) | Not verified (older core baseline)                       | TBD        |     FALSE CLAIM      |
| MCP secure tool execution          | Implied by MCP integration                                                    | Tool args bypass LiteLLM → Presidio bypassed 100%                                                                                                                                                                                                                           | N/A                                          | High risk given agent-heavy use case                                                         | TBD   | N/A (inherits core gap)                                  | N/A (inherits core gap)                                 | N/A (inherits core gap)                                  | TBD        |      LEAK RISK       |
| Document ACL respect               | Implied by RBAC architecture                                                  | Milvus has no ACL field, retrieval doesn't filter by user                                                                                                                                                                                                                   | N/A                                          | Service account ingests everything; cross-user data leak                                     | TBD   | N/A (inherits core gap)                                  | N/A (inherits core gap)                                 | N/A (inherits core gap)                                  | TBD        |      LEAK RISK       |
| Multi-language Swiss (DE/FR/IT/EN) | Platform i18n declared                                                        | Presidio hardcoded `de` across 10 LiteLLM config files in `infra/configs/litellm/`                                                                                                                                                                                          | i18n DE/EN/FR/IT translations present        | N/A                                                                                          | TBD   | DE primary (Swiss `allowed_plz.json`)                    | Inherits core (DE/EN/FR/IT)                             | DE primary (TARDOC/TARMED Swiss medical)                 | TBD        |       PARTIAL        |
| Cost protection per tenant         | Implied by UsageLimits class                                                  | `UsageLimits` partially wired (agent endpoints + OpenAI route via `Depends(use_usage_limits)`); missing 4-layer enforcement, pre-flight estimation, hard cap                                                                                                                | N/A                                          | N/A                                                                                          | TBD   | N/A (single-tenant)                                      | N/A (single-tenant)                                     | N/A (single-tenant)                                      | TBD        |       PARTIAL        |
| Disaster recovery capability       | Backup service exists                                                         | Backup destination = same SeaweedFS instance on same VM                                                                                                                                                                                                                     | No off-site backup                           | No off-site backup                                                                           | TBD   | FATAL (MinIO same VM)                                    | Not in repo                                             | Not in repo (no backup workload in Pulumi)               | TBD        |        FATAL         |
| Common enterprise AI patterns      | Agent framework capability                                                    | Conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution, browser automation: working. Vision / predictive analytics / fine-tuned model serving: out of scope (see `adr_aihub_supported_use_cases.md`) | RAG agents working                           | Multi-agent orchestration working                                                            | TBD   | Personas + hash-partitioned RAG                          | Standard core only                                      | 3-agent routing + BITL events                            | TBD        |          OK          |

______________________________________________________________________

## 5. Concerns and Documentation Backlog

Each concern follows the format `Concern → Direction`. **Concern** = what the issue is and how it manifests.
**Direction** = high-level fix (detailed implementation deep-dive in §6 and dedicated ADRs). Strategic concerns (with
trade-offs to choose between) are presented as full blocks. Documentation deliverables are listed at the end of each
scope.

### 5.1. aihub-core (Platform)

#### Sovereignty and Compliance

**Sovereignty path violation**

- _Concern_:
  - B\*D uses Azure OpenAI (Sweden region)
  - C\*C uses Azure AI Foundry (SUI+SWE) and Azure Document Intelligence
  - Directly violates ADR `2026_02_24` (Swiss sovereign dual-mode inference)
  - "Swiss Sovereign AI" marketing claim needs scope clarification
  - Compliance considerations under
    [Schrems II](https://curia.europa.eu/juris/document/document.jsf?docid=228677&doclang=EN) and
    [US Cloud Act](https://www.congress.gov/bill/115th-congress/house-bill/4943)
- _Direction_: choose 1 of 3 options:
  - **Option A** - self-hosted local LLM for every customer
  - **Option B** - hybrid with ADR updated to explicitly allow Azure-EU regions
  - **Option C** - per-customer sovereignty tier (customer chooses by plan)

**False documentation claims**

- _Concern_:
  - CLAUDE.md claims Presidio is integrated but the code uses a fragile LLM-based guard
  - GDPR docs claim right-to-erasure is implemented but there is no user DELETE endpoint
  - GDPR docs claim audit logs are immutable but there is no `AuditLogEntity`
- _Direction_:
  - Remove false claims from CLAUDE.md and GDPR docs
  - Sync docs with reality (only claim what the code actually does)
  - Add doc-code drift detection in CI to catch early

**AuditLogEntity missing**

- _Concern_:
  - No dedicated `AuditLogEntity` in the codebase
  - Violates [GDPR Art. 30](https://gdpr-info.eu/art-30-gdpr/) (records of processing)
  - Violates [ISO 27001 A.12.4](https://www.iso.org/standard/27001) (event logging)
  - Violates [SOC2 CC7.2](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)
    (system monitoring)
- _Direction_:
  - Implement write-once entity with retention policy
  - Tamper-evident hash chain for integrity
  - Details: see `adr_011_audit_log_entity.md`

**GDPR right-to-erasure unimplementable**

- _Concern_:
  - No cascade user/tenant DELETE endpoint
  - Data spread across Mongo / Milvus / Neo4j / Valkey / SeaweedFS with no deletion path
  - Customer erasure requests cannot be fulfilled → compliance fail
- _Direction_:
  - Implement cascade DELETE endpoint across every data store
  - Document compliance procedure per data store
  - Test with a dry-run erasure flow

#### Security

**UsageLimits enforcement incomplete**

- _Concern_:
  - `UsageLimits` class defined and partially wired via `Depends(use_usage_limits)` at
    `agent_endpoints_discovery_service.py` and `openai_service.UsageLimits.check_and_raise`
  - **Gaps**: not applied across all routes; no 4-layer enforcement (per-user / per-tenant / per-model / global); no
    pre-flight cost estimation; no hard cap / circuit breaker
  - LLM cost still effectively unbounded for non-covered paths
  - User spam requests → cost runaway risk
- _Direction_: extend to 4-layer enforcement across all routes, add pre-flight estimation and hard cap. Details:
  `adr_012_usage_limits_enforcement.md`.

**MCP tool args bypass Presidio**

- _Concern_:
  - MCP tool execution sends args directly, not via LiteLLM proxy
  - Presidio PII guard bypassed 100% for every tool call
  - PII leaks to external tool servers
- _Direction_: implement `SecureMCPExecutor` with:
  - Presidio sanitization on tool args
  - Tool authorization check
  - Details: `adr_019_mcp_secure_executor.md`

**Document ACL not inherited**

- _Concern_:
  - ACL from Jira / SharePoint / Confluence / SMB not inherited into Milvus metadata
  - Service account ingests every document
  - Retrieval doesn't filter by user
  - → cross-user data leak via RAG (user A queries see user B's data)
- _Direction_:
  - ACL metadata field in the Milvus collection
  - Retrieval-time filter by `user_groups`
  - Details: `adr_020_document_acl_inheritance.md`

**Presidio DE-only, multilingual gap**

- _Concern_:
  - Presidio analyzer hardcodes `de` across 10 LiteLLM config files in `infra/configs/litellm/`
  - Swiss customer data in FR/IT/EN is not PII-masked before reaching the LLM
  - PII leak for non-German users
- _Direction_:
  - Per-language Presidio routing (DE/FR/IT/EN)
  - Swiss custom recognizers: AHV, CHE-UID, +41 phone number

**File upload trusts mime-type**

- _Concern_:
  - API trusts header mime-type, no content sniffing
  - Attacker uploads `.exe` disguised as `.pdf`
  - Malware lands in storage
- _Direction_:
  - python-magic content sniffing before accept
  - Malware scan (ClamAV) before committing to storage

**Volumes not encrypted at rest**

- _Concern_:
  - Docker volumes mounted plain
  - Disk theft or VM snapshot exposure = all data in plaintext
- _Direction_:
  - LUKS encryption per deployment
  - Documented procedure per stage (dev / staging / prod)

**No service-to-service mTLS**

- _Concern_:
  - NATS is token-only auth
  - Mongo / Redis use connection strings
  - Internal traffic is not encrypted or mutually authenticated
  - MITM risk inside the cluster
- _Direction_:
  - mTLS for NATS / Mongo / Redis
  - Automated cert rotation (cert-manager or Vault)

**OpenWebUI bypasses RBAC**

- _Concern_:
  - Model list endpoint doesn't filter by user permissions
  - Users can see names of agents they're not authorized for (agent existence leak)
- _Direction_: reverse proxy filter before reaching OpenWebUI (filter model list by user's groups).

**No supply chain security**

- _Concern_:
  - No SBOM (Software Bill of Materials)
  - No image signing
  - No vulnerability scanning
  - Unknown CVEs in images
  - Supply chain attack risk
- _Direction_:
  - SBOM generation via syft
  - Image signing via cosign
  - Vuln scan via trivy in CI

**No API rate limiting**

- _Concern_:
  - API has no per-user / per-tenant rate limit
  - DoS risk via spam requests
  - Cost runaway if requests reach LLM endpoints
- _Direction_:
  - Rate limiter middleware (Redis-backed)
  - Tiers per user and per tenant

#### Reliability and Data Integrity

**No DB migration framework**

- _Concern_:
  - Schemas created implicitly by Pydantic + MongoEngine at startup
  - Core version upgrade may silently drop fields
  - No rollback path
  - No migration history
- _Direction_:
  - Versioned migration framework (Alembic-like)
  - Metadata collection tracking applied migrations

**Milvus duplicate vectors on re-ingest**

- _Concern_:
  - Milvus has no upsert-by-id
  - Ingestion always inserts → re-ingesting the same document = duplicate vectors
  - Retrieval returns wrong results (same chunk shows up N times)
- _Direction_: delete-then-insert pattern by `document_id` before insert.

**No DLQ for JetStream**

- _Concern_:
  - Poison messages have no dead-letter queue
  - A bad event = consumer crash loop
  - Downstream processing is blocked
- _Direction_:
  - Dedicated DLQ subject (`aihub.dlq.*`)
  - Max-retry policy
  - Alerting when messages land in DLQ

**No circuit breaker for external deps**

- _Concern_:
  - Calls to LiteLLM / Keycloak / Milvus have no breaker
  - External outages cascade across the platform
  - No degraded mode
- _Direction_:
  - `pybreaker` per external dep
  - Threshold-based open
  - Half-open recovery probe

**No run / AITL timeout**

- _Concern_:
  - Agent runs have no time budget
  - AITL recursion has no depth cap
  - Stuck loops = resource leak
  - Recursive AITL escalation = cost explosion
- _Direction_:
  - Explicit timeout per run (configurable)
  - `MAX_AITL_DEPTH = 5` hardcap

**Mongo TTL missing**

- _Concern_:
  - Collections `agent_events` and `threads` have no TTL
  - Storage grows unbounded
  - No archival pattern
- _Direction_:
  - TTL indexes with retention policy per collection
  - Archival job for long-term data

**Cross-store snapshot inconsistency**

- _Concern_:
  - Backup mid-run may be inconsistent across NATS, Mongo, Valkey
  - No coordinated checkpoint
  - Restore may land in an invalid state
- _Direction_:
  - Snapshot orchestration with short-pause-then-flush
  - Or event-sourced backup from JetStream (replayable)

**No High Availability architecture**

- _Concern_: every stateful service runs as a **single instance** = SPOF:
  - **PostgreSQL** - no read replica, no streaming replication, no failover
  - **NATS** - single node, `max_memory_store: 512MB` dev config
  - **Valkey** - single instance (SPOF for agent RunContext / ThreadContext)
  - **SeaweedFS** - single master + single volume + single filer, `replication="000"`
  - **Milvus** - single-node
  - **Keycloak** - single instance
  - **etcd** - single (metadata backend for Milvus and SeaweedFS - losing etcd loses both)
  - Container restart = full request failure, no graceful degradation
- _Direction_: HA roadmap per service:
  - **PostgreSQL** - streaming replication or Patroni cluster with failover
  - **NATS** - 3-node cluster with replicated JetStream storage
  - **Valkey** - Sentinel or Redis Cluster mode
  - **SeaweedFS** - multi-master + `replication="001"` (cross-host)
  - **Milvus** - cluster mode
  - **Keycloak** - Infinispan cluster
  - **etcd** - 3-node cluster
  - Load balancer with health checks
  - Multi-AZ deployment when on K8s
  - Document failover RTO per service

#### Observability

**Bot scope has no OTEL**

- _Concern_:
  - `packages/bot` has no OTEL instrumentation
  - Traces break at the bot boundary
  - Can't debug MS Teams / Slack → agent flow
- _Direction_: add OTEL instrumentation in the bot scope (auto-instrumentation plus manual spans for key paths).

**No alerting infrastructure** _[Partial fix for Gen 2]_

- _Concern_:
  - No Prometheus AlertManager
  - No on-call routing
  - Production failures don't page on-call
  - Depend on manual log inspection
- _Status_: **Partial fix for Gen 2** - Slack notification on Ansible Pull failure (`notify_failure.yml`); SigNoz
  collector ships metrics to SigNoz Cloud which has alert rules. **Still missing**: per-service severity rules, on-call
  rotation (PagerDuty/OpsGenie), formal incident response procedure.
- _Direction_:
  - Formal Prometheus + AlertManager setup or use SigNoz alert rules
  - On-call routing via PagerDuty / OpsGenie
  - Alert rules per service severity (P1/P2/P3)
  - Incident response runbook

**No business metrics and SLI/SLO**

- _Concern_:
  - Only technical traces, no business metrics
  - Missing: agent_runs, HITL escalations, ingestion rate, RAG latency
  - No formal SLI / SLO documented
- _Direction_:
  - Business metrics export via Prometheus
  - Formal SLI / SLO documented per service
  - Grafana dashboards

**Unstructured logs and no aggregation** _[Partial fix for Gen 2]_

- _Concern_:
  - Logs are unstructured (default text format)
  - Default WARNING level (miss INFO debugging info)
  - No central aggregation
  - Debugging production requires SSHing into individual containers
  - No cross-service search
- _Status_: **Partial fix for Gen 2** - SigNoz OTEL collector journald (system logs) + OTLP receiver (app traces);
  central aggregation via SigNoz Cloud. **Still missing**: JSON structured logging (logs still text format), log level
  config per env, self-hosted alternative for sovereignty.
- _Direction_:
  - JSON structured logging in app code (separate concern from SigNoz)
  - Log level config per env
  - Consider self-hosted SigNoz or Loki if cloud sovereignty is an issue

**No per-tenant cost attribution**

- _Concern_:
  - Langfuse tracks cost overall, doesn't break down per-tenant
  - In multi-tenant deployments you can't compute cost per customer
  - Showback is impossible
- _Direction_:
  - Tenant label in Langfuse traces
  - Per-tenant cost dashboard
  - Automated monthly cost report

**AI use case scope undefined**

- _Concern_:
  - Doc claim "agent framework covers 9 of 10 enterprise AI use cases" has no ADR backing
  - No canonical taxonomy specifying "what the 10 use cases are"
  - Audit / customer pre-sales asking "is use case X supported" has no authoritative answer
  - Vision / predictive analytics / fine-tuning are out of scope but not explicit
  - Marketing claims may exceed actual capability
- _Direction_:
  - **Authoritative ADR** defining the supported use cases list (✅ Full / ⚠️ Partial / ❌ Out of scope)
  - See `adr_037_aihub_supported_use_cases.md` (proposed)
  - Quarterly review cycle to track coverage maturity
  - Pre-sales playbook anchored to the ADR list

#### Strategic concerns

**Workflow architecture - Process (auto-workflow) vs Agentic** _[Strategic]_

- _Concern_: `packages/process` (declarative orchestration for agents + humans + external programs) is **dead code** (0
  external imports). The team in practice uses agentic workflows in `packages/agent`. CLAUDE.md and arc42 still describe
  process as a production component → architecture drift, false claim.
- _Trade-off_:
  - **Process**: ✓ deterministic, clear audit trail, no LLM cost, easy to test, compliance-friendly · ✗ rigid paths,
    brittle, can't handle ambiguous tasks
  - **Agentic**: ✓ flexible for open-ended tasks, self-correcting, NL friendly · ✗ non-deterministic, LLM cost on every
    decision, fuzzy audit, hallucination risk, no guaranteed execution path
  - Dropping entirely = loss of capability for **compliance customers** (banking/healthcare/gov); high-volume
    low-variance tasks via agentic are **overkill in cost/latency**; CLAUDE.md still claims it → **false architecture
    claim**.
- _Direction_: **Option A (hybrid, recommended)** - activate process for deterministic / compliance flows, agentic for
  ambiguous, document explicit routing criteria (audit requirement / fixed steps → process; open-ended / reasoning →
  agentic). **Option B (deprecate cleanly)** - delete code, update CLAUDE.md + arc42 + docs, migration guide to
  Temporal/self-hosted n8n/Camunda. **Needs its own ADR.**

**Connector framework missing** _[Strategic]_

- _Concern_: No shared connector SDK in core. B*D built its own SMB; C*C built Jira/Confluence/SharePoint; new customers
  must build Salesforce/Notion/GitHub/Drive/Box from scratch.
- _Impact_: Onboarding time = **O(N × M)** instead of O(M); every customer reimplements
  auth/pagination/rate-limit/dedup/incremental sync/schema mapping; bug fixes don't propagate; **biggest entry barrier**
  for new customers; uncompetitive vs Airbyte/Fivetran/Meltano (300+ connectors built-in).
- _Direction_: `BaseSourceConnector` abstract framework with plugin discovery; ship built-in common connectors (SMB, S3,
  SharePoint, Confluence, Jira, GitHub, GitLab, Notion, Drive, Box, Salesforce, IMAP) - covers 80% of use cases;
  long-term **connector marketplace** (community-contributable).

**Code RAG - semantic chunks only, structural missing** _[Strategic]_

- _Concern_: The parsing pipeline only does semantic chunking (BGE-M3 + MinerU), suitable for prose documents but **not
  for code** - cuts mid-method, breaks syntactic boundaries, loses call graph, loses scope.
- _Impact_: A "which function handles X" query retrieves half a method → broken context; "all callers of Y" is
  infeasible without a call-graph index; AI assistant for codebase (C\*C IT services use case, future DevOps customers)
  is unreliable.
- _Direction_: **tree-sitter AST chunking** (100+ languages) plus **code-specific embedding**
  (CodeBERT/GraphCodeBERT/UniXcoder) plus **hybrid index** (vector plus symbol ctags/scip plus call-graph Neo4j) plus a
  code-aware reranker. A deferred plan exists in memory and needs to be unblocked.

**Open-source dependency lock-in** _[Strategic]_

- _Concern_: LLM is already abstracted via the **LiteLLM gateway**, but parser (MinerU), embedding (BGE-M3), reranker
  (BGE), PII (Presidio), vector store (Milvus), STT-TTS (Speaches) **have no equivalent abstraction** - hardcoded
  throughout pipeline code.
- _Impact_: License precedent (Elasticsearch → Elastic License 2024, MongoDB → SSPL, Redis → RSAL/SSPL, Terraform → BSL)
  \- **open-source ≠ no lock-in**; MinerU/BGE/Milvus could go the same way; swapping to a better alternative (MinerU2,
  Qwen embedding, Qdrant) is hard because the dep is embedded throughout the code; no integration test verifies a swap.
- _Direction_: **[Hexagonal Ports and Adapters](https://alistair.cockburn.us/hexagonal-architecture/)** for 6 layers
  (`DocumentParser` / `EmbeddingProvider` / `Reranker` / `VectorStore` / `PIIDetector` / `SpeechProcessor`); **contract
  tests** per interface; config-driven implementation selection; **dedicated ADR per major dep** with exit plan.

#### Performance

**Pipeline single-thread executor**

- _Concern_:
  - Dagster ops use `in_process_executor`
  - Single-threaded for ops within a run
  - Throughput is low when parsing / embedding many files
- _Direction_: Multiprocess executor with explicit worker pool config.

**Milvus single-node memory wall**

- _Concern_:
  - Milvus runs single-node
  - HNSW index memory wall: 10M × 3072d × 4B = 122 GB RAM
  - Multi-customer scale is blocked
- _Direction_:
  - Milvus cluster mode
  - DISKANN benchmark for disk-backed index (memory-efficient)

**Dagster dynamic partition explosion**

- _Concern_:
  - 1 partition per file pattern
  - 1M files = 1M partitions
  - DAG explosion, slow scheduler
- _Direction_: temporal partitioning (per day / per week) instead of dynamic per-file.

**No load test baseline**

- _Concern_:
  - No k6 / Locust scripts in the repo
  - Throughput limit is unknown
  - No regression detection
- _Direction_:
  - Load test suite (k6) in CI
  - Baseline numbers per critical path
  - Alert when regression exceeds threshold

**Embedding batch not tuned**

- _Concern_:
  - Batch size uses recursive bisection fallback (heuristic)
  - Throughput not optimal
  - GPU underutilized
- _Direction_:
  - Explicit batch config per model
  - Profile-based tuning per GPU memory

#### Documentation deliverables (team owners required)

- High-Level Architecture Diagram (HLAD) reflecting actual production
- C4 Level 1 (System Context) and C4 Level 2 (Container) - verify draft from review
- arc42 chapter 11 (Risks) update with new findings
- ADR for `packages/process` decision (Option A activate / Option B deprecate)
- ADR for connector framework strategy
- ADR for code RAG architecture
- Dedicated ADR for each major external dependency (MinerU/BGE/Milvus/Presidio/Speaches) with exit plan

### 5.2. aihub-b\*d

#### Concerns

**SDK version drift**

- _Concern_:
  - Drift of 11 minor versions (v0.279.2 vs core v0.290.4)
  - Internal import violation `pipelines/snk_enrichment.py:2`
  - Patterns not yet extracted to core (`resolve_selection()`, HITL helpers)
- _Direction_:
  - SDK upgrade plan with security delta audit
  - Extract reusable patterns to core
  - SDK versioning CI gate to block PRs when drift is too large

**Backup destination same VM**

- _Concern_:
  - Backup SeaweedFS runs on the same VM as primary data
  - VM failure = loss of both primary and backup
  - Violates the 3-2-1 rule
- _Direction_:
  - Emergency cron sync to Swiss-sovereign off-site (Infomaniak CH / Exoscale CH / Hetzner)
  - Long-term: cross-region replication

**Cohere reranking US/Canada**

- _Concern_:
  - Cohere is a US/Canada vendor
  - Conflicts with the sovereignty story when serving Swiss customers
- _Direction_:
  - ADR documenting the trade-off (acceptable risk or must migrate)
  - Or migrate to a sovereign alternative (local BGE, local Jina)

**Storage multiplier 3.9x**

- _Concern_:
  - Production sizing 1 TB source → 5.1 TB total (3.9x multiplier)
  - 1.9 TB disk insufficient for 2+ shared customers
  - Storage cost scales linearly
- _Direction_:
  - Data partitioning strategy: sharding / time-based / customer-based / cold storage
  - ADR documenting the strategy
  - Cold storage tier for rarely-accessed data

**No test coverage on agents/pipelines**

- _Concern_:
  - Test coverage = 59 lines (1 utility function)
  - 3 agents and 4 pipelines completely untested
  - High regression risk on upgrades
- _Direction_:
  - Baseline test plan (smoke tests per agent / pipeline)
  - Integration tests with staging data
  - Coverage threshold of 60% for new code

**Hardcoded customer config**

- _Concern_:
  - SNK_ANCHOR, BASE_PATH `/mnt/smb_b*d/30 GP/31 Kunden` hardcoded
  - Deployment can't serve other customers
  - Hard to test with different data
- _Direction_:
  - Pydantic Settings from env
  - Documented config matrix per env

**Weak model malformed JSON**

- _Concern_:
  - Weak models (`gpt-oss-120b`, small models) return malformed JSON
  - Breaks downstream workflow steps
  - Team retries the same prompt = same failure pattern
  - Cost runaway risk, root cause not addressed
- _Direction_:
  - **Structured output / JSON mode** (OpenAI `response_format`, function calling with schema)
  - Pydantic validation on the client
  - **Fallback chain** weak → strong model (cost-aware escalation)
  - **Golden test suite** for the JSON contract in CI

**No resource limits in docker-compose**

- _Concern_:
  - Containers have no CPU / memory limits
  - A single leaky container can OOM the entire host
- _Direction_:
  - Explicit resource limits per service
  - Profile-based sizing

#### Documentation deliverables

- arc42 12 chapters for B\*D
- C4 Level 1 (System Context) plus C4 Level 2 (Container): 3 agents plus 4 pipelines plus configs
- ADRs answering 10 design questions: Azure OpenAI sovereignty trade-off; customer/supplier data split; partitioning
  strategy; SMB base path rationale; SNK enrichment placement; regex utils placement; Cohere reranking choice; 6
  docker-compose separation; `snk_enrichment.py:2` import fix; test strategy

### 5.3. aihub-c\*c

#### Concerns

**SDK version drift (larger than B\*D)**

- _Concern_:
  - Drift of 16 minor versions (v0.274.3 vs core v0.290.4)
  - Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`
  - Deep imports in `agents/chat_agent/chat_agent/ChatAgent.py` to
    `swiss_ai_hub.core.generative_ai.{chat_history,guards}` + `swiss_ai_hub.core.i18n.locale_handler` (see proposed
    `adr_038`)
  - Custom tooling `switch_dependencies.py` instead of standard uv workflow
  - Dual lock files (poetry.lock 84KB plus active uv.lock)
- _Direction_:
  - SDK upgrade with security delta audit
  - Standardize uv workflow
  - Deprecate poetry.lock

**Backup destination same VM**

- _Concern_:
  - Same fatal pattern as B\*D
  - Backup on the same Azure VM as primary
  - VM failure = total loss
- _Direction_:
  - Tier 1 - emergency cron sync to Swiss-sovereign storage
  - Tier 2 - Dagster scheduled replication
  - Tier 3 - cross-region replication with encryption

**Service account shared keys**

- _Concern_:
  - Jira / SharePoint / Confluence use a service account shared key
  - Bypasses least-privilege principle
  - Bypasses per-user permissions from source systems
- _Direction_:
  - Per-user OAuth delegated permissions
  - Source systems enforce their own ACL
  - Audit trail per user query

**SharePoint over-permissioned**

- _Concern_:
  - SharePoint Azure AD app-only `Sites.Read.All` tenant-wide
  - = super-admin level access
  - Accesses all tenant data instead of scoped sites
- _Direction_:
  - Scoped permission `Sites.Selected` per site
  - Document access matrix per site

**Hardcoded Jira config**

- _Concern_:
  - Jira URL, Service Desk ID, Request Type ID, Project ID hardcoded
  - Deployment can't serve another instance
  - Hard to test with fixture data
- _Direction_: Pydantic Settings from env per deployment.

**Naming camouflage**

- _Concern_:
  - Alias `gpt-oss-120b` → `azure/gpt-5-nano` in the LiteLLM config
  - Developers / auditors reading the model name don't know the underlying service
  - Sovereignty audit is hard to trace
- _Direction_:
  - Transparent naming convention (e.g., `azure-eu/gpt-5-nano`)
  - ADR documenting the trade-off if an alias is needed

**Jira webhook not idempotent**

- _Concern_:
  - `JiraWebhookController` has no idempotency-key check
  - Same event delivered twice = 2 agent runs
  - Duplicate cost plus inconsistent state
- _Direction_:
  - Idempotency key from webhook event ID
  - Redis lock pattern

**Custom API extension not contributed to core**

- _Concern_:
  - Jira webhook handler plus Support Desk endpoint built in C\*C
  - Pattern is useful for other customers
  - Locked-in to customer scope
- _Direction_:
  - Extract to core as extension points
  - ADR decision on when to extract (criteria: > N customers need it)

**Test coverage zero**

- _Concern_:
  - No `tests/` directory
  - 4 agents plus 6 pipelines plus custom API plus `lib/common` completely untested
  - High regression risk
- _Direction_:
  - Baseline test plan
  - Smoke tests per component
  - Integration tests with staging Jira / Confluence / SharePoint

**External services cascade risk**

- _Concern_:
  - Hard dependency on Jira / Confluence / SharePoint / Azure
  - Outage = full agent failure
  - No degraded mode
- _Direction_:
  - Circuit breaker per source
  - Cached fallback for read paths
  - Documented DR plan

**Data leak via prompt-based isolation**

- _Concern_:
  - Multi-source data (Jira / Confluence / SharePoint) is not isolated at the data layer
  - Team uses prompt instructions to guide agents not to mix data
  - **Defensive layer at the wrong level**:
    - Prompt-injection bypass is easy
    - RAG retrieval happens **before** the LLM sees the prompt
    - LLM may mix data during reasoning even when told not to
    - No forensic audit trail
- _Direction_: move isolation down to the **data layer**:
  - Per-tenant Milvus collection
  - Per-user ACL filter at retrieval query
  - Pre-filter chunks by permissions before the LLM context
  - Forensic audit log (see `adr_020`)

**Per-user data access unclear**

- _Concern_:
  - Unclear whether C\*C enforces per-user access
  - Service account shared key bypasses per-user permissions
  - Risk that user A sees user B's data
  - [GDPR Art. 32](https://gdpr-info.eu/art-32-gdpr/) (security of processing / access control) plus
    [Art. 25](https://gdpr-info.eu/art-25-gdpr/) (privacy by design) violation
- _Direction_:
  - Per-user OAuth for every source connector
  - ACL inheritance into Milvus metadata
  - Retrieval-time filter
  - Documented user access matrix

**Azure stack triple redundancy (DI + Foundry + core MinerU+LiteLLM)**

- _Concern_:
  - C\*C uses Azure Document Intelligence for parsing
  - plus Azure AI Foundry for LLM
  - while core already provides MinerU plus LiteLLM
  - → pay 2x cost (Azure DI plus Foundry tokens plus core infra)
  - **Double sovereignty exposure** (both Azure services outside Switzerland)
  - Parallel maintenance of two stacks
  - Team must master both ecosystems
- _Direction_:
  - **Standardize on the core stack**:
    - MinerU for parsing (per ADR `2026_02_09`)
    - LiteLLM gateway for LLM routing
  - Azure-specific feature → ADR business justification plus deprecation plan
  - Migration roadmap:
    - DI → MinerU
    - Foundry → self-hosted vLLM or Swiss LLM Cloud via LiteLLM

#### Documentation deliverables

- arc42 12 chapters for C\*C
- C4 Level 1 (System Context) plus C4 Level 2 (Container): 4 agents plus 6 pipelines plus custom API plus lib/common
- ADRs answering 13 design questions: Azure Foundry sovereignty; Azure DI vs MinerU; naming camouflage; multi-agent
  orchestrator pattern; custom API extension contribution path; service account vs per-user OAuth; Azure AD B2C vs
  Keycloak; Azure IaC vs Pulumi; dual lock files migration; `switch_dependencies.py` rationale; hardcoded Jira IDs;
  `lib/common` extraction criteria; `RetrievalAgentInTheLoop` import fix
- Technical answers: data quality strategy at ingest; RAG improvement strategy; idempotency solution; Milvus upsert;
  document ACL inheritance; custom API monitoring; DR plan; test coverage plan; large data ingestion strategy; cost
  monitoring Azure Foundry+DI

### 5.4. aihub-Dem\*scope

Evidence base: `aihub-demoscope` repo HEAD `abe968f 2026-01-13`. Linked priority items: §3.4.

#### Concerns

**SDK version drift (44 minors)**

- _Concern_:
  - Drift of 44 minor versions (v0.246.4\* vs core v0.290.4) — 4.5+ months of patches missed (\*SDK pin not present in
    repo `pyproject.toml`; figure carried over from prior snapshot)
  - Coordinated upgrade across 4 deployed agent variants (public/private of persona + multi_personas)
- _Direction_:
  - Confirm actual SDK pin from deploy manifests / CI logs first
  - SDK upgrade plan with security delta audit covering 44 minors
  - CI gate blocking drift > N minors

**Backup destination on the same VM**

- _Concern_:
  - MinIO backup co-located with Milvus/Mongo on the same host
  - VM failure = total loss; violates 3-2-1 rule
  - Recovery currently relies on ad-hoc `backup_updater_script.py`
- _Direction_:
  - Emergency cron sync to Swiss off-site (Infomaniak / Exoscale / Hetzner)
  - Replace ad-hoc script with official `milvus-backup` to off-host bucket

**Pulumi mentioned in README but IaC code NOT committed**

- _Concern_:
  - README documents Pulumi stack initialisation, but no `.iac/` folder exists in the repo
  - Deployment is undocumented and irreproducible from this repo alone
- _Direction_:
  - Commit the actual Pulumi code or remove the README sections
  - Pick one IaC approach (Pulumi vs Terraform) and document end-to-end deployment

**Test coverage ZERO**

- _Concern_:
  - No `test_*.py`, no `.feature` files for 2 agents + 1 pipeline
  - High regression risk on the upcoming 43-minor SDK upgrade
- _Direction_:
  - Baseline smoke test per agent + pipeline
  - BDD `.feature` for hash-partitioned questions flow
  - Integration test against staging Milvus

**Manual SSH+screen+scp migration**

- _Concern_:
  - `scp migrate_questions.py demoscope:aihub/scripts/...` + `screen -r migration` workflow
  - Progress tracked in `migration_log.json` on the VM (not in DB)
  - Fragile, no audit trail
- _Direction_:
  - Replace with Dagster job (preferred) or k8s Job
  - Track migration progress in DB or Dagster runs

**Hash-partitioned Milvus design duplicated in 3 places**

- _Concern_:
  - Same hash function in `lib/common/partition_utils.py`, `persona_agent`, and migration script
  - Drift risk: if any one diverges, all queries miss vectors
- _Direction_:
  - Single source of truth (already partially in `lib/common/partition_utils.py`)
  - CI test asserting agent + pipeline + migration use the same hash

**4 agent variants deployed (public/private of 2 base agents)**

- _Concern_:
  - persona_agent_public / persona_agent_private / multi_personas_agent_public / multi_personas_agent_private
  - Operational surface 2× larger; rationale not documented
- _Direction_:
  - ADR documenting public/private split rationale
  - Verify 4 instances run the same code or merge into 1 binary with config flag

**Stack divergence from core (Mongo + Redis + Phoenix pre-Langfuse)**

- _Concern_:
  - Uses `mongo:8.0.9` + `redis:8.0.1` + `phoenix:version-10.0.4` + `litellm:v1.77.7`
  - Core has migrated to FerretDB + Valkey + Langfuse (ADR `2026_02_10`)
  - Tied to the 43-minor SDK drift
- _Direction_:
  - ADR documenting divergence rationale (or migration plan)
  - Check if Demoscope-specific Mongo features (BSON types, transactions) prevent migration

**Mixed sovereignty (Azure OpenAI SUI + local vLLM)**

- _Concern_:
  - `demoscopeaihub-oai-sui.openai.azure.com` (Azure Switzerland) for some routes
  - Local vLLM (Gemma-3 12b/27b, gte-Qwen2, bge-reranker) for others
  - Mixed position not documented
- _Direction_:
  - ADR documenting partial-sovereignty position
  - Clarify which workloads route to Azure SUI vs local vLLM
  - Tied to Core sovereignty path decision (Option A/B/C)

#### Documentation deliverables

- arc42 12 chapters for Dem\*scope
- C4 Level 1 (System Context) + C4 Level 2 (Container): 2 agent packages (4 deployed variants) + 1 pipeline + custom API
- ADRs answering 9 design questions: stack divergence (Mongo/Redis), hash partition (1000 partitions on `persona_id`),
  4-variant public/private split, sovereignty position (Azure SUI + local vLLM), MinIO same-VM backup, Phoenix →
  Langfuse migration, IaC approach (commit Pulumi or pick Terraform), test strategy, agent-config evolution

### 5.5. aihub-W\*P

Evidence base: `aihub-wpe` repo HEAD `c4b1527 2025-12-18`. `.env.prod` is sensitive-file-guarded; only env-var names
were inspected, not values. Linked priority items: §3.5.

#### Concerns

**TLS private key committed to git**

- _Concern_:
  - `wpe.ai-agents.ch+1-key.pem` and `wpe.ai-agents.ch+1.pem` are tracked in git (only `.env` is in `.gitignore`)
  - Production-domain cert + matching private key visible to anyone with read access on the repo
  - Even if cert is dev/mkcert, the practice is dangerous
- _Direction_:
  - Rotate cert + key **immediately** (re-issue via Traefik + Let's Encrypt)
  - Add `*.pem`, `*-key.pem`, `secrets/` to `.gitignore`
  - Rewrite git history (BFG / `git filter-repo`) to purge the key
  - Audit who pulled the repo since the key was committed

**Manual VM deployment via copy-paste**

- _Concern_:
  - README workflow: `cp docker-compose.latest.yml /opt/docker/config/bbv/docker-compose.latest.yml`
  - No IaC, no rollback, no audit trail, no drift detection
  - Sysadmin `.env` lives in `/opt/bbv/.env` (out of repo)
- _Direction_:
  - Minimum: reproducible deploy script + checksums
  - Better: migrate to Gen 2 (Ansible Pull) or Gen 3 (`aihub-k8s`)

**LLM region not in repo (sovereignty unverified)**

- _Concern_:
  - `AZURE_OPENAI_BASE_URL` only in `.env.prod` (gitignored, sensitive-guarded)
  - Compliance status cannot be reviewed from repo alone
- _Direction_:
  - Commit a non-secret `litellm-region.md` or `.env.example` declaring Azure region
  - ADR aligning with Core sovereignty path

**SDK drift 35 minors + `${CORE_VERSION:-latest}` fallback**

- _Concern_:
  - `.env.prod` pins `CORE_VERSION="v0.255.6"`, but `docker-compose.latest.yml` falls back to `latest` if env var
    missing
  - Reproducible builds require explicit pinning
- _Direction_:
  - Remove `:-latest` default; fail-fast if `CORE_VERSION` unset
  - SDK upgrade plan with security delta audit (35 minors)
  - CI gate blocking drift > N minors
  - Same fallback pattern exists in `aihub-k8s` Helm chart — see proposed `adr_040`

**`VOLUME_ROOT:-./.docker-volumes` defaults to relative dir**

- _Concern_:
  - In production this defaults to a path relative to the current working directory
  - Snapshot/backup paths depend on operator's `pwd` when running `docker compose`
- _Direction_:
  - Force explicit `VOLUME_ROOT` (e.g. `/var/lib/aihub`)
  - Document snapshot strategy

**Off-site backup not in repo**

- _Concern_:
  - No Restic / Swift / cross-region sync configuration visible in repo
  - Unknown if backup exists out-of-repo
- _Direction_:
  - Add backup config to repo (cron + Restic to Swiss off-site)
  - Follow 3-2-1; document RTO/RPO

**No own arc42 + ADRs + no smoke tests**

- _Concern_:
  - Deployment-only repo with no design docs explaining choices
  - No post-deploy validation script
- _Direction_:
  - Minimal arc42 (context + deployment + crosscutting)
  - ADRs for: manual VM choice, identity provider, LLM region, sovereignty position
  - Post-deploy smoke test (curl health endpoints, OAuth round-trip, LiteLLM ping)

#### Documentation deliverables

- arc42 3 chapters for W\*P (Context + Deployment + Crosscutting concepts)
- C4 Level 1 + brief C4 Level 2 (5 ingress hosts via Traefik + 30 containers)
- ADRs answering 6 design questions: TLS key in git (rotation + history rewrite), manual VM deployment, identity
  provider (Azure AD / Entra), LLM region + sovereignty, no own code rationale, backup strategy
- Post-deploy smoke test script (committed to repo)

### 5.6. aihub-F\*H

Evidence base: `aihub-fmh` repo HEAD `5509d39 2026-04-07`. Linked priority items: §3.6.

#### Concerns

**SDK version drift 104 minors (largest of all customers)**

- _Concern_:
  - Drift v0.186.0 vs core v0.290.4 = 104 minor versions
  - 10+ months of security patches missed
  - Cumulative breaking changes likely require multi-step upgrade
- _Direction_:
  - Incremental upgrade plan: v0.186 → v0.220 → v0.260 → v0.290
  - Security delta audit per step
  - CI gate blocking drift > N minors

**LlamaIndex monkey-patch for GPT-5**

- _Concern_:
  - `lib/common/register_openai_models.py` modifies third-party globals
    (`llama_index.llms.openai.utils.ALL_AVAILABLE_MODELS` and `CHAT_MODELS`) at import time
  - Adds `gpt-5-mini` and `gpt-5-nano` because pinned `llama-index-llms-openai ^0.3.x` doesn't know them
  - Supply-chain hygiene concern: behaviour depends on import order; breaks if upstream library changes
- _Direction_:
  - Open PR to `aihub-core` to add first-class GPT-5 model registry
  - SDK upgrade drops this patch automatically
  - Document workaround in ADR until removed

**Azure AI Search instead of Milvus (stack divergence)**

- _Concern_:
  - F\*H uses `mongo_aisearch_storage_context_resources` (Azure AI Search) instead of core Milvus
  - Vendor lock-in: indexer + retrieval coupled to Azure SDK
  - Double inference cost (AI Search query + LLM call)
  - Matches §3.3 C\*C "Azure stack triple redundancy" pattern
- _Direction_:
  - ADR justifying Azure AI Search vs core Milvus
  - Migration plan to Milvus, or formal acceptance of divergence with cost analysis

**Backup status not in repo**

- _Concern_:
  - Pulumi `stores/` deploys infrastructure but no backup workload visible
  - Azure backup policy on `Storage Account` and Cosmos/Mongo not verified from repo
  - Cross-region replication for TARDOC/TARMED handbook data unknown
- _Direction_:
  - Verify Azure backup policy + cross-region replication
  - Restore drill with documented RTO/RPO
  - If backup exists out-of-Pulumi, document where

**Stack divergence (Mongo + Redis + Phoenix pre-Langfuse)**

- _Concern_:
  - Same divergence pattern as Dem\*scope (older core baseline at v0.186.0)
  - Tied to SDK upgrade
- _Direction_:
  - Plan migration Phoenix → Langfuse (ADR `2026_02_10`)
  - Plan MongoDB → FerretDB
  - Tied to SDK upgrade

**Minimal test coverage (5 + 5 BDD)**

- _Concern_:
  - Only 5 `test_*.py` + 5 BDD `.feature` for 3 agents + 2 pipelines
  - Coverage gap on a critical TARMED billing routing flow
- _Direction_:
  - Coverage threshold 60% for new code
  - BDD `.feature` for the 3-agent routing flow (routing → handbook + rules)
  - Integration test against TARMED test fixtures

**Azure vendor lock-in (OpenAI + AI Search + AD + Storage state)**

- _Concern_:
  - Azure OpenAI Switzerland North + Azure AI Search + Azure AD + Pulumi state in Azure storage
  - 4-layer Azure dependency; cross-cloud failover impossible
  - Pulumi state SPOF (single Azure storage account)
- _Direction_:
  - ADR documenting Azure choice rationale (TARDOC/TARMED is Swiss-only data → Switzerland North defensible)
  - Document Pulumi state account name/region in repo; plan state backup
  - Evaluate Keycloak federation as identity alternative

**MS Bot Framework + dev tunnel workflow**

- _Concern_:
  - README references `devtunnel` for local bot dev; risk that prod follows the dev pattern
  - `agents/playground/bot_emulator/fmh-local.bot` referenced from prod docs
- _Direction_:
  - Document the MS Teams integration deployment path explicitly
  - Remove emulator references from prod docs
  - Ensure prod doesn't depend on `devtunnel`

**Hardcoded handbook namespace `handbook_02_2026`**

- _Concern_:
  - Pipeline `handbook_ingestion/__init__.py` hardcodes `CONTAINER_NAME`, `DIRECTORY_NAME`, `NAMESPACE_NAME`,
    `VECTOR_STORE_NAME`, `DOCUMENT_STORE_NAME`
  - New monthly snapshots require code change
- _Direction_:
  - Pydantic Settings from env
  - Allow multiple snapshots in parallel
  - Document the `handbook_MM_YYYY` versioning convention

#### Documentation deliverables

- arc42 12 chapters for F\*H
- C4 Level 1 + C4 Level 2 (3 agents + 2 pipelines + custom API + bot + evaluation framework)
- ADRs answering 9 design questions: Azure AI Search vs Milvus, GPT-5 monkey-patch (workaround + removal path), 3-agent
  routing design (handbook + rules + routing), TARDOC/TARMED data ingestion, MS Bot Framework choice, identity (Azure
  AD), Pulumi state SPOF, evaluation framework rationale, BITL events (DignityCheck / RecognitionCheck)

### 5.7. aihub-Ig\*s

Gen 2 pre-production pilot, deploy-only. Concerns in `Concern → Direction` format (go-live items in §3.7; container view
in [`c4/igs.md`](c4/igs.md)).

**Bot dev-auth in production compose**

- _Concern_: the `bot` service sets `DANGEROUS_DEV_ONLY_AUTH_FAKE_NAME/EMAIL/OID/ROLES` in `docker-compose.latest.yml`;
  a single populated value turns the Teams bot into an unauthenticated, role-spoofing endpoint.
- _Direction_: gate fake-auth behind the `dev` stage; core hard-guard for non-dev; remove `BOT_AUTH_FAKE_*` from the
  vault; CI gate. See proposed `adr_048`.

**Unpinned core images (`:latest`)**

- _Concern_: app images (api/web/bot/agents/pipelines) pull `:latest` → unbounded drift, non-reproducible deploys.
- _Direction_: pin an explicit `CORE_VERSION` tag, fail-fast if unset, CI drift gate (same family as `adr_040`,
  `adr_001`).

**Observability drift (Phoenix vs Langfuse)**

- _Concern_: compose runs Phoenix v10.0.4 (pre-Langfuse) + OTEL→SigNoz Cloud, but `eval/README.md` names Langfuse
  (`langfuse.igs.ai-agents.ch`) as system of record.
- _Direction_: reconcile to a single backend (Langfuse, per ADR `2026_02_10`); add it to the tracked compose/playbook;
  decide SigNoz-region sovereignty. See proposed `adr_049`.

**Sovereignty mixed / unverifiable**

- _Concern_: LiteLLM wired for Azure OpenAI **and** Swiss LLM Cloud (+ Cohere/Gemini/HF); active routing not in repo
  (`litellm-config` supplied by the Gen 2 playbook).
- _Direction_: confirm and document the routing + (partial) sovereignty position; tie to the Core sovereignty path
  (`adr_000`).

**CORS wildcard + missing docs/tests + backup verification**

- _Concern_: `CORS_ALLOW_ORIGIN: "*"` in OpenWebUI; empty `README.md`, no own arc42/ADRs; no unit/integration tests
  (only the Langfuse eval harness); off-site backup not visible in repo.
- _Direction_: restrict CORS to known origins; minimal arc42 + ADRs; post-deploy smoke tests; verify the Gen 2
  `os_backups` Restic→Swift role is active for IGS (`adr_030`).

**Documentation deliverables**: arc42 (context + deployment + crosscutting) + ADRs for the Gen 2 pilot, Docling parser
choice, sovereignty position, Phoenix→Langfuse, and `:latest` pinning. Strengths to preserve: most core-aligned stack
(FerretDB + Valkey + Docling), Swiss LLM Cloud wired, working `Citation Quality` eval harness.

### 5.8. Other customer projects (placeholders pending input)

Remaining customers with no information available yet. Each will get its own §5 subsection (similar to §5.2-§5.7) once
details are provided.

| Customer         | Status placeholder        |
| ---------------- | ------------------------- |
| aihub-Balmer-E\* | TBD - awaiting team input |

**Per-customer info to provide** (each customer):

- Status (production date / pilot / onboarding)
- Core version + drift in minor versions
- Components (number of agents / pipelines / custom APIs / bots)
- Deployment generation (Gen 1 Azure manual / Gen 2 Infomaniak Ansible Pull / Gen 3 `aihub-k8s` / other)
- Data sources (SharePoint / Jira / SMB / custom / etc.)
- LLM provider + sovereignty annotation
- Identity provider (Keycloak / Azure AD / SaaS)
- Off-site backup status
- Own arc42 + ADRs available?
- Test coverage estimate
- Key concerns / blockers specific to the customer
- Migration plan Gen 1 → Gen 2 → Gen 3 (if applicable)

### 5.8. Cross-cutting (Infrastructure, Process, Governance)

#### Concerns

**Infrastructure topology undocumented** _[Resolved for Gen 2]_

- _Concern_:
  - Network zones undocumented
  - Container resource sizing has no matrix
  - Service dependencies unclear
  - IaC not standardized
- _Status_: **Resolved for Gen 2** - aihub-ops/setup README documents OpenStack network zones, security groups, volume
  topology, VM sizing in full. aihub-playbook standardizes via Ansible roles.
- _Direction_: B*D/C*C still need HLAD + network zone diagram for Gen 1; migrate to Gen 2 with the same documentation
  pattern.

**Operations runtime undocumented** _[Resolved for Gen 2]_

- _Concern_:
  - Secret management plus rotation has no procedure
  - TLS certificate lifecycle has no owner
  - Time / locale handling not documented
- _Status_: **Resolved for Gen 2** - Ansible Vault encrypted (AES256) with auto-gen via `vault-vars-routing.yml`;
  Traefik + Let's Encrypt ACME handles cert lifecycle (acme_email config); ops runbook in aihub-ops/setup README and
  aihub-playbook AGENTS.md.
- _Direction_: B*D/C*C need to migrate to Gen 2 pattern; deploy key rotation policy should be explicit (current
  AGENTS.md is vague - "periodically"); time/locale standardization for Gen 2 still pending.

**Supply chain visibility missing** _[Open]_

- _Concern_:
  - No SBOM
  - No image signing
  - No vuln scanning
  - No log aggregation topology
- _Status_: Log aggregation **partial fix** via SigNoz OTEL collector (Gen 2); SBOM/signing/vuln scan still missing.
- _Direction_:
  - syft (SBOM generation)
  - cosign (image signing)
  - trivy (vuln scan)
  - All integrated in CI

**Off-site backup strategy** _[Partial fix for Gen 2]_

- _Concern_:
  - Both B*D and C*C back up on the same VM
  - Violates the 3-2-1 rule
  - Hardware failure = total loss
- _Status_: **Partial fix for Gen 2** - Restic backs up to OpenStack Swift container (`vol-backup`) achieving the
  "off-host" component of 3-2-1; retention policy documented (24h/7d/4w/12m/7y); restore tested via
  `restore-restic-backup.sh`. **Still missing**: cross-provider replication (Swift on same Infomaniak as primary VM).
- _Direction_:
  - **B*D/C*C**: migrate to Gen 2 (urgent) - emergency cron sync to Swiss-sovereign off-site
  - **Gen 2 enhancement**: cross-provider tier (Infomaniak Swift → Hetzner / Exoscale / bare-metal secondary)
  - Reference: `adr_030_offsite_backup_replication.md`

**No RTO/RPO documented and no DR drill**

- _Concern_:
  - Recovery objectives undefined
  - No automated restore drill
  - DR capability unverified
- _Direction_:
  - Document RTO/RPO per service tier
  - Monthly automated DR drill
  - Restore verification in CI

**No K8s migration path**

- _Concern_:
  - Docker Compose single-server ceiling
  - No Helm chart
  - No StatefulSet pattern for stateful services
- _Direction_:
  - K8s migration plan
  - Helm chart for every service
  - StatefulSets for the data layer
  - HPA for stateless services

**No customer onboarding template** _[Resolved for Gen 2 deployment]_

- _Concern_:
  - New customers must reinvent arc42
  - Reinvent ADRs
  - Reinvent deployment scripts
  - Spend weeks on structure before building features
- _Status_: **Deployment template resolved** via `setup-aihub.sh` + 3-repo pattern (aihub-playbook + aihub-core +
  aihub-\{customer_id}); automated VM provisioning on OpenStack; SSH deploy keys + Ansible Vault auto-setup. **Docs
  template (arc42 + ADRs) still missing**.
- _Direction_:
  - arc42 12 chapters skeleton template (still missing)
  - ADR list (required decisions) template
  - Customer repo structure docs for aihub-\{customer_id}

**No SDK versioning policy**

- _Concern_:
  - No max version-drift policy
  - No security patch SLA
  - No CI gate blocking outdated customers
  - No breaking change communication
- _Direction_:
  - Formal SDK versioning policy document
  - CI gate (block PR if drift > N versions)
  - Documented security patch SLA (e.g., critical = 7 days)

**No documentation gate before go-production**

- _Concern_:
  - Customer launches don't require arc42
  - Don't require ADRs
  - No sign-off checklist
  - Doc gaps only surface at audit time
- _Direction_:
  - Documentation gate in the release process
  - Required artifacts list
  - Sign-off matrix per stakeholder

**No ADR compliance audit process**

- _Concern_:
  - Major architectural decisions don't require an ADR before merge
  - Architecture drifts over time
  - False claim risk
- _Direction_:
  - ADR compliance gate in PR workflow
  - Lint rule checking an ADR exists when an architecture path is touched

**No documentation drift detection** _[Partial fix for env vars]_

- _Concern_:
  - Doc claims don't match code (Presidio, GDPR examples)
  - Discovered late at audit time
- _Status_: **Partial fix** - `check_env_drift.py` + nightly GitHub Actions workflow (`vault-vars-routing-drift.yml`)
  detect env vars drift between aihub-core `.env.template` and aihub-ops `vault-vars-routing.yml`. **Only covers env
  vars**, doesn't cover prose docs claims.
- _Direction_:
  - Extend drift detection to docs claims (Presidio, GDPR, audit log)
  - Claim parser plus code grep cross-check
  - Fail the build if a claim cannot be verified

**No customer-facing SLA**

- _Concern_:
  - No formal Service Level Agreement for customers
  - Uptime commitment undefined (e.g., 99.5% / 99.9% / 99.95%)
  - Response time guarantees per endpoint class missing (chat / RAG query / ingest)
  - Incident response time per severity missing
  - Scheduled maintenance window policy missing
  - Downtime credit / refund policy missing
  - When a customer hits an outage there is no baseline to measure breach
  - SLA not linked to HA architecture (99.9% requires HA stack, 99.95% requires multi-AZ)
- _Direction_:
  - **Define SLA tiers per customer plan** (e.g., Bronze 99.0% / Silver 99.5% / Gold 99.9%):
    - Uptime commitment per tier
    - Response time per endpoint class
    - Support response time per severity
    - Credit / refund policy
  - **Map tier → infrastructure requirement**:
    - Bronze - single-VM
    - Silver - HA single-AZ
    - Gold - multi-AZ K8s
  - Link RTO/RPO matrix to SLA targets
  - Public status page (statuspage.io / Atlassian Statuspage / self-hosted Cachet)
  - Automated monthly SLA report driven by the observability stack

#### Gen 2 deployment pattern (Ansible Pull / OpenStack)

**3-repo coordination version compatibility**

- _Concern_:
  - 3 repos must sync state: `aihub-playbook` (infra) + `aihub-core` (apps) + `aihub-{customer}` (secrets)
  - If `aihub-core` upgrades with breaking changes but `aihub-playbook` is not updated → next Ansible Pull (15 min
    later) breaks the VM
  - Similarly: customer vault schema change → playbook doesn't handle = deployment fails
  - No compatibility matrix today; no CI gate testing combinations
- _Direction_:
  - **Documented version compatibility matrix** (e.g., playbook v1.5+ supports core v0.280-v0.290)
  - **CI integration test** spawning an ephemeral VM with a combination (playbook + core + customer template) to
    validate
  - **Pin core version** in playbook config (instead of always `latest`)
  - Release coordination: breaking change in core → playbook PR in the same release cycle

**GitHub as deployment SPOF**

- _Concern_:
  - VMs fetch the aihub-core release archive via the GitHub REST API every 15 min
  - AGENTS.md confirms: "no local fallback if api.github.com is unreachable - sustained GitHub outages block deploys"
  - `GHCR_TOKEN` requires both scopes (`read:packages` + `contents:read`); a fine-grained PAT missing one will fail
  - GitHub rate limit (5000 req/hour authenticated) - N customers × 4 pulls/hour = N×4 requests/customer
- _Direction_:
  - **Local mirror / private registry fallback** for release tarballs
  - Cache release tarballs locally on the VM (only pull when version changes)
  - Document GitHub dependency in the DR plan
  - Monitor rate limit usage; consider a GitHub Enterprise mirror at scale

**Same-cloud backup (Restic → Swift on same Infomaniak)**

- _Concern_:
  - Primary VM on Infomaniak OpenStack
  - Restic backup → Swift on same Infomaniak
  - Infomaniak region outage / account suspension / billing issue = loses both
  - Achieves off-host in 3-2-1 rule but **not off-site / off-provider**
- _Direction_:
  - **Cross-provider tier** (Tier 2 in adr_030):
    - Primary: Infomaniak Swift
    - Secondary: Hetzner Storage Box / Exoscale Object Store / Backblaze B2 / bare-metal NAS
  - Rclone job replicates Swift → secondary daily
  - Document cloud-provider-failure scenario in the DR runbook

**Ansible Pull 15-min cadence for hot-fix**

- _Concern_:
  - Security patch pushed to main = wait up to 15 min before VMs apply
  - During an outage requires manual `systemctl start infra-pull.service` per VM
  - N customers = N SSH sessions for emergency deploy
  - No centralized emergency trigger
- _Direction_:
  - **Emergency push mechanism**:
    - Webhook trigger from GitHub Actions after a security release
    - Or NATS broadcast subject `aihub.infra.emergency-pull` → VMs subscribe and trigger immediately
    - Or central SSH fan-out script
  - Document emergency deploy SLA (e.g., P0 security patch deployed < 5 min from release)
  - Manual override procedure in the incident response runbook

**SigNoz Cloud data sovereignty**

- _Concern_:
  - SigNoz collector role defaults to `signoz_region: "eu"` - ships observability data to SigNoz Cloud (EU region)
  - Observability data may contain: user IDs, tenant identifiers, prompt fragments in traces, error messages containing
    PII
  - Swiss customer data → leaves tenant infra → contradicts the sovereignty story when serving regulated industries
  - SigNoz Cloud has no Swiss region (only US / EU / India)
- _Direction_:
  - **Self-hosted SigNoz** alternative (full stack: query service + clickhouse + collector in a Swiss VM)
  - Or **Grafana Cloud EU region** with data residency guarantees
  - Or self-hosted **Loki + Tempo + Mimir** stack
  - Document trace data sanitization: redact PII / user IDs before export
  - Dedicated ADR for the observability data sovereignty trade-off

**Vault password storage on VM**

- _Concern_:
  - Ansible Vault password stored on the VM filesystem (needed to decrypt on every pull)
  - VM compromise = full vault unlock = leaks every secret (API keys, DB passwords, OAuth secrets, SUPERUSER_TOKEN)
  - VM snapshot exposure = vault password inside the snapshot
  - No short-lived token / HSM-backed pattern
- _Direction_:
  - **HSM / KMS-backed vault password**:
    - OpenStack Barbican (key management service) - fetched at boot
    - Or Azure Key Vault / HashiCorp Vault retrieval at boot
  - **Short-lived decryption token** (e.g., 1 hour TTL, auto-refresh)
  - Audit log access to the vault password
  - VM snapshot encryption with a separate key (not stored on the VM)

**B*D/C*C migration Gen 1 → Gen 2**

- _Concern_:
  - B*D/C*C still on Gen 1 (Azure VM + manual shell scripts)
  - Backup still has the fatal pattern (same VM)
  - Security patches don't auto-deploy
  - Customer Registry shows discrepancy with Customer #3+ (Gen 2)
  - Migration path undocumented; risk that migration breaks customer running production
- _Direction_:
  - **Documented migration playbook**:
    - Phase 1: Provision Gen 2 VM on Infomaniak (parallel to Gen 1 Azure)
    - Phase 2: Data migration (volume snapshot → restore on Gen 2)
    - Phase 3: DNS cutover with rollback plan
    - Phase 4: Decommission Gen 1
  - **Pilot migration** with B*D (smaller surface area) before C*C
  - Customer communication: SLA window, downtime expectation, rollback guarantee
  - Skill transfer for the customer ops team (Azure portal → Infomaniak OpenStack)

**Deploy key rotation policy implicit**

- _Concern_:
  - AGENTS.md mentions "Rotate deploy keys and vault passwords periodically" but:
    - No concrete period (quarterly? yearly?)
    - No automation script
    - No audit log "key X rotated on date Y"
    - 3 deploy keys per VM (playbook + core + customer) → manual rotation is complex
  - A compromised key may go undetected
- _Direction_:
  - **Formal rotation policy** (e.g., quarterly for deploy keys, monthly for vault passwords)
  - **Automation script**:
    - Generate a new key
    - Push to the repo via GitHub API
    - Push via `setup-aihub.sh` re-run to the VM
    - Revoke the old key
    - Log the rotation event
  - Audit dashboard: key age, last rotation date per VM
  - Alert if a key has not been rotated for > X months

**AI evaluation framework (Core/B*D/C*C)** _[Strategic]_

- _Concern_: When the eval dataset for RAG/agents produces poor results, the team's approach is to **tweak the prompt
  and retry** → local optimization, doesn't address root causes.
- _Impact_: Prompt tuning isn't transferable when changing models; no systematic A/B; no regression detection; can't
  distinguish retrieval miss vs weak generation.
- _Direction_: **Multi-lever framework** instead of prompt-only - **Retrieval** (BGE-M3 tuning, hybrid dense plus BM25,
  query rewriting, BGE reranker); **Chunking** (semantic, parent-document, metadata enrichment); **Context** (top-k
  tuning, context compression); **Generation** (model routing easy→cheap hard→strong, few-shot, CoT); **Eval loop**
  (Langfuse datasets plus RAGAS metrics faithfulness/relevancy/context-precision, automated LLM-as-judge, regression
  test on PR); **Fine-tuning/DPO** when prompt plus retrieval hit the ceiling. **Every tweak measured against the eval
  dataset, not by intuition.**

#### Documentation deliverables

- Customer onboarding template (arc42 plus ADRs plus deployment scripts)
- Formal SDK versioning policy document
- Documentation gate checklist
- ADR compliance gate procedure
- Documentation drift detection CI workflow
- Multi-customer pattern extraction roadmap

______________________________________________________________________

## 6. Recommendations

> High-level direction. Detailed implementation, cost, ownership will be deep-dived in subsequent sessions.

### 6.1. Immediate decisions

- **Sovereignty decision**: choose Option A (self-hosted local LLM) / B (hybrid with updated ADR) / C (per-customer
  tier)
- **Review "Swiss Sovereign AI" marketing positioning** — note: this claim does not yet fully align with reality
  (B*D/C*C use Azure for LLM); consider softening the wording or clarifying scope until the sovereignty path decision is
  finalized
- **Backup Tier 1 emergency mitigation**: cron sync to Swiss-sovereign off-site target (Infomaniak/Exoscale CH)
- **Wire UsageLimits middleware**: block LLM cost runaway risk
- **Decide `packages/process` fate**: delete or activate
- **Security delta audit** from each customer's pinned version (B*D v0.279.2, C*C v0.274.3, W*P v0.255.6, Dem*scope
  v0.246.4\*, F\*H v0.186.0) → current core v0.290.4, force-upgrade customers if security patches exist (\*Demoscope SDK
  pin unverified from repo, see footnote in §Component versions)
- **Dem\*scope remediate-vs-rebuild**: decide whether to upgrade the very-old pin in place (agent crashes on start) or
  rebuild on the current core generation; and **formally accept the customer-owned backup / key-renewal risk** (RACI
  sign-off)
- **F\*H answer quality**: approve the RAG/vector re-design for structured data and the AI-Search-vs-Milvus decision
  (`adr_039`, `adr_044`)
- **Adopt standing gates**: the RAG/vector-design gate (`adr_044`) and a continuous component-update strategy
  (`adr_043`)

### 6.2. Strategic priorities

- **Multi-tenant data layer**: NATS namespace, Mongo `tenant_id`, Milvus per-tenant collection, Valkey key prefix
- **Security hardening**: SecureMCPExecutor, Document ACL inheritance, audit log entity, service-to-service mTLS
- **Per-user OAuth** for Jira/SharePoint/Confluence connectors (replace service account shared keys)
- **K8s migration**: Helm chart, StatefulSets for stateful services, HPA for stateless
- **Milvus cluster mode**: prepare for multi-customer scale
- **DB migration framework**: versioned scripts for upgrade safety
- **Off-site backup full**: Tier 2 configurable target + Tier 3 Dagster cross-region replication
- **Observability stack**: Prometheus + AlertManager + dashboards + SLI/SLO
- **Third-party penetration test** after security hardening is complete
- **Component replaceability / continuous-update strategy**: ports & adapters for the swappable building blocks
  (document parser, vector store, OCR — LLM is already provider-agnostic via LiteLLM) + Renovate + eval-gated upgrades +
  a named fallback for commercial/EOL libraries. Generalises the MinerU→Docling case (`adr_042`, `adr_043`)
- **Reduce per-customer upgrade pain**: the single-tenant-per-deployment model makes every customer upgrade bespoke and
  expensive — the multi-tenant data layer + a formal SDK versioning policy are the structural fix

### 6.3. Documentation deliverables (team owners required)

- **Core platform**: HLAD, C4 L1/L2, update false-claim docs, audit log + GDPR ADRs
- **Customer aihub-b\*d**: arc42 12 chapters, C4 L1/L2, 10 ADRs answering design questions
- **Customer aihub-c\*c**: arc42 12 chapters, C4 L1/L2, 13 ADRs answering design questions, technical questions
- **Infrastructure**: deployment topology + operations runtime + observability/supply chain
- **Customer onboarding template** for new customers

### 6.4. Process and governance

- **Formal SDK versioning policy** (max drift, security patch SLA, CI gate)
- **Documentation gate** before customer go-production (sign-off checklist)
- **ADR compliance gate** in development workflow (major decision = required ADR)
- **Documentation drift detection** in CI (catch claims that don't match code)
- **Pattern extraction roadmap**: customer patterns → core (multi-agent orchestrator, industry connectors)
- **Design/analysis gate before implementation**: require a short design artefact — especially vector-DB
  chunking/schema/index tuning + an eval plan — before coding. This process gap is the root cause of the
  F\*H/Dem\*scope/W\*P quality & performance issues (`adr_044`)
- **Load-test baselines**: establish per-project + core baselines (Locust) and run them on a cadence; prerequisite for
  SLI/SLO and for diagnosing the W\*P performance complaint (`adr_046`)

______________________________________________________________________

## References and Standards

This document references the following frameworks, standards, and regulations:

### Architecture frameworks

- **Well-Architected Framework**:
  - Azure: https://learn.microsoft.com/en-us/azure/well-architected/
  - AWS: https://aws.amazon.com/architecture/well-architected/
  - Google Cloud: https://cloud.google.com/architecture/framework
- **AWS SaaS Lens** (multi-tenancy patterns): https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/
- **arc42 documentation template**: https://arc42.org/
- **C4 Model** (Simon Brown): https://c4model.com/
- **CNCF Cloud Native Maturity Model**: https://maturitymodel.cncf.io/
- **Hexagonal Architecture (Ports & Adapters)** - Alistair Cockburn:
  https://alistair.cockburn.us/hexagonal-architecture/
- **ADR (Architecture Decision Records)** - Michael Nygard:
  https://github.com/joelparkerhenderson/architecture-decision-record

### Backup / DR / Resilience

- **3-2-1 Backup Rule** - US-CERT / CISA: https://www.cisa.gov/news-events/news/data-backup-options
- **3-2-1-1-0 (modern anti-ransomware variant)** - Veeam: https://www.veeam.com/blog/321-backup-rule.html
- **ISO 22301 Business Continuity Management**: https://www.iso.org/standard/75106.html
- **Site Reliability Engineering (SLO/SLI/SLA)** - Google SRE: https://sre.google/sre-book/service-level-objectives/

### Security

- **STRIDE threat model** - Microsoft:
  https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats
- **OWASP Top 10 for LLM Applications**: https://genai.owasp.org/llm-top-10/
- **OWASP Top 10 (Web)**: https://owasp.org/www-project-top-ten/
- **SLSA (Supply-chain Levels for Software Artifacts)**: https://slsa.dev/
- **SBOM (Software Bill of Materials)** - CISA: https://www.cisa.gov/sbom
- **CycloneDX SBOM standard**: https://cyclonedx.org/
- **mTLS / Zero Trust** - NIST SP 800-207: https://csrc.nist.gov/publications/detail/sp/800-207/final

### Compliance / Privacy

- **GDPR** - EU General Data Protection Regulation: https://gdpr-info.eu/
  - Art. 17 (right to erasure): https://gdpr-info.eu/art-17-gdpr/
  - Art. 25 (privacy by design): https://gdpr-info.eu/art-25-gdpr/
  - Art. 30 (records of processing): https://gdpr-info.eu/art-30-gdpr/
  - Art. 32 (security of processing): https://gdpr-info.eu/art-32-gdpr/
- **Swiss revDSG** (Federal Data Protection Act, revised 2023): https://www.fedlex.admin.ch/eli/cc/2022/491/de
- **Schrems II ruling** (CJEU Case C-311/18, 2020):
  https://curia.europa.eu/juris/document/document.jsf?docid=228677&doclang=EN
- **US Cloud Act** (2018): https://www.congress.gov/bill/115th-congress/house-bill/4943
- **ISO/IEC 27001** (Information Security Management): https://www.iso.org/standard/27001
- **ISO/IEC 27040** (Storage Security): https://www.iso.org/standard/80194.html
- **SOC 2 Trust Services Criteria** - AICPA:
  https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2

### Quality / Process

- **ISO/IEC 25010** (Software Product Quality): https://iso25000.com/index.php/en/iso-25000-standards/iso-25010
- **Conventional Commits 1.0.0**: https://www.conventionalcommits.org/

### AI / RAG evaluation

- **RAGAS metrics** (RAG evaluation framework): https://docs.ragas.io/
- **Langfuse LLM observability**: https://langfuse.com/docs

### Tools referenced

- **syft (SBOM generator)**: https://github.com/anchore/syft
- **cosign (image signing)**: https://github.com/sigstore/cosign
- **trivy (vulnerability scanner)**: https://github.com/aquasecurity/trivy
- **Presidio (Microsoft PII detection)**: https://microsoft.github.io/presidio/
- **LiteLLM (LLM gateway)**: https://docs.litellm.ai/
- **tree-sitter (AST parser)**: https://tree-sitter.github.io/tree-sitter/

### Gen 3 Kubernetes deployment stack (aihub-k8s)

- **Kubernetes**: https://kubernetes.io/docs/
- **Helm 3** (chart packaging): https://helm.sh/docs/
- **Terraform** (multi-cloud IaC): https://developer.hashicorp.com/terraform/docs
- **Azure AKS** (managed Kubernetes): https://learn.microsoft.com/en-us/azure/aks/
- **OpenStack Magnum** (Container Infra; used on Stoney cloud): https://docs.openstack.org/magnum/latest/
- **CloudNativePG** (PostgreSQL operator): https://cloudnative-pg.io/documentation/current/
- **Keycloak Operator**: https://www.keycloak.org/operator/installation
- **cert-manager** (TLS certificate automation in K8s): https://cert-manager.io/docs/
- **NGINX Ingress Controller**: https://kubernetes.github.io/ingress-nginx/
- **External Secrets Operator**: https://external-secrets.io/latest/
- **SeaweedFS Helm chart**: https://github.com/seaweedfs/seaweedfs/tree/master/k8s/charts
- **Milvus Helm chart (Zilliztech)**: https://github.com/zilliztech/milvus-helm

### Customer-specific technologies (referenced in §3.4-§3.6)

- **Azure AI Search** (F\*H vector backend; alternative to Milvus): https://learn.microsoft.com/en-us/azure/search/
- **Azure Data Lake Storage Gen2** (F\*H source storage):
  https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction
- **Microsoft Bot Framework** (F\*H bot integration): https://learn.microsoft.com/en-us/azure/bot-service/
- **TARDOC** (Swiss outpatient tariff): https://www.tarmed-suisse.ch/tardoc.html
- **TARMED** (Swiss medical billing tariff, predecessor): https://www.tarmed-suisse.ch/
- **vLLM** (high-throughput LLM serving; Dem\*scope local stack): https://docs.vllm.ai/en/latest/
- **LlamaIndex** (RAG framework; F\*H monkey-patches it for GPT-5): https://docs.llamaindex.ai/
- **Pulumi** (IaC framework; ADR `2024_12_18`; F\*H committed code; Dem\*scope README-only):
  https://www.pulumi.com/docs/
- **mkcert** (locally-trusted dev certs; relevant to W\*P `wpe.ai-agents.ch+1*.pem` audit):
  https://github.com/FiloSottile/mkcert
- **BFG Repo-Cleaner** (history rewrite to purge committed secrets; relevant to W\*P §3.5 item #1):
  https://rtyley.github.io/bfg-repo-cleaner/
- **git-filter-repo** (alternative history rewrite tool): https://github.com/newren/git-filter-repo

### Gen 2 deployment stack

- **Ansible**: https://docs.ansible.com/
- **Ansible Pull mode**: https://docs.ansible.com/ansible/latest/cli/ansible-pull.html
- **Ansible Vault**: https://docs.ansible.com/ansible/latest/vault_guide/index.html
- **Ansible Lint**: https://ansible-lint.readthedocs.io/
- **Cloud-init**: https://cloudinit.readthedocs.io/
- **OpenStack documentation**: https://docs.openstack.org/
- **OpenStack Swift (Object Storage)**: https://docs.openstack.org/swift/latest/
- **OpenStack Barbican (Key Management)**: https://docs.openstack.org/barbican/latest/
- **Infomaniak Public Cloud**: https://docs.infomaniak.cloud/
- **Traefik (reverse proxy)**: https://doc.traefik.io/traefik/
- **Let's Encrypt ACME**: https://letsencrypt.org/docs/
- **Restic (encrypted backup)**: https://restic.readthedocs.io/
- **SigNoz (OpenTelemetry observability)**: https://signoz.io/docs/
- **arillso.restic Ansible role**: https://github.com/arillso/ansible.restic
- **systemd timers**: https://www.freedesktop.org/software/systemd/man/systemd.timer.html

______________________________________________________________________

**Document type**: Overview (for stakeholders)

[^1]: Demoscope SDK pin not present in `aihub-demoscope/pyproject.toml`; no `swiss-ai-hub-*` git dependency declared and
    docker-compose images carry no version tag. The `v0.246.4` figure is carried over from the previous review
    snapshot pending operational confirmation (CI logs / deploy manifests).
