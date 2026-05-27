# Architecture Review: Overview

**Loại document**: Executive Summary cho stakeholders.

**Đối tượng đọc**: C-level, Product, Business, Compliance/Legal, Architects, Technical Leads.

**Phạm vi**: Swiss AI Hub ecosystem gồm:

- `aihub-core` - platform application stack
- **Customer deployments**:
  - `aihub-b*d`, `aihub-c*c` - Gen 1 (Azure VM + shell scripts), đã production
  - `aihub-Ig*s`, `aihub-Dem*scope`, `aihub-W*P`, `aihub-Balmer-E*` - TBD (deployment generation, version, status
    pending team input)
- **Infrastructure repos (Gen 2)**:
  - `aihub-playbook` - Ansible Pull infrastructure-as-code (every 15-min reconcile)
  - `aihub-ops` - VM provisioning automation cho OpenStack (cloud-init + setup script)
  - `aihub-{customer_id}` - per-customer encrypted secrets + custom config repos (template pattern)

Cấu trúc extensible cho customer projects bổ sung.

**Mục tiêu document**:

1. **Đánh giá high-level architecture hiện tại** theo các tiêu chuẩn production cho enterprise / multi-customer
   (10-pillar framework, [WAF](https://learn.microsoft.com/en-us/azure/well-architected/),
   [STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats),
   [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/), [CNCF maturity](https://maturitymodel.cncf.io/),
   [GDPR](https://gdpr-info.eu/) cộng [revDSG](https://www.fedlex.admin.ch/eli/cc/2022/491/de)). Chi tiết references ở
   cuối document.
2. **List các concerns** đang chặn hoặc làm chậm production readiness, mỗi concern có `What → How → Direction` rõ ràng.
3. **Đề xuất high-level recommendations** để team planning improvement roadmap.

**Document không làm**:

- Không prescribe chi tiết implementation (sẽ deep-dive ở ADRs riêng và planning sessions).
- Không là gate / NO-GO verdict cuối cùng - là **input** cho roadmap quyết định improvement priorities.
- Không cover code review chi tiết hay performance benchmark cụ thể.

## Phiên bản các thành phần

| Thành phần                  | Version        | Ghi chú                                                                              |
| --------------------------- | -------------- | ------------------------------------------------------------------------------------ |
| aihub-core (HEAD on `main`) | v0.289.10      | Application stack - Latest dev                                                       |
| aihub-b\*d dùng core        | v0.279.2       | Customer Gen 1 - Azure VM + shell scripts, đi sau core 10 minor                      |
| aihub-c\*c dùng core        | v0.274.3       | Customer Gen 1 - Azure VM + shell scripts, đi sau core 15 minor, đi sau b\*d 5 minor |
| aihub-Ig\*s                 | TBD            | Customer - chi tiết version + deployment gen pending                                 |
| aihub-W\*P                  | TBD            | Customer - chi tiết version + deployment gen pending                                 |
| aihub-Dem\*scope            | TBD            | Customer - chi tiết version + deployment gen pending                                 |
| aihub-Balmer-E\*            | TBD            | Customer - chi tiết version + deployment gen pending                                 |
| aihub-playbook              | HEAD on `main` | Infra Gen 2 - Ansible Pull (every 15 min), 3-repo coordination                       |
| aihub-ops                   | HEAD on `main` | VM provisioning automation (OpenStack Infomaniak)                                    |
| aihub-\{customer_id}        | per-customer   | Encrypted Ansible Vault + custom config (template repo pattern)                      |

Cảnh báo:

- 2 existing customers (B*D/C*C) chạy 2 phiên bản SDK khác nhau, đều cũ hơn core. Không có policy ép upgrade.
- Security patches trên `main` không tự lan xuống Gen 1 customers; Gen 2 (Ansible Pull) auto-deploy trong 15 min.
- B*D/C*C migration path từ Gen 1 (Azure manual) sang Gen 2 (Infomaniak OpenStack + Ansible) chưa documented.

______________________________________________________________________

## Mục lục

1. [Tóm tắt](#1-t%C3%B3m-t%E1%BA%AFt)
2. [Sơ đồ hệ sinh thái](#2-s%C6%A1-%C4%91%E1%BB%93-h%E1%BB%87-sinh-th%C3%A1i)
3. [Priority items cho go-live (CRITICAL + HIGH)](#3-priority-items-cho-go-live-critical--high) 3.1.
   [aihub-core (Platform)](#31-aihub-core-platform) 3.2. [aihub-b\*d](#32-aihub-bd) 3.3. [aihub-c\*c](#33-aihub-cc)
4. [Đánh giá](#4-%C4%91%C3%A1nh-gi%C3%A1) 4.1. [Theo khung 10 pillars](#41-theo-khung-10-pillars) 4.2.
   [Business core values vs thực tế](#42-business-core-values-vs-th%E1%BB%B1c-t%E1%BA%BF)
5. [Concerns và Documentation Backlog](#5-concerns-v%C3%A0-documentation-backlog)
6. [Recommendations](#6-recommendations)

______________________________________________________________________

## 1. Tóm tắt

**Mục đích section này**: đưa ra picture tổng quan strengths cộng weaknesses của platform để stakeholder nắm nhanh trước
khi đi vào chi tiết §3 đến §6.

| Strengths                                                                                                                                                                                                         | Weaknesses                                                                                                                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event-driven architecture (NATS JetStream cộng Swiss AI Agent Protocol)                                                                                                                                           | Sovereignty violation - B*D/C*C dùng Azure OpenAI/Foundry, vi phạm ADR `2026_02_24`                                                                                  |
| 45 ADRs document major decisions                                                                                                                                                                                  | Gen 1 customer backup destination cùng VM (vi phạm [3-2-1 rule](https://www.cisa.gov/news-events/news/data-backup-options)); Gen 2 partial fix qua Restic→Swift      |
| OpenTelemetry observability stack (traces cross-service)                                                                                                                                                          | No HA architecture - mọi stateful service single-instance (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd)                                                              |
| Agent framework support common enterprise AI patterns (conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution sandbox, browser automation) | AI use case scope chưa documented trong ADR, claim coverage không defensible cho audit; vision / predictive analytics / fine-tuning out of scope nhưng chưa explicit |
| CI/CD đầy đủ (lint, semantic-pr, build per package)                                                                                                                                                               | UsageLimits class defined nhưng không enforce → LLM cost runaway risk                                                                                                |
| Hierarchical permission template cộng AccessChecker tenant-ceiling (BDD tested)                                                                                                                                   | AuditLogEntity missing, GDPR right-to-erasure không implementable, false docs claims                                                                                 |
| LiteLLM gateway abstract LLM provider (swap dễ)                                                                                                                                                                   | Customer SDK drift lớn - B*D 10 minors, C*C 15 minors, no versioning policy                                                                                          |
| Dagster pipeline orchestration với asset lineage                                                                                                                                                                  | No customer-facing SLA, no alerting infra; chỉ có Slack notification on Ansible Pull failure                                                                         |
| License compliance OK (402 Python + 993 npm + 33 Docker images approved)                                                                                                                                          | Single-server ceiling (Docker Compose only, no K8s, no horizontal scale)                                                                                             |
| 45 ADRs cộng existing arc42 chapters cho platform                                                                                                                                                                 | Customer docs gap - B*D/C*C không có arc42 cộng ADRs riêng                                                                                                           |
| Hierarchical scoping protocol (Thread → Display → Run)                                                                                                                                                            | Connector framework thiếu - mỗi customer tự build (O(N×M) onboarding cost)                                                                                           |
| Multi-language i18n cho UI (DE/EN/FR/IT)                                                                                                                                                                          | Presidio chỉ DE, multilingual PII gap cho Swiss FR/IT/EN                                                                                                             |
| **Gen 2 deployment: Ansible Pull self-configuring VMs (15-min auto-reconcile)**                                                                                                                                   | B*D/C*C vẫn Gen 1 (Azure manual) - chưa có migration plan sang Gen 2                                                                                                 |
| **Infomaniak OpenStack - Swiss-sovereign cloud cho Gen 2**                                                                                                                                                        | Restic → Swift cùng cloud provider Infomaniak; chưa cross-provider replication                                                                                       |
| **3-repo coordination pattern (playbook/core/customer) - separation of concerns**                                                                                                                                 | 3-repo version compatibility chưa có matrix / CI gate test combos                                                                                                    |
| **Customer onboarding template (`setup-aihub.sh`)** automated VM provisioning                                                                                                                                     | Ansible Pull 15-min cadence chậm cho hot-fix; GitHub dependency = deploy SPOF                                                                                        |
| **Ansible Vault encrypted secrets + auto-gen random via vault-vars-routing.yml**                                                                                                                                  | Vault password stored on VM filesystem - VM compromise = full unlock                                                                                                 |
| **Traefik + Let's Encrypt ACME** tự động SSL cert lifecycle                                                                                                                                                       | Deploy key rotation policy implicit ("periodically"), không automation / audit                                                                                       |
| **SigNoz OTEL collector role** (host metrics + OTLP traces + journald)                                                                                                                                            | SigNoz Cloud region "eu" - chưa rõ data sovereignty implication                                                                                                      |
| **Env vars drift detection CI** (`check_env_drift.py` nightly)                                                                                                                                                    | Drift check chỉ cho env vars, không cover docs claims                                                                                                                |
| Langfuse cost tracking per LLM call                                                                                                                                                                               | No per-tenant cost attribution → showback impossible                                                                                                                 |
| Open-source self-hosted positioning                                                                                                                                                                               | Open-source dependency lock-in (parser/embedding/reranker/vector store chưa abstraction)                                                                             |
| BDD test integration với real NATS                                                                                                                                                                                | Test coverage zero ở C*C, 59 lines ở B*D                                                                                                                             |
| Trace context propagate qua NATS message headers                                                                                                                                                                  | Bot scope không OTEL → trace gãy ở bot boundary                                                                                                                      |
| Pulumi IaC defined cho core (superseded by Ansible Pull cho Gen 2)                                                                                                                                                | No K8s migration path (no Helm chart, no StatefulSets)                                                                                                               |

**Next steps**

1. §3 - priority items CRITICAL + HIGH cho go-live (3 tables Core/B*D/C*C).
2. §4 - chi tiết đánh giá 10 pillars (table format) cộng business values vs reality.
3. §5 - list từng concern theo format `Concern → Direction` (tactical) hoặc trade-off block (strategic).
4. §6 - high-level recommendations grouped Immediate / Strategic / Documentation / Process.
5. Team dùng document này làm input cho improvement roadmap.

______________________________________________________________________

## 2. Sơ đồ hệ sinh thái

```mermaid
flowchart TB
    subgraph CORE["Swiss AI Hub Core (aihub-core v0.289.10)"]
        direction TB
        CorePkgs["packages/<br/>core • agent • api • pipeline<br/>bot • backup • web • process"]
        CoreADR["45 ADRs"]
        CoreInfra["30+ containers<br/>per deployment"]
    end

    subgraph B*D["aihub-b*d v0.279.2 (drift 10 minor)"]
        direction TB
        B*DAgents["Agents (3)<br/>b*d · expert_rag · expert_asking"]
        B*DPipes["Pipelines (4)<br/>customers × 2-stage<br/>suppliers × 2-stage"]
        B*DCfg["Configs (16 services)<br/>SMB path hardcoded<br/>SNK enrichment"]
        B*DExt["External: Azure OpenAI (Sweden)<br/>Cohere reranking<br/>SMB share"]
    end

    subgraph C*C["aihub-c*c v0.274.3 (drift 15 minor)"]
        direction TB
        C*CAgents["Agents (4)<br/>chat · jira · log<br/>retrieval_orchestrator"]
        C*CPipes["Pipelines (6)<br/>jira/confluence/sharepoint<br/>× 2-stage"]
        C*CAPI["Custom API<br/>Jira webhook<br/>Support Desk"]
        C*CLib["lib/common/<br/>events · types · ops"]
        C*CExt["External: Azure Foundry SUI+SWE<br/>Azure Doc Intelligence<br/>Azure AD B2C · Key Vault · VM<br/>Jira · Confluence · SharePoint"]
    end

    Future["Other customers (TBD info):<br/>Ig*s · Dem*scope · W*P · Balmer-E*<br/>(deployment gen + components pending)"]

    subgraph INFRA["Infrastructure Repos (Gen 2)"]
        direction TB
        Playbook["aihub-playbook<br/>Ansible Pull (every 15min)<br/>docker_runtime · traefik_proxy<br/>signoz · aihub_application<br/>os_backups (Restic→Swift)"]
        Ops["aihub-ops<br/>OpenStack VM provisioning<br/>setup-aihub.sh · cloud-init<br/>vault-vars-routing.yml<br/>nightly drift check"]
        CustomerRepo["aihub-{customer_id}<br/>Ansible Vault (encrypted)<br/>Custom config + secrets"]
    end

    CORE -.->|git tag<br/>v0.279.2| B*D
    CORE -.->|git tag<br/>v0.274.3| C*C
    CORE -.->|git tag<br/>vX.Y.Z| Future

    Playbook -->|pulls every 15min| Future
    Ops -.->|provisions VM| Future
    CustomerRepo -.->|vault secrets| Future

    style CORE fill:#e8f0ff
    style B*D fill:#fff4e8
    style C*C fill:#fff4e8
    style Future stroke-dasharray: 5 5,stroke:#888,fill:#f5f5f5
    style INFRA fill:#e8ffe8
```

**Customer Registry** (extend khi có customer mới)

Components format: `A` = agents, `P` = pipelines, `API` = custom API. Drift = số minor versions behind core latest.
Sovereignty annotation inline trong LLM Provider. **Deployment Gen**: Gen 1 = Azure VM + shell scripts (manual); Gen 2 =
OpenStack Infomaniak + Ansible Pull (aihub-playbook/aihub-ops).

| Customer              | Status            | Core ver (drift)     | Components      | Deployment Gen                                          | Data sources                         | LLM Provider                                        | Identity                |        Off-site Backup         | Own arc42 + ADRs | Test coverage              |
| --------------------- | ----------------- | -------------------- | --------------- | ------------------------------------------------------- | ------------------------------------ | --------------------------------------------------- | ----------------------- | :----------------------------: | :--------------: | -------------------------- |
| aihub-b\*d            | Production 4/2026 | v0.279.2 (10 behind) | 3A / 4P / -     | **Gen 1** - On-prem (SMB share)                         | SMB share (customer + supplier docs) | Azure OpenAI Sweden - **sovereignty violated**      | Keycloak SaaS           |        Không (same VM)         |      Không       | Minimal (59 dòng / 1 util) |
| aihub-c\*c            | Production        | v0.274.3 (15 behind) | 4A / 6P / 1 API | **Gen 1** - Azure VM (SUI+SWE)                          | Jira / Confluence / SharePoint       | Azure AI Foundry SUI+SWE - **sovereignty violated** | Keycloak + Azure AD B2C |        Không (same VM)         |      Không       | Zero                       |
| aihub-Ig\*s           | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| aihub-W\*P            | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| aihub-Dem\*scope      | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| aihub-Balmer-E\*      | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| Customer #N+ (future) | Template ready    | TBD                  | TBD             | **Gen 2** - OpenStack Infomaniak (Swiss) + Ansible Pull | TBD                                  | TBD                                                 | TBD                     | Restic → Swift (partial 3-2-1) | TBD via template | TBD                        |

______________________________________________________________________

## 3. Priority items cho go-live (CRITICAL + HIGH)

Section này highlight các items cần ưu tiên address để chuẩn bị go-live, group theo scope (Core / B*D / C*C). Severity:

- **CRITICAL**: block go-live, gây data loss / security breach / compliance violation / fatal scenario nếu không fix
- **HIGH**: significant impact tới scale, reliability, hoặc compliance; cần address trước khi mở rộng customer base

**Lưu ý severity**: Severity assume scenario "new customer onboarding với mid-to-high compliance requirement" (Swiss
enterprise / regulated industry như banking, healthcare, gov). Cho scenarios khác (vd internal-only customer low
regulation, hoặc shared multi-tenant SaaS) → review severity individually; nhiều items có thể downgrade hoặc upgrade tuỳ
context.

Dùng list này làm input để team sắp xếp priority tasks cho roadmap go-live. Chi tiết technical đầy đủ trong §4
Assessment và §5 Concerns. Items severity MEDIUM (business / scoping / nice-to-have) tracked trong §6 Recommendations
thay vì list này.

### 3.1. aihub-core (Platform)

| #   | Item                                                                 |   Severity   | Recommendation actions                                                                                                                                        |
| --- | -------------------------------------------------------------------- | :----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Sovereignty path chưa decide                                         | **CRITICAL** | Chọn Option A (self-hosted local LLM) / B (hybrid với updated ADR allow Azure-EU) / C (per-customer sovereignty tier); update ADR `2026_02_24`                |
| 2   | UsageLimits không enforce                                            | **CRITICAL** | Wire middleware 4-layer (per-user/tenant/model/global); pre-flight cost estimation; hard cap với circuit breaker (xem `adr_012`)                              |
| 3   | Multi-tenant data layer không isolate                                | **CRITICAL** | Add `tenant_id` field bắt buộc; per-tenant Milvus collection; NATS subject namespace `aihub.tenant.{id}.*`; Valkey key prefix; auto-filter repository wrapper |
| 4   | Document ACL không inherit vào Milvus                                | **CRITICAL** | ACL metadata field trong Milvus + retrieval-time filter `user_groups` (xem `adr_020`)                                                                         |
| 5   | MCP tool args bypass Presidio                                        | **CRITICAL** | Implement `SecureMCPExecutor` với Presidio sanitization + tool authorization (xem `adr_019`)                                                                  |
| 6   | `AuditLogEntity` missing                                             | **CRITICAL** | Write-once entity với retention policy + tamper-evident hash chain (xem `adr_011`); fix GDPR Art. 30 / ISO 27001 A.12.4 / SOC2 violation                      |
| 7   | GDPR right-to-erasure không implementable                            | **CRITICAL** | Implement cascade DELETE endpoint user/tenant qua Mongo/Milvus/Neo4j/Valkey/SeaweedFS; document compliance procedure                                          |
| 8   | No DLQ JetStream poison messages                                     | **CRITICAL** | DLQ subject `aihub.dlq.*` với max-retry policy + alerting; tránh consumer crash loop block downstream                                                         |
| 9   | No circuit breaker external deps                                     | **CRITICAL** | `pybreaker` per LiteLLM/Keycloak/Milvus với threshold + half-open recovery; tránh outage cascade khắp platform                                                |
| 10  | No HA architecture (mọi stateful service single instance)            |     HIGH     | HA roadmap per service: Postgres streaming replication, NATS 3-node cluster, Valkey Sentinel, Milvus cluster mode, Keycloak Infinispan, etcd 3-node           |
| 11  | No DB migration framework                                            |     HIGH     | Versioned migration framework (Alembic-like) + metadata collection tracking applied migrations                                                                |
| 12  | False docs claims (Presidio, GDPR right-to-erasure, audit immutable) |     HIGH     | Remove false claims trong CLAUDE.md + GDPR docs; sync với reality; add doc-code drift detection CI                                                            |
| 13  | Presidio chỉ DE multilingual gap                                     |     HIGH     | Per-language Presidio routing (DE/FR/IT/EN) + Swiss custom recognizers (AHV, CHE-UID, +41 phone)                                                              |
| 14  | No mTLS service-to-service                                           |     HIGH     | mTLS NATS/Mongo/Redis với cert rotation tự động (cert-manager / Vault)                                                                                        |
| 15  | No supply chain security (SBOM/signing/scan)                         |     HIGH     | syft (SBOM) + cosign (image signing) + trivy (vuln scan) trong CI                                                                                             |
| 16  | No API rate limiting                                                 |     HIGH     | Redis-backed rate limiter middleware per user + per tenant                                                                                                    |
| 17  | Milvus single-node memory wall (122 GB cho 10M × 3072d)              |     HIGH     | Milvus cluster mode + DISKANN benchmark cho disk-backed index                                                                                                 |
| 18  | No alerting infrastructure formal                                    |     HIGH     | Prometheus AlertManager + PagerDuty/OpsGenie on-call routing + per-service severity rules                                                                     |
| 19  | No business metrics + SLI/SLO formal                                 |     HIGH     | Business metrics export (agent_runs, HITL escalations, RAG latency); formal SLI/SLO documented per service                                                    |
| 20  | No K8s migration path                                                |     HIGH     | K8s migration plan với Helm chart + StatefulSets cho stateful services + HPA cho stateless                                                                    |
| 21  | No load test baseline                                                |     HIGH     | Load test suite (k6/Locust) trong CI với baseline numbers per critical path                                                                                   |
| 22  | Connector framework missing                                          |     HIGH     | `BaseSourceConnector` framework + 12 built-in connectors (SMB, S3, SharePoint, Confluence, Jira, GitHub, Notion, Drive, Box, Salesforce, IMAP)                |
| 23  | Code RAG semantic-only (thiếu structural chunks)                     |     HIGH     | tree-sitter AST chunking + code-specific embedding (CodeBERT/UniXcoder) + hybrid index (vector + symbol + Neo4j call-graph)                                   |
| 24  | Open-source dependency lock-in                                       |     HIGH     | Hexagonal Ports & Adapters cho 6 layer (DocumentParser/EmbeddingProvider/Reranker/VectorStore/PIIDetector/SpeechProcessor) + contract tests                   |
| 25  | Workflow architecture Process vs Agentic chưa quyết định             |     HIGH     | Strategic decision: Option A (activate hybrid Process+Agentic với routing criteria) hoặc Option B (deprecate process clean + migration guide)                 |
| 26  | No run / AITL timeout                                                |     HIGH     | Explicit timeout per agent run + `MAX_AITL_DEPTH = 5` hardcap cho recursive escalation                                                                        |
| 27  | Container resource limits in production                              |     HIGH     | Explicit `deploy.resources.limits` (CPU/memory) per service trong docker-compose; profile-based sizing; tránh 1 container OOM = host crash                    |
| 28  | Backup encryption at rest chưa verify                                |     HIGH     | Verify Restic encryption enabled cho off-host backup; document encryption key management; key rotation procedure                                              |
| 29  | Keycloak signing key rotation procedure thiếu                        |     HIGH     | Document JWT signing key rotation (every 6 months); automation script; audit log; tránh compromised key = unlimited token forgery                             |
| 30  | Image vulnerability remediation SLA thiếu                            |     HIGH     | SLA cho critical CVE (7 days), high (30 days), medium (90 days); track trong dashboard; tách biệt với supply chain detection (scanning)                       |

### 3.2. aihub-b\*d

| #   | Item                                                           |   Severity   | Recommendation actions                                                                                                                                           |
| --- | -------------------------------------------------------------- | :----------: | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Backup destination cùng VM (FATAL: VM dies = total loss)       | **CRITICAL** | Emergency cron sync ra Swiss-sovereign off-site (Infomaniak CH / Exoscale CH / Hetzner); long-term migrate Gen 2 (Restic→Swift)                                  |
| 2   | Azure OpenAI (Sweden) sovereignty violation                    |     HIGH     | Tied tới Core sovereignty path decision (Option A/B/C); ADR document trade-off hoặc migration plan. Severity depends on customer compliance contract             |
| 3   | Test coverage near-zero (59 dòng / 1 utility)                  |     HIGH     | Baseline test plan (smoke tests per agent / pipeline); integration test với staging data; coverage threshold 60% cho new code                                    |
| 4   | SDK drift 10 minor versions (v0.279.2 vs v0.289.10)            |     HIGH     | SDK upgrade plan với security delta audit; extract reusable patterns (`resolve_selection`, HITL helpers) về core; CI gate block drift > N versions               |
| 5   | Cohere reranking US/Canada vendor                              |     HIGH     | ADR document sovereignty trade-off hoặc migrate sang sovereign alternative (BGE local, Jina local)                                                               |
| 6   | Storage multiplier 3.9x (1.9 TB insufficient cho 2+ customers) |     HIGH     | Data partitioning strategy (sharding / time-based / customer-based / cold storage); ADR document chiến lược                                                      |
| 7   | Hardcoded customer config (SNK_ANCHOR, BASE_PATH SMB)          |     HIGH     | Pydantic Settings từ env per deployment; document config matrix                                                                                                  |
| 8   | Weak model malformed JSON break workflow                       |     HIGH     | Structured output / JSON mode (`response_format`) + Pydantic validation + fallback chain weak→strong model + golden test suite CI                                |
| 9   | No resource limits docker-compose                              |     HIGH     | Explicit CPU/memory limits per service; profile-based sizing                                                                                                     |
| 10  | Internal import violation `pipelines/snk_enrichment.py:2`      |     HIGH     | Fix import qua core public API (`__init__.py`); lint rule chặn internal imports                                                                                  |
| 11  | No own arc42 + ADRs                                            |     HIGH     | arc42 12 chapters skeleton + C4 L1/L2 + 10 ADRs trả lời design questions (sovereignty, partitioning, SMB path, SNK enrichment, regex utils, Cohere choice, etc.) |

### 3.3. aihub-c\*c

| #   | Item                                                                           |   Severity   | Recommendation actions                                                                                                                                                                                                                                                                                                                                                                                                   |
| --- | ------------------------------------------------------------------------------ | :----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Backup destination cùng Azure VM (FATAL)                                       | **CRITICAL** | Tier 1 emergency cron sync ra Swiss off-site; plan migration Gen 2 với cross-region replication                                                                                                                                                                                                                                                                                                                          |
| 2   | Azure AI Foundry + Azure DI sovereignty violation                              | **CRITICAL** | Standardize trên core stack (MinerU + LiteLLM gateway); migration roadmap DI → MinerU, Foundry → vLLM/Swiss LLM Cloud qua LiteLLM                                                                                                                                                                                                                                                                                        |
| 3   | Per-user data access control thiếu (3 manifestations cùng root cause)          | **CRITICAL** | Holistic fix: (a) per-user OAuth delegated permissions cho Jira/SharePoint/Confluence thay service account shared keys; (b) move isolation xuống data layer (per-tenant Milvus collection, per-user ACL filter retrieval query, pre-filter chunks trước LLM context); (c) ACL inheritance vào Milvus metadata + retrieval-time filter; (d) user access matrix documented; audit log forensic. GDPR Art. 32/25 compliance |
| 4   | Test coverage ZERO (4 agents + 6 pipelines + custom API + lib/common untested) |     HIGH     | Baseline test plan; smoke tests per component; integration test với staging Jira/Confluence/SharePoint                                                                                                                                                                                                                                                                                                                   |
| 5   | SDK drift 15 minor versions (largest drift)                                    |     HIGH     | SDK upgrade với security delta audit; standardize uv workflow; deprecate poetry.lock; CI gate block drift                                                                                                                                                                                                                                                                                                                |
| 6   | SharePoint over-permissioned `Sites.Read.All` tenant-wide                      |     HIGH     | Scoped permission `Sites.Selected` per site; document access matrix per site (sub-aspect của item #3)                                                                                                                                                                                                                                                                                                                    |
| 7   | Hardcoded Jira config (URL/IDs)                                                |     HIGH     | Pydantic Settings từ env per deployment                                                                                                                                                                                                                                                                                                                                                                                  |
| 8   | Naming camouflage (gpt-oss-120b → azure/gpt-5-nano)                            |     HIGH     | Transparent naming convention (vd `azure-eu/gpt-5-nano`); ADR document trade-off                                                                                                                                                                                                                                                                                                                                         |
| 9   | Jira webhook không idempotent (`JiraWebhookController`)                        |     HIGH     | Idempotency key từ webhook event ID; Redis lock pattern                                                                                                                                                                                                                                                                                                                                                                  |
| 10  | Custom API chưa contribute lên core                                            |     HIGH     | Extract Jira webhook + Support Desk endpoint về core như extension points; ADR decision when to extract                                                                                                                                                                                                                                                                                                                  |
| 11  | External services cascade risk (Jira/Confluence/SharePoint/Azure outage)       |     HIGH     | Circuit breaker per source; cached fallback cho read paths; DR plan documented                                                                                                                                                                                                                                                                                                                                           |
| 12  | Azure stack triple redundancy (DI + Foundry + core MinerU+LiteLLM)             |     HIGH     | Standardize core stack; ADR Azure-specific justification; migration roadmap                                                                                                                                                                                                                                                                                                                                              |
| 13  | Azure AD B2C vendor lock-in                                                    |     HIGH     | ADR document trade-off; evaluate pure Keycloak federation alternative                                                                                                                                                                                                                                                                                                                                                    |
| 14  | Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`    |     HIGH     | Fix import qua core public API; lint rule chặn                                                                                                                                                                                                                                                                                                                                                                           |
| 15  | Dual lock files (poetry.lock 84KB + uv.lock)                                   |     HIGH     | Migrate to uv-only workflow; deprecate poetry.lock; standard uv commands                                                                                                                                                                                                                                                                                                                                                 |
| 16  | No own arc42 + ADRs                                                            |     HIGH     | arc42 12 chapters skeleton + C4 L1/L2 + 13 ADRs trả lời design questions (Azure Foundry, DI vs MinerU, naming camouflage, service account, AD B2C, etc.)                                                                                                                                                                                                                                                                 |

______________________________________________________________________

## 4. Đánh giá

Đánh giá theo 2 perspectives song song.

### 4.1. Theo khung 10 pillars

10 pillars dựa trên [Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/), mở rộng
thêm các trụ cột đặc thù cho platform multi-customer (Multi-Tenancy, SDK Versioning, Observability, Quality Assurance).
Mỗi cell liệt kê findings của scope đó. Cell `-` nghĩa là scope không có finding riêng.

| #   | Pillar - Status                                                          | Core                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | B\*D                                                                                                                                                                                                                                                                   | C\*C                                                                                                                                                                                                                                                                                                                                          | Ig\*s | Dem\*scope | W\*P | Balmer-E\* | Cross-cutting                                                                                                                                                                                                              |
| --- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------- | ---- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Multi-Tenancy & Customer Isolation** - Critical                        | • NATS subjects không hierarchy `aihub.tenant.{id}.*`<br>• Milvus collections không namespace per-tenant<br>• MongoDB entities không có `tenant_id` field bắt buộc<br>• Valkey keys không có per-tenant prefix<br>• Neo4j graphs không namespace<br>• Không có tenant provisioning workflow / automation API<br>• Không có per-tenant feature flags<br>• Không có per-tenant resource quotas (rate limit, storage, LLM budget)<br>• Tenant chỉ tồn tại ở Keycloak layer (groups `/tenants/{id}`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD   | TBD        | TBD  | TBD        | • Mỗi customer = 1 Docker stack riêng biệt<br>• Không thể chạy shared SaaS multi-tenant<br>• Operational cost tuyến tính theo số customers<br>• Không có cross-tenant isolation test trong CI                              |
| 2   | **SDK Versioning & Extension Contract** - Gap                            | • Không có public SDK release (PyPI/internal registry), chỉ git+ssh<br>• Không có policy về breaking change, deprecation window<br>• Không có CHANGELOG categorization<br>• Không có downstream CI integration test với customers<br>• Không có lint rule chặn import từ internal modules                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | • Drift 10 minor versions (v0.279.2 vs v0.289.10)<br>• Internal import violation `pipelines/snk_enrichment.py:2`<br>• Patterns chưa extract về core (`resolve_selection()`, HITL helpers)                                                                              | • Drift 15 minor versions (v0.274.3 vs v0.289.10)<br>• Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`<br>• Custom `switch_dependencies.py` thay standard uv workflow<br>• Dual lock files `poetry.lock` (84KB) + `uv.lock`<br>• Multi-agent orchestrator, Jira/Confluence/SharePoint connectors chưa extract     | TBD   | TBD        | TBD  | TBD        | -                                                                                                                                                                                                                          |
| 3   | **Security & Compliance** - Partial                                      | **Strengths**: 5 auth handlers (Keycloak/Token/Bearer/OAuth2/OpenWebUI) JWKS 6h cache; hierarchical permission template với wildcards; AccessChecker tenant-ceiling + BDD tests; two-stage access control tested.<br>**Gaps**:<br>• UsageLimits class defined nhưng KHÔNG wire vào middleware<br>• Không có `AuditLogEntity` (vi phạm GDPR Art. 30, ISO 27001 A.12.4, SOC2)<br>• Event payloads không signing (JetStream unsigned JSON)<br>• NATS token-only auth, no mTLS; MongoDB/Redis connection string<br>• Presidio claim ≠ thực tế (code dùng LLM-based fragile guard)<br>• MCP tool args bypass LiteLLM → Presidio guards bypass 100%<br>• File upload trust mime-type, no content sniffing<br>• OpenWebUI render model list bypass RBAC<br>• Docker volume chưa encrypt at rest<br>• No rate limiting per user/tenant ở API<br>• Không có SAST / dep vuln scan / SBOM / image signing / container vuln scan                                                                                                                                                                                                                                                                      | • Cohere reranking (US/Canada vendor)<br>• Hardcoded customer-specific config (SNK_ANCHOR, BASE_PATH)<br>• No secrets rotation policy                                                                                                                                  | • Service account shared key cho Jira/SharePoint/Confluence (vi phạm least-privilege)<br>• SharePoint Azure AD app-only `Sites.Read.All` tenant-wide<br>• Hardcoded Jira IDs (URL, Service Desk, Request Type, Project)<br>• Azure AD B2C federation thay pure Keycloak (vendor lock-in)                                                      | TBD   | TBD        | TBD  | TBD        | • Document ACL không inherit từ Jira/SharePoint/Confluence vào Milvus<br>• Service account ingest mọi thứ, user query được mọi document (cross-user leak)<br>• Presidio chỉ DE, Swiss multilingual FR/IT/EN PII không mask |
| 4   | **Reliability & Data Integrity** - Critical (Gen 2 partial fix)          | • Không có DB migration framework (schemas tạo implicit bởi Pydantic + MongoEngine startup)<br>• Cross-store consistency không đảm bảo (NATS + Mongo + Valkey)<br>• Không có RTO/RPO documented<br>• Không có automated DR test / restore drill<br>• Backup encryption at rest chưa rõ cho Gen 1<br>• Milvus không upsert-by-id → re-ingest = duplicate vectors<br>• Agent config schema không versioning<br>• No agent versioning cho in-flight runs<br>• No run / delegation timeout<br>• No circuit breaker cho external deps (LiteLLM, Keycloak, Milvus cascade)<br>• No DLQ cho JetStream poison messages<br>• No HA architecture (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd đều single-instance)<br>• **Gen 2 partial fix**: Ansible Pull tự re-reconcile khi container drift; Restic backup ra OpenStack Swift container (off-host)<br>• Vẫn thiếu: cross-provider replication, HA stateful services, no DR drill automated                                                                                                                                                                                                                                                      | • **Gen 1 fatal**: Backup destination SeaweedFS cùng VM → VM chết = mất cả<br>• No off-site replication<br>• Production 3.9x storage multiplier (1 TB → 5.1 TB)<br>• Chưa migration sang Gen 2 (Restic→Swift)                                                          | • **Gen 1 fatal**: Backup destination cùng Azure VM<br>• Jira webhook không idempotent (`JiraWebhookController`): cùng event 2x = 2 agent runs<br>• External services cascade (Jira/Confluence/SharePoint/Azure outage)<br>• Chưa migration sang Gen 2 (Restic→Swift)                                                                         | TBD   | TBD        | TBD  | TBD        | • Gen 2 Restic→Swift đạt off-host nhưng **cùng cloud provider** (Infomaniak) - Infomaniak region outage = mất cả primary cộng backup<br>• Cross-provider replication chưa có                                               |
| 5   | **Operational Excellence** - Partial (improved with Gen 2)               | **Strengths**: CI/CD đầy đủ (lint-pr, semantic-pr, build-\* per package, deploy-docs, auto-tag); pre-commit hooks; 45 ADRs; Docker Compose Jinja2 templates; **Gen 2 Ansible Pull pattern** (aihub-playbook every 15min auto-reconcile); **customer onboarding automation** (`setup-aihub.sh`); **Ansible Vault encrypted secrets** với auto-gen via `vault-vars-routing.yml`; **Traefik + Let's Encrypt ACME** automated SSL; **env vars drift detection CI** (`check_env_drift.py` nightly).<br>**Gaps**:<br>• Không có Operations Guide / Runbook cho incident response<br>• Không có Incident Response Process (severity, escalation)<br>• Không có Upgrade Procedure documented<br>• Không có K8s/Helm chart cho production<br>• Health checks không tách liveness/readiness<br>• arc42 ch.11 (Risks) cần update với findings mới<br>• CLAUDE.md có false claims (Presidio integration)<br>• GDPR docs có false claims (right to erasure, audit logs immutable)<br>• Ansible Pull 15-min cadence chậm cho hot-fix<br>• GitHub là deploy SPOF (no local mirror)<br>• 3-repo version compatibility chưa có matrix / CI gate<br>• Deploy key rotation policy implicit, không automation | • Gen 1 deployment (Azure manual, chưa Gen 2)<br>• CI riêng (build-agents, build-pipelines, auto-tag)<br>• Không có arc42 docs riêng (12 chapters required)<br>• Không có ADRs riêng (8+ key decisions)<br>• 6 docker-compose files separation chưa document rationale | • Gen 1 deployment (Azure VM + shell scripts, chưa Gen 2)<br>• CI riêng (build-agents, build-pipelines, build-api, lint-pr)<br>• Không có arc42 docs riêng (12 chapters required)<br>• Không có ADRs riêng (13+ key decisions)<br>• Azure IaC `.iac/scripts/` shell scripts thay Pulumi<br>• Custom API deployment monitoring chưa documented | TBD   | TBD        | TBD  | TBD        | • Không có alerting infrastructure formal (chỉ Slack on Ansible Pull failure)<br>• Customer documentation gate trước go-production chưa định nghĩa<br>• B*D/C*C migration path Gen 1 → Gen 2 chưa có                       |
| 6   | **Performance & Scalability** - Critical                                 | • Single-server ceiling (Docker Compose only, no K8s)<br>• Milvus single-node, HNSW memory wall (122 GB RAM cho 10M × 3072d × 4B)<br>• PostgreSQL single instance (no replica, no failover)<br>• SeaweedFS single master/volume/filer (no HA, replication="000")<br>• NATS single node, `max_memory_store: 512MB`, `max_file_store: 10GB` (dev config)<br>• Valkey single instance (SPOF)<br>• Pipeline ops dùng `in_process_executor` (single-thread)<br>• Dagster dynamic partition explosion risk (1 partition per file)<br>• Embedding batch size không tối ưu (recursive bisection fallback)<br>• LiteLLM throughput limit không documented<br>• Tenant membership không cache (Keycloak call per request)<br>• GPU pinned device 0, multi-GPU không tận dụng<br>• Không có resource limits trong docker-compose                                                                                                                                                                                                                                                                                                                                                                     | • Sizing production (4/2026): 16 CPU + 64 GiB RAM + 1.9 TB disk<br>• 1.9 TB disk insufficient cho 2+ customers shared                                                                                                                                                  | -                                                                                                                                                                                                                                                                                                                                             | TBD   | TBD        | TBD  | TBD        | • Không có Load Test Baseline (k6, Locust)<br>• Không có Performance Baseline document<br>• Không có Horizontal Scaling Guide                                                                                              |
| 7   | **Observability** - Traces tốt, metrics yếu (improved with Gen 2 SigNoz) | **Strengths**: OTEL comprehensive (NATS/Mongo/Redis/Milvus/HTTP/asyncio); `SmartTracer` + `@trace_fn`; trace context cross-service qua NATS headers; Langfuse LLM observability (prompt/response, cost); Docker healthchecks; HealthController; **Gen 2 SigNoz OTEL collector role** (host metrics, OTLP traces, journald log collection); **Slack failure notifications** từ Ansible Pull.<br>**Gaps**:<br>• Bot scope (`packages/bot`) không OTEL → trace gãy ở bot boundary<br>• Không có business metrics (agent_runs, HITL escalations, ingestion rate, RAG latency)<br>• Không có SLO/SLI formal<br>• Không có Prometheus AlertManager với rules per service severity<br>• Không có Grafana dashboards<br>• Không có on-call routing (PagerDuty/OpsGenie)<br>• Logs unstructured, default WARNING level<br>• Không có log aggregation centralized (ELK/Loki tự host)<br>• Không có per-tenant cost attribution trong Langfuse<br>• Không có synthetic monitoring<br>• **SigNoz Cloud region "eu"** - data observability ra ngoài tenant infra; sovereignty implication chưa rõ<br>• SigNoz chỉ Gen 2; Gen 1 (B*D/C*C) không có                                                      | • Gen 1 - không SigNoz<br>• Business-level metrics chưa có                                                                                                                                                                                                             | • Gen 1 - không SigNoz<br>• Business-level metrics chưa có<br>• Custom API endpoints chưa monitoring                                                                                                                                                                                                                                          | TBD   | TBD        | TBD  | TBD        | -                                                                                                                                                                                                                          |
| 8   | **Quality Assurance** - Gap                                              | **Strengths**: ~150 test files trong `packages/core`, 35+ `packages/api`, 30+ `packages/agent`; BDD qua pytest-bdd; integration tests với real NATS (`SimulatedAgentApiTestRunner`); E2E key flows.<br>**Gaps**:<br>• Không có Load test trong CI<br>• Không có Chaos engineering<br>• Không có coverage threshold (no 80% gate)<br>• Không có SAST trong CI<br>• Không có dependency audit (pip-audit, trivy)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | • Test coverage: 59 dòng total (`tests/test_snk_enrichment.py`)<br>• 9 parametrized tests cho 1 utility function only<br>• Agents và pipelines chưa có tests                                                                                                           | • Test coverage: ZERO<br>• Không có thư mục tests<br>• 4 agents + 6 pipelines + custom API + `lib/common` đều untested                                                                                                                                                                                                                        | TBD   | TBD        | TBD  | TBD        | • Không có integration test giữa core release và customer projects<br>• Không có E2E test cho multi-tenant isolation                                                                                                       |
| 9   | **Cost Optimization** - Critical                                         | • LLM cost tracking via `LLMCostEvent` (per-model, per-token rates)<br>• Per-agent run cost attribution via Langfuse<br>• S3 file expiration 7 days (`FILE_EXPIRATION_DAYS = 7`)<br>• Backup retention configured<br>• `UsageLimits` defined NHƯNG KHÔNG wire vào middleware → LLM cost unbounded<br>• Không có Pre-flight Cost Estimation<br>• Không có Hard Per-tenant Cost Cap<br>• Không có Storage Quota per tenant<br>• Không có Showback Mechanism<br>• Không có Budget Alert<br>• MCP tool costs KHÔNG tracked (external API costs invisible)<br>• Mongo collections unbounded (no TTL) = storage cost growth                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD   | TBD        | TBD  | TBD        | • Không có per-tenant cost attribution Langfuse<br>• Không có cold storage tier (tất cả data ở hot storage)                                                                                                                |
| 10  | **Sustainability** - Critical                                            | • Cloud-native capable in theory (containerized, stateless)<br>• License compliance OK (402 Python + 993 npm + 33 Docker all approved)<br>• Python 3.13 slim base images<br>• Không có Region/Data-Residency Strategy<br>• Không có Carbon Footprint Metrics<br>• Không có Energy Consumption Tracking<br>• Không có Sustainability Reporting<br>• LLM calls không optimize (no aggressive caching, batching, prompt compression)<br>• Không có Hardware Lifecycle Management<br>• Không có efficient algorithm benchmarking (HNSW vs DISKANN)<br>• Compute-heavy LLM calls không scheduling off-peak                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD   | TBD        | TBD  | TBD        | -                                                                                                                                                                                                                          |

### 4.2. Business core values vs thực tế

| Core value                         | Statement / Source                                                            | Core (Platform)                                                                                                                                                                                                                                                             | b\*d                                         | c\*c                                                                               | Ig\*s | Dem\*scope | W\*P | Balmer-E\* |       Status       |
| ---------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- | ----- | ---------- | ---- | ---------- | :----------------: |
| Swiss data sovereignty             | ADR `2026_02_24`: "All cloud inference must stay within Swiss infrastructure" | Declared via ADR, enforce qua self-hosted local LLM hoặc Swiss LLM Cloud                                                                                                                                                                                                    | 100% Azure OpenAI (Sweden region)            | 100% Azure AI Foundry (SUI+SWE) + Azure Document Intelligence                      | TBD   | TBD        | TBD  | TBD        |      VIOLATED      |
| No vendor lock-in                  | Platform principle                                                            | OK (no lock-in trong core)                                                                                                                                                                                                                                                  | Cohere reranking (US/Canada vendor)          | Lock-in Azure ở 5 tầng (VM, Key Vault, AD B2C, OpenAI, Doc Intelligence) + Jina AI | TBD   | TBD        | TBD  | TBD        |      VIOLATED      |
| Self-hosted, on-premise capable    | Marketing claim                                                               | Infrastructure self-hosted OK                                                                                                                                                                                                                                               | Infra self-hosted, LLM Azure cloud           | Infra Azure VM, LLM Azure cloud                                                    | TBD   | TBD        | TBD  | TBD        |      PARTIAL       |
| "Swiss Sovereign AI" marketing     | Public positioning                                                            | Infrastructure-level đúng                                                                                                                                                                                                                                                   | B\*D dùng Azure LLM → claim chưa align scope | C\*C dùng Azure LLM → claim chưa align scope                                       | TBD   | TBD        | TBD  | TBD        | Cần review wording |
| Open-source platform               | License declaration                                                           | OK (BSD/MIT/Apache verified)                                                                                                                                                                                                                                                | OK                                           | OK                                                                                 | TBD   | TBD        | TBD  | TBD        |         OK         |
| Multi-tenant SaaS support          | ADRs 2026_03_30, 2026_02_20                                                   | Tenant chỉ ở Keycloak; data layer không namespace                                                                                                                                                                                                                           | Single-tenant deployment                     | Single-tenant deployment                                                           | TBD   | TBD        | TBD  | TBD        |     NOT READY      |
| GDPR Art. 17 right to erasure      | Compliance docs claim "implemented"                                           | Không có user/tenant DELETE endpoint                                                                                                                                                                                                                                        | N/A                                          | N/A                                                                                | TBD   | TBD        | TBD  | TBD        |    FALSE CLAIM     |
| Audit log immutability             | GDPR docs claim "audit logs remain immutable"                                 | Không có `AuditLogEntity` trong codebase                                                                                                                                                                                                                                    | N/A                                          | N/A                                                                                | TBD   | TBD        | TBD  | TBD        |    FALSE CLAIM     |
| Presidio PII protection            | CLAUDE.md claims integrated                                                   | Code dùng LLM-based fragile guard, không phải Presidio                                                                                                                                                                                                                      | N/A                                          | N/A                                                                                | TBD   | TBD        | TBD  | TBD        |    FALSE CLAIM     |
| MCP secure tool execution          | Implied by MCP integration                                                    | Tool args bypass LiteLLM → Presidio bypass 100%                                                                                                                                                                                                                             | N/A                                          | Risk cao do agent-heavy use case                                                   | TBD   | TBD        | TBD  | TBD        |     LEAK RISK      |
| Document ACL respect               | Implied by RBAC architecture                                                  | Milvus không có ACL field, retrieval không filter user                                                                                                                                                                                                                      | N/A                                          | Service account ingest mọi thứ; cross-user query data leak                         | TBD   | TBD        | TBD  | TBD        |     LEAK RISK      |
| Multi-language Swiss (DE/FR/IT/EN) | Platform i18n declared                                                        | Presidio hardcode `de` ở 16 cấu hình files                                                                                                                                                                                                                                  | i18n DE/EN/FR/IT translations có             | N/A                                                                                | TBD   | TBD        | TBD  | TBD        |      PARTIAL       |
| Cost protection per tenant         | Implied by UsageLimits class                                                  | `UsageLimits` defined nhưng KHÔNG wire vào middleware                                                                                                                                                                                                                       | N/A                                          | N/A                                                                                | TBD   | TBD        | TBD  | TBD        |    NOT ENFORCED    |
| Disaster recovery capability       | Backup service tồn tại                                                        | Backup destination = cùng SeaweedFS instance trên cùng VM                                                                                                                                                                                                                   | No off-site backup                           | No off-site backup                                                                 | TBD   | TBD        | TBD  | TBD        |       FATAL        |
| Common enterprise AI patterns      | Agent framework capability                                                    | Conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution, browser automation: working. Vision / predictive analytics / fine-tuned model serving: out of scope (xem `adr_aihub_supported_use_cases.md`) | RAG agents working                           | Multi-agent orchestration working                                                  | TBD   | TBD        | TBD  | TBD        |         OK         |

______________________________________________________________________

## 5. Concerns và Documentation Backlog

Mỗi concern được trình bày theo format `Concern → Direction`. **Concern** = vấn đề là gì cộng như thế nào
(manifestation). **Direction** = hướng giải quyết high-level (chi tiết implementation deep-dive trong §6 cộng các ADRs
riêng). Strategic concerns (có trade-off cần lựa chọn) trình bày dạng block đầy đủ. Documentation deliverables list ở
cuối mỗi scope.

### 5.1. aihub-core (Platform)

#### Sovereignty cộng Compliance

**Sovereignty path violation**

- _Concern_:
  - B\*D dùng Azure OpenAI (Sweden region)
  - C\*C dùng Azure AI Foundry (SUI+SWE) cộng Azure Document Intelligence
  - Vi phạm trực tiếp ADR `2026_02_24` (Swiss sovereign dual-mode inference)
  - Marketing claim "Swiss Sovereign AI" cần clarify scope
  - Compliance considerations theo
    [Schrems II](https://curia.europa.eu/juris/document/document.jsf?docid=228677&doclang=EN) cộng
    [US Cloud Act](https://www.congress.gov/bill/115th-congress/house-bill/4943)
- _Direction_: chọn 1 trong 3 options:
  - **Option A** - self-hosted local LLM cho mọi customer
  - **Option B** - hybrid với ADR updated explicitly allow Azure-EU regions
  - **Option C** - per-customer sovereignty tier (customer chọn theo plan)

**False documentation claims**

- _Concern_:
  - CLAUDE.md claim Presidio integrated nhưng code dùng LLM-based fragile guard
  - GDPR docs claim right-to-erasure implemented nhưng không có user DELETE endpoint
  - GDPR docs claim audit logs immutable nhưng không có `AuditLogEntity`
- _Direction_:
  - Remove false claims trong CLAUDE.md cộng GDPR docs
  - Sync docs với reality (claim chỉ những gì code thật sự làm)
  - Add doc-code drift detection trong CI để catch sớm

**AuditLogEntity missing**

- _Concern_:
  - Không có dedicated `AuditLogEntity` trong codebase
  - Vi phạm [GDPR Art. 30](https://gdpr-info.eu/art-30-gdpr/) (records of processing)
  - Vi phạm [ISO 27001 A.12.4](https://www.iso.org/standard/27001) (event logging)
  - Vi phạm [SOC2 CC7.2](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2)
    (system monitoring)
- _Direction_:
  - Implement write-once entity với retention policy
  - Tamper-evident hash chain cho integrity
  - Chi tiết: xem `adr_011_audit_log_entity.md`

**GDPR right-to-erasure unimplementable**

- _Concern_:
  - Không có user/tenant DELETE endpoint cascade
  - Data nằm rải Mongo / Milvus / Neo4j / Valkey / SeaweedFS không có deletion path
  - Customer request erasure không thực hiện được → compliance fail
- _Direction_:
  - Implement cascade DELETE endpoint qua mọi data store
  - Document compliance procedure per data store
  - Test bằng dry-run erasure flow

#### Security

**UsageLimits không enforce**

- _Concern_:
  - Class `UsageLimits` defined nhưng không wire vào middleware
  - LLM cost unbounded
  - User spam request → cost runaway risk
- _Direction_: wire vào middleware với 4-layer enforcement (per-user / per-tenant / per-model / global). Chi tiết:
  `adr_012_usage_limits_enforcement.md`.

**MCP tool args bypass Presidio**

- _Concern_:
  - MCP tool execution gửi args trực tiếp, không qua LiteLLM proxy
  - Presidio PII guard bypass 100% cho mọi tool call
  - PII leak ra external tool servers
- _Direction_: implement `SecureMCPExecutor` với:
  - Presidio sanitization trên tool args
  - Tool authorization check
  - Chi tiết: `adr_019_mcp_secure_executor.md`

**Document ACL không inherit**

- _Concern_:
  - ACL từ Jira / SharePoint / Confluence / SMB không inherit vào Milvus metadata
  - Service account ingest mọi document
  - Retrieval không filter theo user
  - → cross-user data leak qua RAG (user A query thấy data user B)
- _Direction_:
  - ACL metadata field trong Milvus collection
  - Retrieval-time filter theo `user_groups`
  - Chi tiết: `adr_020_document_acl_inheritance.md`

**Presidio chỉ DE, multilingual gap**

- _Concern_:
  - Presidio analyzer hardcode `de` ở 16 config files
  - Swiss customer data FR/IT/EN không được PII-mask trước khi gửi LLM
  - PII leak cho non-German users
- _Direction_:
  - Per-language Presidio routing (DE/FR/IT/EN)
  - Swiss custom recognizers: AHV, CHE-UID, +41 phone number

**File upload trust mime-type**

- _Concern_:
  - API trust header mime-type, không content sniff
  - Attacker upload `.exe` disguised as `.pdf`
  - Malware lọt vào storage
- _Direction_:
  - python-magic content sniffing trước accept
  - Malware scan (ClamAV) trước commit vào storage

**Volume không encrypt at rest**

- _Concern_:
  - Docker volumes mount plain
  - Disk theft hoặc VM snapshot exposure = toàn bộ data plain text
- _Direction_:
  - LUKS encryption per deployment
  - Document procedure per stage (dev / staging / prod)

**No service-to-service mTLS**

- _Concern_:
  - NATS token-only auth
  - Mongo / Redis dùng connection string
  - Internal traffic không encrypt cộng không authenticate mutually
  - MITM risk trong cluster
- _Direction_:
  - mTLS cho NATS / Mongo / Redis
  - Cert rotation tự động (cert-manager hoặc Vault)

**OpenWebUI bypass RBAC**

- _Concern_:
  - Model list endpoint không filter theo user permissions
  - User thấy được tên agent không có quyền (agent existence leak)
- _Direction_: reverse proxy filter trước khi reach OpenWebUI (filter model list theo user's groups).

**No supply chain security**

- _Concern_:
  - Không có SBOM (Software Bill of Materials)
  - Không có image signing
  - Không có vulnerability scanning
  - Unknown CVEs trong images
  - Supply chain attack risk
- _Direction_:
  - SBOM generation qua syft
  - Image signing qua cosign
  - Vuln scan qua trivy trong CI

**No API rate limiting**

- _Concern_:
  - API không có per-user / per-tenant rate limit
  - DoS risk qua spam request
  - Cost runaway nếu reach LLM endpoints
- _Direction_:
  - Rate limiter middleware (Redis-backed)
  - Tiers per user cộng per tenant

#### Reliability cộng Data Integrity

**No DB migration framework**

- _Concern_:
  - Schemas tạo implicit bởi Pydantic cộng MongoEngine startup
  - Upgrade core version có thể silently drop fields
  - Không có rollback path
  - Không có migration history
- _Direction_:
  - Versioned migration framework (Alembic-like)
  - Metadata collection track applied migrations

**Milvus duplicate vectors khi re-ingest**

- _Concern_:
  - Milvus không có upsert-by-id
  - Ingestion luôn insert → re-ingest cùng document = duplicate vectors
  - Retrieval kết quả sai (cùng chunk xuất hiện N lần)
- _Direction_: delete-then-insert pattern by `document_id` trước khi insert.

**No DLQ cho JetStream**

- _Concern_:
  - Poison messages không có dead-letter queue
  - Bad event = consumer crash loop
  - Block downstream processing
- _Direction_:
  - DLQ subject riêng (`aihub.dlq.*`)
  - Max retry policy
  - Alerting khi message vào DLQ

**No circuit breaker external deps**

- _Concern_:
  - Call LiteLLM / Keycloak / Milvus không có breaker
  - External outage cascade khắp platform
  - Không có degraded mode
- _Direction_:
  - `pybreaker` per external dep
  - Threshold based open
  - Half-open recovery probe

**No run / AITL timeout**

- _Concern_:
  - Agent run không có time budget
  - AITL recursion không cap depth
  - Stuck loop = resource leak
  - Recursive AITL escalation = cost explosion
- _Direction_:
  - Explicit timeout per run (configurable)
  - `MAX_AITL_DEPTH = 5` hardcap

**Mongo TTL missing**

- _Concern_:
  - Collections `agent_events` cộng `threads` không có TTL
  - Storage grow unbounded
  - Không có archival pattern
- _Direction_:
  - TTL indexes với retention policy per collection
  - Archival job cho long-term data

**Cross-store snapshot inconsistency**

- _Concern_:
  - Backup mid-run có thể inconsistent giữa NATS, Mongo, Valkey
  - Không có coordinated checkpoint
  - Restore có thể vào state không valid
- _Direction_:
  - Snapshot orchestration với short-pause-then-flush
  - Hoặc event-sourced backup từ JetStream (replay-able)

**No High Availability architecture**

- _Concern_: mọi stateful service chạy **single instance** = SPOF:
  - **PostgreSQL** - no read replica, no streaming replication, no failover
  - **NATS** - single node, `max_memory_store: 512MB` dev config
  - **Valkey** - single instance (SPOF cho RunContext / ThreadContext agent state)
  - **SeaweedFS** - single master cộng single volume cộng single filer, `replication="000"`
  - **Milvus** - single-node
  - **Keycloak** - single instance
  - **etcd** - single (metadata backend cho Milvus và SeaweedFS, mất etcd = mất cả 2)
  - Container restart = full request failure, không có graceful degradation
- _Direction_: HA roadmap per service:
  - **PostgreSQL** - streaming replication hoặc Patroni cluster với failover
  - **NATS** - 3-node cluster với JetStream replicated storage
  - **Valkey** - Sentinel hoặc Redis Cluster mode
  - **SeaweedFS** - multi-master + `replication="001"` (cross-host)
  - **Milvus** - cluster mode
  - **Keycloak** - Infinispan cluster
  - **etcd** - 3-node cluster
  - Load balancer với health checks
  - Multi-AZ deployment khi lên K8s
  - Document failover RTO per service

#### Observability

**Bot scope no OTEL**

- _Concern_:
  - `packages/bot` không có OTEL instrumentation
  - Trace gãy khi đi qua bot boundary
  - Không debug được flow MS Teams / Slack → agent
- _Direction_: add OTEL instrumentation trong bot scope (auto-instrumentation cộng manual spans cho key paths).

**No alerting infrastructure** _[Partial fix for Gen 2]_

- _Concern_:
  - Không có Prometheus AlertManager
  - Không có on-call routing
  - Lỗi production không page on-call
  - Phụ thuộc manual log check
- _Status_: **Partial fix cho Gen 2** - Slack notification on Ansible Pull failure (`notify_failure.yml`); SigNoz
  collector gửi metrics ra SigNoz Cloud có alert rules. **Còn thiếu**: per-service severity rules, on-call rotation
  (PagerDuty/OpsGenie), formal incident response procedure.
- _Direction_:
  - Prometheus cộng AlertManager setup formal hoặc dùng SigNoz alert rules
  - On-call routing qua PagerDuty / OpsGenie
  - Alert rules per service severity (P1/P2/P3)
  - Incident response runbook

**No business metrics cộng SLI/SLO**

- _Concern_:
  - Chỉ có technical traces, không có business metrics
  - Thiếu: agent_runs, HITL escalations, ingestion rate, RAG latency
  - Không có SLI / SLO formal documented
- _Direction_:
  - Business metrics export qua Prometheus
  - Formal SLI / SLO documented per service
  - Dashboard Grafana

**Unstructured logs cộng no aggregation** _[Partial fix for Gen 2]_

- _Concern_:
  - Logs unstructured (default text format)
  - Default WARNING level (miss INFO debugging info)
  - Không có central aggregation
  - Debug production phải SSH từng container
  - Không search cross-service
- _Status_: **Partial fix cho Gen 2** - SigNoz OTEL collector journald (system logs) cộng OTLP receiver (app traces);
  central aggregation qua SigNoz Cloud. **Còn thiếu**: JSON structured logging (logs vẫn text format), log level config
  per env, self-hosted alternative cho sovereignty.
- _Direction_:
  - JSON structured logging trong app code (separate concern từ SigNoz)
  - Log level config per env
  - Consider self-hosted SigNoz hoặc Loki nếu cloud sovereignty là issue

**No per-tenant cost attribution**

- _Concern_:
  - Langfuse track cost overall, không break down per-tenant
  - Multi-tenant không tính được cost per customer
  - Showback impossible
- _Direction_:
  - Tenant label trong Langfuse traces
  - Dashboard per-tenant cost
  - Cost report tự động monthly

**AI use case scope undefined**

- _Concern_:
  - Doc claim "agent framework cover 9 trên 10 enterprise AI use cases" không có ADR backing
  - Không có canonical taxonomy "10 use cases là gì"
  - Audit / customer pre-sales hỏi "use case X có support không" → không có authoritative answer
  - Vision / predictive analytics / fine-tuning out of scope nhưng không explicit
  - Marketing claims có thể vượt actual capability
- _Direction_:
  - **Authoritative ADR** define list use cases supported (✅ Full / ⚠️ Partial / ❌ Out of scope)
  - Xem `adr_037_aihub_supported_use_cases.md` (proposed)
  - Quarterly review cycle để track coverage maturity
  - Pre-sales playbook anchor vào ADR list

#### Strategic concerns

**Workflow architecture - Process (auto-workflow) vs Agentic** _[Strategic]_

- _Concern_: `packages/process` (declarative orchestration cho agents cộng humans cộng external programs) là **dead
  code** (0 external imports). Team thực tế xài agentic ở `packages/agent`. CLAUDE.md cộng arc42 vẫn document process
  như production component → architecture drift, false claim.
- _Trade-off_:
  - **Process**: ✓ deterministic, audit trail rõ, no LLM cost, dễ test, compliance-friendly · ✗ rigid path, brittle,
    không handle ambiguous
  - **Agentic**: ✓ flexible với open-ended, self-correcting, NL friendly · ✗ non-deterministic, LLM cost mỗi decision,
    audit mờ, hallucination risk, không guarantee execution path
  - Drop hoàn toàn = mất capability cho **compliance customers** (banking/healthcare/gov); high-volume low-variance
    tasks dùng agentic là **overkill cost/latency**; CLAUDE.md vẫn claim → **false architecture claim**.
- _Direction_: **Option A (hybrid, recommended)** - activate process cho deterministic / compliance flows, agentic cho
  ambiguous, document routing criteria explicit (audit requirement / fixed steps → process; open-ended / reasoning →
  agentic). **Option B (deprecate clean)** - xoá code, update CLAUDE.md cộng arc42 cộng docs, migration guide tới
  Temporal/n8n self-hosted/Camunda. **Cần ADR riêng**.

**Connector framework missing** _[Strategic]_

- _Concern_: Không có connector SDK chung trong core. B*D tự build SMB; C*C tự build Jira/Confluence/SharePoint;
  customer mới phải tự build Salesforce/Notion/GitHub/Drive/Box từ scratch.
- _Impact_: Time-to-onboard = **O(N × M)** thay vì O(M); mỗi customer reimplement
  auth/pagination/rate-limit/dedup/incremental sync/schema mapping; bug fix không propagate; **biggest entry barrier**
  cho customer mới; uncompetitive vs Airbyte/Fivetran/Meltano (300+ connectors built-in).
- _Direction_: `BaseSourceConnector` abstract framework cộng plugin discovery; ship built-in connectors phổ biến (SMB,
  S3, SharePoint, Confluence, Jira, GitHub, GitLab, Notion, Drive, Box, Salesforce, IMAP) - covers 80% use cases;
  long-term **connector marketplace** (community-contributable).

**Code RAG - chỉ semantic chunks, thiếu structural** _[Strategic]_

- _Concern_: Pipeline parsing chỉ có semantic chunking (BGE-M3 cộng MinerU), phù hợp prose document **không phù hợp
  code** - cắt giữa method, vỡ syntactic boundary, mất call graph, mất scope.
- _Impact_: Query "function nào xử lý X" retrieve nửa method → broken context; "all callers of Y" không khả thi không có
  call-graph index; AI assistant cho codebase (C\*C IT services use case, future DevOps customers) không reliable.
- _Direction_: **tree-sitter AST chunking** (100+ languages) cộng **code-specific embedding**
  (CodeBERT/GraphCodeBERT/UniXcoder) cộng **hybrid index** (vector cộng symbol ctags/scip cộng call-graph Neo4j) cộng
  code-aware reranker. Plan deferred trong memory cần unblock.

**Open-source dependency lock-in** _[Strategic]_

- _Concern_: LLM đã abstract qua **LiteLLM gateway** nhưng parser (MinerU), embedding (BGE-M3), reranker (BGE), PII
  (Presidio), vector store (Milvus), STT-TTS (Speaches) **chưa có abstraction tương đương** - hardcoded khắp pipeline
  code.
- _Impact_: License precedent (Elasticsearch → Elastic License 2024, MongoDB → SSPL, Redis → RSAL/SSPL, Terraform → BSL)
  \- **open-source ≠ no lock-in**; MinerU/BGE/Milvus có thể đi tương tự; swap sang alternative tốt hơn (MinerU2, Qwen
  embedding, Qdrant) khó vì dep embedded khắp code; không có integration test verify swap.
- _Direction_: **[Hexagonal Ports cộng Adapters](https://alistair.cockburn.us/hexagonal-architecture/)** cho 6 layer
  (`DocumentParser` / `EmbeddingProvider` / `Reranker` / `VectorStore` / `PIIDetector` / `SpeechProcessor`); **contract
  tests** mỗi interface; config-driven implementation selection; **ADR riêng mỗi major dep** với exit plan.

#### Performance

**Pipeline single-thread executor**

- _Concern_:
  - Dagster ops dùng `in_process_executor`
  - Single-thread cho ops trong 1 run
  - Throughput thấp khi parsing / embedding nhiều files
- _Direction_: Multiprocess executor với worker pool config explicit.

**Milvus single-node memory wall**

- _Concern_:
  - Milvus single-node
  - HNSW index memory wall: 10M × 3072d × 4B = 122 GB RAM
  - Multi-customer scale block
- _Direction_:
  - Milvus cluster mode
  - DISKANN benchmark cho disk-backed index (memory-efficient)

**Dagster dynamic partition explosion**

- _Concern_:
  - Pattern 1 partition per file
  - 1M files = 1M partitions
  - DAG explosion, scheduler chậm
- _Direction_: temporal partitioning (per day / per week) thay dynamic per-file.

**No load test baseline**

- _Concern_:
  - Không có k6 / Locust scripts trong repo
  - Không biết throughput limit
  - Không có regression detection
- _Direction_:
  - Load test suite (k6) trong CI
  - Baseline numbers per critical path
  - Alert khi regression > threshold

**Embedding batch không tuned**

- _Concern_:
  - Batch size dùng recursive bisection fallback (heuristic)
  - Throughput không tối ưu
  - GPU underutilized
- _Direction_:
  - Explicit batch config per model
  - Profile-based tuning theo GPU memory

#### Documentation deliverables (team owners required)

- High-Level Architecture Diagram (HLAD) reflecting actual production
- C4 Level 1 (System Context) cộng C4 Level 2 (Container) - verify draft từ review
- arc42 chapter 11 (Risks) update với findings mới
- ADR cho `packages/process` decision (Option A activate / Option B deprecate)
- ADR cho connector framework strategy
- ADR cho code RAG architecture
- ADR riêng cho mỗi major external dependency (MinerU/BGE/Milvus/Presidio/Speaches) với exit plan

### 5.2. aihub-b\*d

#### Concerns

**SDK version drift**

- _Concern_:
  - Drift 10 minor versions (v0.279.2 vs core v0.289.10)
  - Internal import violation `pipelines/snk_enrichment.py:2`
  - Patterns chưa extract về core (`resolve_selection()`, HITL helpers)
- _Direction_:
  - SDK upgrade plan với security delta audit
  - Extract reusable patterns về core
  - SDK versioning gate CI để block PR khi drift quá lớn

**Backup destination same VM**

- _Concern_:
  - Backup SeaweedFS chạy cùng VM với primary data
  - VM failure = mất cả primary cộng backup
  - Vi phạm 3-2-1 rule
- _Direction_:
  - Cron sync emergency ra Swiss-sovereign off-site (Infomaniak CH / Exoscale CH / Hetzner)
  - Long-term: cross-region replication

**Cohere reranking US/Canada**

- _Concern_:
  - Cohere là US/Canada vendor
  - Conflict với sovereignty story khi serve Swiss customers
- _Direction_:
  - ADR document trade-off (acceptable risk hoặc must migrate)
  - Hoặc migrate sang sovereign alternative (BGE local, Jina local)

**Storage multiplier 3.9x**

- _Concern_:
  - Production sizing 1 TB source → 5.1 TB total (3.9x multiplier)
  - 1.9 TB disk insufficient cho 2+ customers shared
  - Storage cost scale tuyến tính
- _Direction_:
  - Data partitioning strategy: sharding / time-based / customer-based / cold storage
  - ADR document chiến lược
  - Cold storage tier cho data ít access

**No test coverage on agents/pipelines**

- _Concern_:
  - Test coverage = 59 lines (1 utility function)
  - 3 agents cộng 4 pipelines hoàn toàn untested
  - Regression risk cao khi upgrade
- _Direction_:
  - Test plan baseline (smoke tests per agent / pipeline)
  - Integration test với staging data
  - Coverage threshold 60% cho new code

**Hardcoded customer config**

- _Concern_:
  - SNK_ANCHOR, BASE_PATH `/mnt/smb_b*d/30 GP/31 Kunden` hardcoded
  - Không deploy được customer khác
  - Khó test với data khác
- _Direction_:
  - Pydantic Settings từ env
  - Document config matrix per env

**Weak model JSON malformed**

- _Concern_:
  - Weak models (`gpt-oss-120b`, các small model) trả JSON sai format
  - Break downstream workflow steps
  - Team retry cùng prompt = same failure pattern
  - Cost runaway risk, không address root cause
- _Direction_:
  - **Structured output / JSON mode** (OpenAI `response_format`, function calling với schema)
  - Pydantic validation ở client
  - **Fallback chain** weak → strong model (cost-aware escalation)
  - **Golden test suite** cho JSON contract trong CI

**No resource limits docker-compose**

- _Concern_:
  - Containers không có CPU / memory limits
  - 1 container leak có thể OOM toàn host
- _Direction_:
  - Explicit resource limits per service
  - Profile-based sizing

#### Documentation deliverables

- arc42 12 chapters cho B\*D
- C4 Level 1 (System Context) cộng C4 Level 2 (Container): 3 agents cộng 4 pipelines cộng configs
- ADRs trả lời 10 design questions: Azure OpenAI sovereignty trade-off; customer/supplier data split; partitioning
  strategy; SMB base path rationale; SNK enrichment placement; regex utils placement; Cohere reranking choice; 6
  docker-compose separation; `snk_enrichment.py:2` import fix; test strategy

### 5.3. aihub-c\*c

#### Concerns

**SDK version drift (lớn hơn B\*D)**

- _Concern_:
  - Drift 15 minor versions (v0.274.3 vs core v0.289.10)
  - Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`
  - Custom tooling `switch_dependencies.py` thay standard uv workflow
  - Dual lock files (poetry.lock 84KB cộng uv.lock active)
- _Direction_:
  - SDK upgrade với security delta audit
  - Standardize uv workflow
  - Deprecate poetry.lock

**Backup destination same VM**

- _Concern_:
  - Same fatal pattern như B\*D
  - Backup cùng Azure VM với primary
  - VM failure = total loss
- _Direction_:
  - Tier 1 - emergency cron sync ra Swiss-sovereign storage
  - Tier 2 - Dagster scheduled replication
  - Tier 3 - cross-region replication với encryption

**Service account shared keys**

- _Concern_:
  - Jira / SharePoint / Confluence dùng service account shared key
  - Bypass least-privilege principle
  - Bypass per-user permissions từ source systems
- _Direction_:
  - Per-user OAuth delegated permissions
  - Source systems enforce ACL nguồn
  - Audit trail per user query

**SharePoint over-permissioned**

- _Concern_:
  - SharePoint Azure AD app-only `Sites.Read.All` tenant-wide
  - = super-admin level access
  - Access toàn bộ tenant data thay vì scoped sites
- _Direction_:
  - Scoped permission `Sites.Selected` per site
  - Document access matrix per site

**Hardcoded Jira config**

- _Concern_:
  - Jira URL, Service Desk ID, Request Type ID, Project ID hardcoded
  - Không deploy được instance khác
  - Khó test với fixture data
- _Direction_: Pydantic Settings từ env per deployment.

**Naming camouflage**

- _Concern_:
  - Alias `gpt-oss-120b` → `azure/gpt-5-nano` trong LiteLLM config
  - Developer / auditor đọc model name không biết underlying service
  - Sovereignty audit khó trace
- _Direction_:
  - Transparent naming convention (vd `azure-eu/gpt-5-nano`)
  - ADR document trade-off nếu cần alias

**Jira webhook không idempotent**

- _Concern_:
  - `JiraWebhookController` không có idempotency key check
  - Cùng event delivered 2x = 2 agent runs
  - Duplicate cost cộng inconsistent state
- _Direction_:
  - Idempotency key từ webhook event ID
  - Redis lock pattern

**Custom API extension chưa contribute lên core**

- _Concern_:
  - Jira webhook handler cộng Support Desk endpoint built trong C\*C
  - Pattern hữu ích cho customer khác
  - Locked-in trong customer scope
- _Direction_:
  - Extract về core như extension points
  - ADR decision when to extract (criteria: > N customers cần)

**Test coverage zero**

- _Concern_:
  - Không có thư mục `tests/`
  - 4 agents cộng 6 pipelines cộng custom API cộng `lib/common` hoàn toàn untested
  - Regression risk cao
- _Direction_:
  - Test plan baseline
  - Smoke tests per component
  - Integration test với staging Jira / Confluence / SharePoint

**External services cascade risk**

- _Concern_:
  - Hard dependency Jira / Confluence / SharePoint / Azure
  - Outage = full agent failure
  - Không có degraded mode
- _Direction_:
  - Circuit breaker per source
  - Cached fallback cho read paths
  - DR plan documented

**Data leak qua prompt-based isolation**

- _Concern_:
  - Multi-source data (Jira / Confluence / SharePoint) chưa isolate ở data layer
  - Team dùng prompt instructions để guide agent không trộn data
  - **Defensive layer ở wrong level**:
    - Prompt injection bypass dễ
    - RAG retrieval xảy ra **trước** khi LLM thấy prompt
    - LLM có thể trộn data trong reasoning ngay cả khi dặn không trộn
    - Không có audit trail forensic
- _Direction_: chuyển isolation xuống **data layer**:
  - Per-tenant Milvus collection
  - Per-user ACL filter ngay tại retrieval query
  - Pre-filter chunks theo permissions trước LLM context
  - Audit log forensic (xem `adr_020`)

**Per-user data access unclear**

- _Concern_:
  - Chưa rõ C\*C có enforce per-user access không
  - Service account shared key bypass per-user permissions
  - Risk user A thấy data user B
  - [GDPR Art. 32](https://gdpr-info.eu/art-32-gdpr/) (security of processing / access control) cộng
    [Art. 25](https://gdpr-info.eu/art-25-gdpr/) (privacy by design) violation
- _Direction_:
  - Per-user OAuth cho mọi source connector
  - ACL inheritance vào Milvus metadata
  - Retrieval-time filter
  - User access matrix documented

**Azure stack triple redundancy (DI cộng Foundry cộng core MinerU+LiteLLM)**

- _Concern_:
  - C\*C dùng Azure Document Intelligence cho parsing
  - cộng Azure AI Foundry cho LLM
  - Trong khi core đã có MinerU cộng LiteLLM
  - → pay 2x cost (Azure DI cộng Foundry tokens cộng core infra)
  - **Double sovereignty exposure** (cả 2 Azure service ngoài Thuỵ Sỹ)
  - Maintenance 2 stacks song song
  - Team phải master cả 2 ecosystems
- _Direction_:
  - **Standardize trên core stack**:
    - MinerU cho parsing (per ADR `2026_02_09`)
    - LiteLLM gateway cho LLM routing
  - Azure-specific feature → ADR business justification cộng deprecation plan
  - Migration roadmap:
    - DI → MinerU
    - Foundry → self-hosted vLLM hoặc Swiss LLM Cloud qua LiteLLM

#### Documentation deliverables

- arc42 12 chapters cho C\*C
- C4 Level 1 (System Context) cộng C4 Level 2 (Container): 4 agents cộng 6 pipelines cộng custom API cộng lib/common
- ADRs trả lời 13 design questions: Azure Foundry sovereignty; Azure DI vs MinerU; naming camouflage; multi-agent
  orchestrator pattern; custom API extension contribute path; service account vs per-user OAuth; Azure AD B2C vs
  Keycloak; Azure IaC vs Pulumi; dual lock files migration; `switch_dependencies.py` rationale; hardcoded Jira IDs;
  `lib/common` extraction criteria; `RetrievalAgentInTheLoop` import fix
- Technical answers: data quality strategy at ingest; RAG improvement strategy; idempotency solution; Milvus upsert;
  document ACL inheritance; custom API monitoring; DR plan; test coverage plan; large data ingestion strategy; cost
  monitoring Azure Foundry+DI

### 5.4. Other customer projects (placeholders pending input)

Các customer projects sau đang trong scope review nhưng chi tiết deployment, version, components, data sources,
sovereignty status, test coverage chưa được cung cấp. Mỗi customer sẽ có structure tương tự §5.2 B*D / §5.3 C*C khi info
available.

| Customer         | Status placeholder        |
| ---------------- | ------------------------- |
| aihub-Ig\*s      | TBD - awaiting team input |
| aihub-W\*P       | TBD - awaiting team input |
| aihub-Dem\*scope | TBD - awaiting team input |
| aihub-Balmer-E\* | TBD - awaiting team input |

**Per-customer info cần cung cấp** (mỗi customer):

- Status (production date / pilot / onboarding)
- Core version + drift số minor versions
- Components (số agents / pipelines / custom APIs)
- Deployment generation (Gen 1 Azure manual / Gen 2 Infomaniak Ansible Pull / khác)
- Data sources (SharePoint / Jira / SMB / custom / etc.)
- LLM provider + sovereignty annotation
- Identity provider (Keycloak / Azure AD / SaaS)
- Off-site backup status
- Own arc42 + ADRs available?
- Test coverage estimate
- Key concerns / blockers specific to customer
- Migration plan Gen 1 → Gen 2 (nếu applicable)

Khi info available, mỗi customer sẽ expand thành section riêng tương tự B*D/C*C: Concerns (categorized) + Documentation
deliverables.

### 5.5. Cross-cutting (Infrastructure, Process, Governance)

#### Concerns

**Infrastructure topology undocumented** _[Resolved for Gen 2]_

- _Concern_:
  - Network zones chưa documented
  - Container resource sizing không có matrix
  - Service dependencies không rõ
  - IaC chưa standardize
- _Status_: **Resolved cho Gen 2** - aihub-ops/setup README document đầy đủ OpenStack network zones, security groups,
  volume topology, VM sizing. aihub-playbook standardize qua Ansible roles.
- _Direction_: B*D/C*C vẫn cần HLAD cộng network zone diagram cho Gen 1; migrate sang Gen 2 cùng documentation pattern.

**Operations runtime undocumented** _[Resolved for Gen 2]_

- _Concern_:
  - Secret management cộng rotation chưa procedure
  - TLS certificate lifecycle không có owner
  - Time / locale handling không document
- _Status_: **Resolved cho Gen 2** - Ansible Vault encrypted (AES256) với auto-gen via `vault-vars-routing.yml`; Traefik
  \+ Let's Encrypt ACME tự động cert lifecycle (acme_email config); ops runbook trong aihub-ops/setup README cộng
  aihub-playbook AGENTS.md.
- _Direction_: B*D/C*C cần migrate sang Gen 2 pattern; deploy key rotation policy explicit (current AGENTS.md vague
  "periodically"); time/locale standardization cho Gen 2 còn pending.

**Supply chain visibility missing** _[Open]_

- _Concern_:
  - Không có SBOM
  - Không có image signing
  - Không có vuln scanning
  - Không có log aggregation topology
- _Status_: Log aggregation **partial fix** qua SigNoz OTEL collector (Gen 2); SBOM/signing/vuln scan vẫn chưa có.
- _Direction_:
  - syft (SBOM generation)
  - cosign (image signing)
  - trivy (vuln scan)
  - Tất cả integrated trong CI

**Off-site backup strategy** _[Partial fix for Gen 2]_

- _Concern_:
  - Cả B*D và C*C backup cùng VM
  - Vi phạm 3-2-1 rule
  - Hardware failure = total loss
- _Status_: **Partial fix cho Gen 2** - Restic backup ra OpenStack Swift container (`vol-backup`) đã đạt "off-host"
  component của 3-2-1; retention policy documented (24h/7d/4w/12m/7y); restore tested qua `restore-restic-backup.sh`.
  **Còn thiếu**: cross-provider replication (Swift cùng Infomaniak với primary VM).
- _Direction_:
  - **B*D/C*C**: migrate sang Gen 2 (urgent) - cron sync emergency ra Swiss-sovereign off-site
  - **Gen 2 enhancement**: cross-provider tier (Infomaniak Swift → Hetzner / Exoscale / bare-metal secondary)
  - Reference: `adr_030_offsite_backup_replication.md`

**No RTO/RPO documented cộng no DR drill**

- _Concern_:
  - Recovery objectives chưa định nghĩa
  - Không có automated restore drill
  - DR capability không verified
- _Direction_:
  - Document RTO/RPO per service tier
  - Monthly DR drill automated
  - Restore verification trong CI

**No K8s migration path**

- _Concern_:
  - Docker Compose single-server ceiling
  - Không có Helm chart
  - Không có StatefulSet pattern cho stateful services
- _Direction_:
  - K8s migration plan
  - Helm chart cho mọi services
  - StatefulSets cho data layer
  - HPA cho stateless services

**No customer onboarding template** _[Resolved for Gen 2 deployment]_

- _Concern_:
  - Customer mới phải reinvent arc42
  - Reinvent ADRs
  - Reinvent deployment scripts
  - Tốn weeks cho structure trước khi build feature
- _Status_: **Deployment template resolved** qua `setup-aihub.sh` + 3-repo pattern (aihub-playbook + aihub-core +
  aihub-\{customer_id}); automated VM provisioning trên OpenStack; SSH deploy keys + Ansible Vault auto-setup. **Docs
  template (arc42 + ADRs) vẫn chưa có**.
- _Direction_:
  - arc42 12 chapters skeleton template (vẫn còn thiếu)
  - ADR list (required decisions) template
  - Customer repo structure docs cho aihub-\{customer_id}

**SDK versioning policy chưa định nghĩa**

- _Concern_:
  - Không có max version drift policy
  - Không có security patch SLA
  - Không có CI gate blocking outdated customers
  - Không có breaking change communication
- _Direction_:
  - Formal SDK versioning policy document
  - CI gate (block PR nếu drift > N versions)
  - Security patch SLA documented (vd critical = 7 days)

**No documentation gate trước go-production**

- _Concern_:
  - Customer launch không required arc42
  - Không required ADRs
  - Không có sign-off checklist
  - Docs gap chỉ surface khi audit
- _Direction_:
  - Documentation gate trong release process
  - Required artifacts list
  - Sign-off matrix per stakeholder

**No ADR compliance audit process**

- _Concern_:
  - Major architectural decision không required ADR before merge
  - Architecture drift theo thời gian
  - False claim risk
- _Direction_:
  - ADR compliance gate trong PR workflow
  - Lint rule check ADR exist khi touch architecture path

**No documentation drift detection** _[Partial fix for env vars]_

- _Concern_:
  - Docs claim không match code (Presidio, GDPR examples)
  - Discovered late khi audit
- _Status_: **Partial fix** - `check_env_drift.py` + nightly GitHub Actions workflow (`vault-vars-routing-drift.yml`)
  detect env vars drift giữa aihub-core `.env.template` và aihub-ops `vault-vars-routing.yml`. **Chỉ cover env vars**,
  chưa cover prose docs claims.
- _Direction_:
  - Mở rộng drift detection ra docs claim (Presidio, GDPR, audit log)
  - Claim parser cộng code grep cross-check
  - Fail build nếu claim không verify được

**No customer-facing SLA**

- _Concern_:
  - Không có Service Level Agreement formal cho customer
  - Uptime commitment chưa định nghĩa (vd 99.5% / 99.9% / 99.95%)
  - Response time guarantees per endpoint class chưa có (chat / RAG query / ingest)
  - Incident response time per severity chưa có
  - Scheduled maintenance window policy chưa có
  - Downtime credit / refund policy chưa có
  - Khi customer outage, không có baseline để measure breach
  - SLA không link tới HA architecture (99.9% yêu cầu HA stack, 99.95% yêu cầu multi-AZ)
- _Direction_:
  - **Define SLA tiers per customer plan** (vd Bronze 99.0% / Silver 99.5% / Gold 99.9%):
    - Uptime commitment per tier
    - Response time per endpoint class
    - Support response time per severity
    - Credit / refund policy
  - **Map tier → infrastructure requirement**:
    - Bronze - single-VM
    - Silver - HA single-AZ
    - Gold - multi-AZ K8s
  - Link RTO/RPO matrix vào SLA targets
  - Public status page (statuspage.io / Atlassian Statuspage / self-hosted Cachet)
  - Monthly SLA report tự động từ observability stack

#### Gen 2 deployment pattern (Ansible Pull / OpenStack)

**3-repo coordination version compatibility**

- _Concern_:
  - 3 repos cần sync state: `aihub-playbook` (infra) + `aihub-core` (apps) + `aihub-{customer}` (secrets)
  - Nếu `aihub-core` upgrade breaking nhưng `aihub-playbook` chưa update → next Ansible Pull (15 min sau) break VM
  - Tương tự: customer vault schema change → playbook không handle = deployment fail
  - Hiện tại không có compatibility matrix; không có CI gate test combos
- _Direction_:
  - **Version compatibility matrix** documented (vd playbook v1.5+ supports core v0.280-v0.290)
  - **CI integration test** spawn ephemeral VM với combo (playbook + core + customer template) để validate
  - **Pin core version** trong playbook config (thay vì luôn `latest`)
  - Release coordination: breaking change ở core → playbook PR cùng release cycle

**GitHub là deployment SPOF**

- _Concern_:
  - VMs fetch aihub-core release archive qua GitHub REST API mỗi 15 min
  - AGENTS.md xác nhận: "no local fallback if api.github.com is unreachable - sustained GitHub outages block deploys"
  - `GHCR_TOKEN` cần đúng 2 scopes (`read:packages` + `contents:read`); fine-grained PAT thiếu sẽ fail
  - GitHub rate limit (5000 req/hour cho authenticated) - N customers × 4 pulls/hour = N×4 requests/customer
- _Direction_:
  - **Local mirror / private registry fallback** cho release tarballs
  - Cache release tarballs locally trên VM (chỉ pull khi version thay đổi)
  - Document GitHub dependency trong DR plan
  - Monitor rate limit usage; consider GitHub Enterprise mirror nếu scale lớn

**Same-cloud backup (Restic → Swift cùng Infomaniak)**

- _Concern_:
  - Primary VM trên Infomaniak OpenStack
  - Backup Restic → Swift cùng Infomaniak
  - Infomaniak region outage / account suspension / billing issue = mất cả 2
  - Đạt off-host trong 3-2-1 rule nhưng **chưa đạt off-site / off-provider**
- _Direction_:
  - **Cross-provider tier** (Tier 2 trong adr_030):
    - Primary: Infomaniak Swift
    - Secondary: Hetzner Storage Box / Exoscale Object Store / Backblaze B2 / bare-metal NAS
  - Rclone job replicate Swift → secondary daily
  - Document cloud-provider-failure scenario trong DR runbook

**Ansible Pull 15-min cadence cho hot-fix**

- _Concern_:
  - Security patch push lên main = chờ tới 15 min trước khi VM apply
  - Trong outage cần manual `systemctl start infra-pull.service` mỗi VM
  - N customers = N SSH sessions để emergency deploy
  - Không có centralized emergency trigger
- _Direction_:
  - **Emergency push mechanism**:
    - Webhook trigger từ GitHub Actions sau security release
    - Hoặc NATS broadcast subject `aihub.infra.emergency-pull` → VMs subscribe và trigger ngay
    - Hoặc SSH fan-out script central
  - Document emergency deploy SLA (vd P0 security patch deploy < 5 min từ release)
  - Manual override procedure trong incident response runbook

**SigNoz Cloud data sovereignty**

- _Concern_:
  - SigNoz collector role default `signoz_region: "eu"` - gửi observability data ra SigNoz Cloud (EU region)
  - Observability data có thể chứa: user IDs, tenant identifiers, prompt fragments trong traces, error messages chứa PII
  - Swiss customer data → ngoài tenant infra → vi phạm sovereignty story khi serve regulated industries
  - SigNoz Cloud không có Swiss region (chỉ US / EU / India)
- _Direction_:
  - **Self-hosted SigNoz** alternative (full stack: query service + clickhouse + collector trong Swiss VM)
  - Hoặc **Grafana Cloud EU region** với data residency guarantees
  - Hoặc **Local Loki + Tempo + Mimir** stack tự host
  - Document trace data sanitization: redact PII / user IDs trước khi export
  - ADR riêng cho observability data sovereignty trade-off

**Vault password storage on VM**

- _Concern_:
  - Ansible Vault password stored on VM filesystem (cần để decrypt mỗi pull)
  - VM compromise = full vault unlock = leak mọi secrets (API keys, DB passwords, OAuth secrets, SUPERUSER_TOKEN)
  - VM snapshot exposure = vault password trong snapshot
  - Không có short-lived token / HSM-backed pattern
- _Direction_:
  - **HSM / KMS-backed vault password**:
    - OpenStack Barbican (key management service) - fetch tại boot
    - Hoặc Azure Key Vault / HashiCorp Vault retrieval at boot
  - **Short-lived decryption token** (vd 1 hour TTL, auto-refresh)
  - Audit log access tới vault password
  - VM snapshot encryption with separate key (not stored on VM)

**B*D/C*C migration Gen 1 → Gen 2**

- _Concern_:
  - B*D/C*C vẫn Gen 1 (Azure VM + shell scripts manual)
  - Backup vẫn fatal pattern (same VM)
  - Security patches không auto-deploy
  - Customer Registry phản ánh discrepancy với Customer #3+ (Gen 2)
  - Migration path chưa documented; risk migration làm break customer running production
- _Direction_:
  - **Migration playbook documented**:
    - Phase 1: Provision Gen 2 VM trên Infomaniak (parallel với Gen 1 Azure)
    - Phase 2: Data migration (volume snapshot → restore on Gen 2)
    - Phase 3: DNS cutover với rollback plan
    - Phase 4: Decommission Gen 1
  - **Pilot migration** với B*D (smaller surface area) trước C*C
  - Customer communication: SLA window, downtime expectation, rollback guarantee
  - Skill transfer cho customer ops team (Azure portal → Infomaniak OpenStack)

**Deploy key rotation policy implicit**

- _Concern_:
  - AGENTS.md mention "Rotate deploy keys and vault passwords periodically" nhưng:
    - Không có period concrete (quarterly? yearly?)
    - Không có automation script
    - Không có audit log "key X rotated on date Y"
    - 3 deploy keys per VM (playbook + core + customer) → manual rotation phức tạp
  - Compromised key có thể không phát hiện được
- _Direction_:
  - **Formal rotation policy** (vd quarterly cho deploy keys, monthly cho vault passwords)
  - **Automation script**:
    - Generate new key
    - Push qua GitHub API tới repo
    - Push qua `setup-aihub.sh` re-run tới VM
    - Revoke old key
    - Log rotation event
  - Audit dashboard: key age, last rotation date per VM
  - Alert nếu key > X tháng không rotate

**AI evaluation framework (Core/B*D/C*C)** _[Strategic]_

- _Concern_: Khi eval dataset cho RAG/agent ra kết quả kém, team approach: **tweak prompt cộng retry** → local
  optimization, không address root causes.
- _Impact_: Prompt tuning không transferable khi đổi model; không systematic A/B; không regression detection; không phân
  biệt retrieval miss vs generation kém.
- _Direction_: **Multi-lever framework** thay vì chỉ prompt - **Retrieval** (BGE-M3 tuning, hybrid dense cộng BM25,
  query rewriting, BGE reranker); **Chunking** (semantic, parent-document, metadata enrichment); **Context** (top-k
  tuning, context compression); **Generation** (model routing easy→cheap hard→strong, few-shot, CoT); **Eval loop**
  (Langfuse datasets cộng RAGAS metrics faithfulness/relevancy/context-precision, LLM-as-judge automated, regression
  test PR); **Fine-tuning/DPO** khi prompt cộng retrieval đạt ceiling. **Mỗi tweak đo bằng eval dataset, không cảm
  tính.**

#### Documentation deliverables

- Customer onboarding template (arc42 cộng ADRs cộng deployment scripts)
- SDK versioning policy formal document
- Documentation gate checklist
- ADR compliance gate procedure
- Documentation drift detection CI workflow
- Multi-customer pattern extraction roadmap

______________________________________________________________________

## 6. Recommendations

> High-level direction. Implementation chi tiết, cost, ownership sẽ deep dive trong các sessions tiếp theo.

### 6.1. Immediate decisions

- **Sovereignty decision**: chọn Option A (self-hosted local LLM) / B (hybrid với updated ADR) / C (per-customer tier)
- **Review "Swiss Sovereign AI" marketing positioning** — note: claim này hiện chưa align hoàn toàn với reality (B*D/C*C
  dùng Azure cho LLM); cân nhắc soften wording hoặc clarify scope cho tới khi sovereignty path quyết định xong
- **Backup Tier 1 emergency mitigation**: cron sync ra Swiss-sovereign off-site target (Infomaniak/Exoscale CH)
- **Wire UsageLimits middleware**: block LLM cost runaway risk
- **Quyết định fate `packages/process`**: delete hoặc activate
- **Audit security delta** từ v0.274.3 → v0.289.10, force-upgrade customers nếu có security patches

### 6.2. Strategic priorities

- **Multi-tenant data layer**: NATS namespace, Mongo `tenant_id`, Milvus per-tenant collection, Valkey key prefix
- **Security hardening**: SecureMCPExecutor, Document ACL inheritance, audit log entity, mTLS service-to-service
- **Per-user OAuth** cho Jira/SharePoint/Confluence connectors (thay service account shared keys)
- **K8s migration**: Helm chart, StatefulSets cho stateful services, HPA cho stateless
- **Milvus cluster mode**: chuẩn bị multi-customer scale
- **DB migration framework**: versioned scripts cho upgrade safety
- **Off-site backup full**: Tier 2 configurable target + Tier 3 Dagster cross-region replication
- **Observability stack**: Prometheus + AlertManager + dashboards + SLI/SLO
- **Penetration test bên thứ 3** sau khi security hardening done

### 6.3. Documentation deliverables (cần team owner)

- **Core platform**: HLAD, C4 L1/L2, update false claims docs, audit log + GDPR ADRs
- **Customer aihub-b\*d**: arc42 12 chapters, C4 L1/L2, 10 ADRs trả lời design questions
- **Customer aihub-c\*c**: arc42 12 chapters, C4 L1/L2, 13 ADRs trả lời design questions, technical questions
- **Infrastructure**: deployment topology + operations runtime + observability/supply chain
- **Customer onboarding template** cho customer mới

### 6.4. Process và governance

- **SDK versioning policy** chính thức (max drift, security patch SLA, CI gate)
- **Documentation gate** trước customer go-production (sign-off checklist)
- **ADR compliance gate** trong development workflow (major decision = required ADR)
- **Documentation drift detection** trong CI (catch claims không match code)
- **Pattern extraction roadmap**: customer patterns → core (multi-agent orchestrator, industry connectors)

______________________________________________________________________

## References và Standards

Document này reference các framework, standard, regulation sau:

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

**Document loại**: Overview (for stakeholders)
