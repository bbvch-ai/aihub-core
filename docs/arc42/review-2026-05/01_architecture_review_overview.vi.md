# Architecture Review: Overview

**Loại document**: Executive Summary cho stakeholders.

**Đối tượng đọc**: C-level, Product, Business, Compliance/Legal, Architects, Technical Leads.

**Phạm vi**: Swiss AI Hub ecosystem gồm:

- `aihub-core` - platform application stack
- **Customer deployments**:
  - `aihub-b*d`, `aihub-c*c` - Gen 1 (Azure VM + shell scripts), đã production
  - `aihub-Dem*scope`, `aihub-W*P`, `aihub-F*H` - Gen 1 (Azure / manual VM), đã production
  - `aihub-Ig*s`, `aihub-Balmer-E*` - TBD (deployment generation, version, status pending team input)
- **Infrastructure repos (Gen 2)**:
  - `aihub-playbook` - Ansible Pull infrastructure-as-code (every 15-min reconcile)
  - `aihub-ops` - VM provisioning automation cho OpenStack (cloud-init + setup script)
  - `aihub-{customer_id}` - per-customer encrypted secrets + custom config repos (template pattern)
- **Kubernetes deployment (Gen 3, mới nổi)**:
  - `aihub-k8s` - Terraform (Azure AKS + Stoney OpenStack Magnum) + 2 Helm chart
    (`aihub-common`, `aihub-tenant`) cho **multi-tenancy theo namespace** và scale-out theo chiều ngang. Cả hai
    chart khai báo `appVersion: "0.1.0"` và pull image qua `${CORE_VERSION:-latest}` — chart **không** pin
    aihub-core version cụ thể; phiên bản core đang chạy là giá trị `CORE_VERSION` lúc apply. Các tenant
    `tenant1`, `jointcreate`, `postgres-test` chỉ là test/sample - chưa có customer production migrate sang.

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

| Thành phần                  | Version        | Ghi chú                                                                                                                                                                                                          |
| --------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| aihub-core (HEAD on `main`) | v0.290.4       | Application stack - Latest dev (`pyproject.toml:3`); 47 ADR trong `docs/arc42/decisions/`                                                                                                                          |
| aihub-b\*d dùng core        | v0.279.2       | Customer Gen 1 - Azure VM + shell scripts, đi sau core 11 minor                                                                                                                                                    |
| aihub-c\*c dùng core        | v0.274.3       | Customer Gen 1 - Azure VM + shell scripts, đi sau core 16 minor, đi sau b\*d 5 minor                                                                                                                               |
| aihub-Ig\*s                 | TBD            | Customer - chi tiết version + deployment gen pending                                                                                                                                                               |
| aihub-W\*P                  | v0.255.6       | Customer Gen 1 - manual VM (docker-compose copy-paste), đi sau core 35 minor                                                                                                                                       |
| aihub-Dem\*scope            | v0.246.4 [^1]  | Customer Gen 1 - Azure VM (Pulumi theo README; IaC code không có trong repo), 44 sau                                                                                                                              |
| aihub-F\*H                  | v0.186.0       | Customer Gen 1 - Azure VM (Pulumi đã commit trong `.iac/iac_azure/`), 104 sau                                                                                                                                      |
| aihub-Balmer-E\*            | TBD            | Customer - chi tiết version + deployment gen pending                                                                                                                                                               |
| aihub-playbook              | HEAD on `main` | Infra Gen 2 - Ansible Pull (every 15 min), 3-repo coordination; **7 role** (`docker_runtime`, `traefik_proxy`, `signoz`, `aihub_application`, `os_backups`, `custom_vars_sync`, `restore_os_backup`)                |
| aihub-ops                   | HEAD on `main` | VM provisioning automation (OpenStack Infomaniak)                                                                                                                                                                  |
| aihub-\{customer_id}        | per-customer   | Encrypted Ansible Vault + custom config (template repo pattern)                                                                                                                                                    |
| aihub-k8s                   | HEAD on `main` (Helm chart `appVersion 0.1.0`; image qua `${CORE_VERSION:-latest}` — chart KHÔNG pin core version) | Infra Gen 3 - Terraform (Azure AKS + Stoney OpenStack Magnum) + Helm (`aihub-common` + `aihub-tenant`); namespace-per-tenant; phiên bản core deploy là giá trị operator set lúc apply |

[^1]: SDK pin của Demoscope không có trong `aihub-demoscope/pyproject.toml`; không có git dependency `swiss-ai-hub-*`
và docker-compose image không tag version. Số `v0.246.4` được carry over từ snapshot review trước, chờ xác nhận
operational (CI logs / deploy manifests).

Cảnh báo:

- Cả 5 Gen 1 customer (B*D/C*C/W*P/Dem*scope/F*H) chạy SDK version khác nhau, tất cả đều cũ hơn core. Không có policy
  ép upgrade. Khoảng drift: 11 → 104 minor (F*H ở v0.186.0 là drift lớn nhất, đi sau core 104 minor).
- Security patches trên `main` không tự lan xuống Gen 1 customers; Gen 2 (Ansible Pull) auto-deploy trong 15 min.
- Migration path Gen 1 → Gen 2 (Azure manual → Infomaniak OpenStack + Ansible) chưa documented cho bất kỳ B*D / C*C /
  W*P / Dem*scope / F*H nào.
- **Gen 3 (`aihub-k8s`) đã đóng một phần gap "No K8s migration path"** nêu ở §3.1 Item #20: Helm chart, Terraform cho
  2 cloud (Azure AKS + Stoney OpenStack Magnum), CloudNativePG + Keycloak Operator + cert-manager + NGINX Ingress đã
  được commit. **Tuy nhiên**: chưa có customer production nào trên path này (mới chỉ có tenant `tenant1`,
  `jointcreate`, `postgres-test` ở dạng test); Stoney Magnum có limitation đã ghi nhận là `node_count` không update
  được sau khi tạo cluster; Milvus mặc định chạy standalone (cluster scale-out mode có document nhưng optional);
  cách Keycloak Operator watch cross-namespace được chính tài liệu gọi là "community workaround, not a first-class
  Keycloak support statement"; **và chart không pin aihub-core version cụ thể** — chỉ pull image tag mà
  `CORE_VERSION` resolve tới (xem proposed `adr_040`).

______________________________________________________________________

## Mục lục

1. [Tóm tắt](#1-t%C3%B3m-t%E1%BA%AFt)
2. [Sơ đồ hệ sinh thái](#2-s%C6%A1-%C4%91%E1%BB%93-h%E1%BB%87-sinh-th%C3%A1i)
3. [Priority items cho go-live (CRITICAL + HIGH)](#3-priority-items-cho-go-live-critical--high) 3.1.
   [aihub-core (Platform)](#31-aihub-core-platform) 3.2. [aihub-b\*d](#32-aihub-bd) 3.3. [aihub-c\*c](#33-aihub-cc) 3.4.
   [aihub-Dem\*scope](#34-aihub-demscope) 3.5. [aihub-W\*P](#35-aihub-wp) 3.6. [aihub-F\*H](#36-aihub-fh)
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
| Event-driven architecture (NATS JetStream cộng Swiss AI Agent Protocol)                                                                                                                                           | Sovereignty violation xuyên qua customers - B*D Azure Sweden, C*C Azure Foundry SUI+SWE, F*H Azure SUI + Azure AI Search; W*P region chưa verified (chỉ env-var); Dem*scope partial (Azure SUI + local vLLM). Chỉ Dem*scope có dấu hiệu sovereign-LLM |
| 47 ADRs document major decisions (trong `docs/arc42/decisions/`)                                                                                                                                                  | Gen 1 customer backup destination cùng VM (vi phạm [3-2-1 rule](https://www.cisa.gov/news-events/news/data-backup-options)); Gen 2 partial fix qua Restic→Swift      |
| OpenTelemetry observability stack (traces cross-service)                                                                                                                                                          | No HA architecture - mọi stateful service single-instance (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd)                                                              |
| Agent framework support common enterprise AI patterns (conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution sandbox, browser automation) | AI use case scope chưa documented trong ADR, claim coverage không defensible cho audit; vision / predictive analytics / fine-tuning out of scope nhưng chưa explicit |
| CI/CD đầy đủ (lint, semantic-pr, build per package)                                                                                                                                                               | UsageLimits class defined nhưng không enforce → LLM cost runaway risk                                                                                                |
| Hierarchical permission template cộng AccessChecker tenant-ceiling (BDD tested)                                                                                                                                   | AuditLogEntity missing, GDPR right-to-erasure không implementable, false docs claims                                                                                 |
| LiteLLM gateway abstract LLM provider (swap dễ)                                                                                                                                                                   | Customer SDK drift trên **5 production customers**: B*D 11, C*C 16, W*P 35, Dem*scope 44, F*H 104 minor sau core - không có versioning policy hay CI gate                                                  |
| Dagster pipeline orchestration với asset lineage                                                                                                                                                                  | No customer-facing SLA, no alerting infra; chỉ có Slack notification on Ansible Pull failure                                                                         |
| License compliance OK (402 Python + 993 npm + 33 Docker images approved)                                                                                                                                          | Single-server ceiling cho Gen 1 / Gen 2 (chỉ Docker Compose) - được giảm nhẹ một phần bởi **Gen 3 `aihub-k8s`** mới nổi (Helm + Terraform, namespace-per-tenant), nhưng chưa có prod customer migrate sang |
| 47 ADRs cộng existing arc42 chapters cho platform                                                                                                                                                                 | Customer docs gap - **không có customer nào (B*D / C*C / W*P / Dem*scope / F*H) có arc42 hoặc ADRs riêng** (5 customer, 0 docs)                                              |
| Hierarchical scoping protocol (Thread → Display → Run)                                                                                                                                                            | Connector framework thiếu - mỗi customer tự build (O(N×M) onboarding cost)                                                                                           |
| Multi-language i18n cho UI (DE/EN/FR/IT)                                                                                                                                                                          | Presidio chỉ DE, multilingual PII gap cho Swiss FR/IT/EN                                                                                                             |
| **Gen 2 deployment: Ansible Pull self-configuring VMs (15-min auto-reconcile)**                                                                                                                                   | **Cả 5 customer đều vẫn Gen 1** (Azure manual hoặc copy-paste VM) - chưa có migration plan sang Gen 2 hay Gen 3 (`aihub-k8s`) cho bất kỳ customer nào                |
| **Infomaniak OpenStack - Swiss-sovereign cloud cho Gen 2**                                                                                                                                                        | Restic → Swift cùng cloud provider Infomaniak; chưa cross-provider replication                                                                                       |
| **3-repo coordination pattern (playbook/core/customer) - separation of concerns**                                                                                                                                 | 3-repo version compatibility chưa có matrix / CI gate test combos                                                                                                    |
| **Customer onboarding template (`setup-aihub.sh`)** automated VM provisioning                                                                                                                                     | Ansible Pull 15-min cadence chậm cho hot-fix; GitHub dependency = deploy SPOF                                                                                        |
| **Ansible Vault encrypted secrets + auto-gen random via vault-vars-routing.yml**                                                                                                                                  | Vault password stored on VM filesystem - VM compromise = full unlock                                                                                                 |
| **Traefik + Let's Encrypt ACME** tự động SSL cert lifecycle                                                                                                                                                       | Deploy key rotation policy implicit ("periodically"), không automation / audit                                                                                       |
| **SigNoz OTEL collector role** (host metrics + OTLP traces + journald)                                                                                                                                            | SigNoz Cloud region "eu" - chưa rõ data sovereignty implication                                                                                                      |
| **Env vars drift detection CI** (`check_env_drift.py` nightly)                                                                                                                                                    | Drift check chỉ cho env vars, không cover docs claims                                                                                                                |
| Langfuse cost tracking per LLM call                                                                                                                                                                               | No per-tenant cost attribution → showback impossible                                                                                                                 |
| Open-source self-hosted positioning                                                                                                                                                                               | Open-source dependency lock-in (parser/embedding/reranker/vector store chưa abstraction)                                                                             |
| BDD test integration với real NATS                                                                                                                                                                                | Test coverage qua 5 customer: **ZERO ở Dem*scope, W*P**; **C*C có 3 file / 788 dòng nhưng chỉ trong `log_analysis_agent`** (3 agent khác + 6 pipeline + custom API + `lib/common` chưa test); 58 dòng ở B*D; 5 `test_*.py` + 5 BDD `.feature` ở F*H |
| Trace context propagate qua NATS message headers                                                                                                                                                                  | Bot scope không OTEL → trace gãy ở bot boundary                                                                                                                      |
| Pulumi IaC defined cho core (superseded by Ansible Pull cho Gen 2); **Gen 3 `aihub-k8s` bổ sung Terraform + Helm + CloudNativePG + Keycloak Operator cho AKS / Stoney Magnum** | K8s path đã commit nhưng chưa được prove ở production; Pulumi code vẫn không có trong `aihub-core`; chưa có ADR nào adopt `aihub-k8s` là Gen 3 official path; **Helm chart KHÔNG pin core version** (`appVersion: "0.1.0"`, image qua `${CORE_VERSION:-latest}`) — xem proposed `adr_040` |
| **F\*H đã commit Pulumi IaC** (10 deploy units: agents / ai / api / bot / dagster / nats / network / openwebui / phoenix / stores) - IaC tốt nhất trong 3 customer mới                                                                                                                                                | **Dem\*scope nêu Pulumi trong README nhưng code `.iac/` KHÔNG commit** lên repo; W\*P không có IaC nào cả (thủ công `cp docker-compose.latest.yml /opt/docker/config/bbv/`)                            |
| **`aihub-k8s` lần đầu mang lại multi-tenancy thực sự** - namespace-per-tenant, realm-per-tenant (Keycloak), DB-per-tenant (CNPG), Milvus DB-per-tenant, bucket-prefix-per-tenant (SeaweedFS)                                                                                                                       | F\*H **monkey-patch LlamaIndex** ở import time (`lib/common/register_openai_models.py` chỉnh third-party globals để register tên GPT-5); hành vi phụ thuộc import order; sẽ rơi khi SDK upgrade        |
| **Chart `aihub-k8s` pull qua `${CORE_VERSION:-latest}`** — operator có thể đặt khớp HEAD core hiện tại `v0.290.4` (drift cực thấp nếu pin một version mới); chưa có policy chart-level pin (xem proposed `adr_040`)                                                                                              | F\*H dùng **Azure AI Search thay vì Milvus** - vendor lock-in + double inference cost (AI Search query + LLM call); cùng pattern với §3.3 C*C "Azure stack triple redundancy" (xem proposed `adr_039`) |
| Dem\*scope chạy **local vLLM** (Gemma-3 12b/27b + gte-Qwen2 embedding + bge-reranker) - customer duy nhất có sovereign-LLM stack một phần                                                                                                                                                                              | **W\*P TLS private key được commit lên git** (`wpe.ai-agents.ch+1-key.pem` đang track cùng cert tên production-domain); chỉ `.env` được đặt trong `.gitignore`                                          |
| F\*H có **evaluation framework** riêng (`evaluation/` với own evaluator + testset + Excel test catalogue)                                                                                                                                                                                                              | Stack divergence: Dem\*scope và F\*H vẫn dùng **MongoDB + Redis + Phoenix v10.0.4** (pre-Langfuse ADR `2026_02_10`), khác với core hiện tại dùng FerretDB + Valkey + Langfuse                          |
| **C4 model** đã có (`03_c4_diagrams.md`): L1 + 3×L2 + 4×L3 + 5 sequence + deployment + multi-customer topology, cover Platform + B*D + C*C; thêm per-customer C4 cho Platform / B*D / C*C / Dem*scope / W*P / F*H trong folder `c4/`                                                                                | **C4 chưa có cho Dem*scope / W*P / F*H** trước đó (3/5 prod customer) — được lấp bởi folder `c4/` mới trong review này                                                                                |
| C*C `log_analysis_agent` có test suite riêng (3 file / 788 dòng, gồm integration + extract logs)                                                                                                                                                                                                                       | C*C deep-import violation: `agents/chat_agent/chat_agent/ChatAgent.py` reach `swiss_ai_hub.core.generative_ai.{chat_history,guards}` và `swiss_ai_hub.core.i18n.locale_handler` (bypass public API) — xem proposed `adr_038` |

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
    subgraph CORE["Swiss AI Hub Core (aihub-core v0.290.4)"]
        direction TB
        CorePkgs["packages/<br/>core • agent • api • pipeline<br/>bot • backup • web • process"]
        CoreADR["47 ADRs"]
        CoreInfra["30+ containers<br/>per deployment"]
    end

    subgraph B*D["aihub-b*d v0.279.2 (drift 11 minor)"]
        direction TB
        B*DAgents["Agents (3)<br/>b*d · expert_rag · expert_asking"]
        B*DPipes["Pipelines (4)<br/>customers × 2-stage<br/>suppliers × 2-stage"]
        B*DCfg["Configs (16 services)<br/>SMB path hardcoded<br/>SNK enrichment"]
        B*DExt["External: Azure OpenAI (Sweden)<br/>Cohere reranking<br/>SMB share"]
    end

    subgraph C*C["aihub-c*c v0.274.3 (drift 16 minor)"]
        direction TB
        C*CAgents["Agents (4)<br/>chat · jira · log<br/>retrieval_orchestrator"]
        C*CPipes["Pipelines (6)<br/>jira/confluence/sharepoint<br/>× 2-stage"]
        C*CAPI["Custom API<br/>Jira webhook<br/>Support Desk"]
        C*CLib["lib/common/<br/>events · types · ops"]
        C*CExt["External: Azure Foundry SUI+SWE<br/>Azure Doc Intelligence<br/>Azure AD B2C · Key Vault · VM<br/>Jira · Confluence · SharePoint"]
    end

    subgraph DEMOSCOPE["aihub-Dem*scope v0.246.4* (drift 44 minor, *SDK pin chưa verify)"]
        direction TB
        DemoAgents["Agents (2 pkg / 4 deployed)<br/>persona_agent · multi_personas_agent<br/>(mỗi cái có public + private variant)"]
        DemoPipes["Pipelines (1)<br/>personas (imputation + insertion jobs)"]
        DemoAPI["Custom API (mount core controllers)"]
        DemoLib["lib/common/<br/>events · ops · schemas · persistence"]
        DemoExt["External: Azure OpenAI SUI<br/>+ local vLLM (Gemma-3 12b/27b)<br/>+ gte-Qwen2 embed · bge-rerank<br/>Azure AD · MongoDB · Milvus"]
    end

    subgraph WPE["aihub-W*P v0.255.6 (drift 35 minor)"]
        direction TB
        WPEDeploy["Deployment thuần<br/>(không có custom agents / pipelines / API)<br/>dùng core llm_wrapping_agent + rag_agent<br/>dùng core default_rag_pipeline"]
        WPECfg["Configs: LiteLLM, Milvus, Postgres,<br/>SeaweedFS, OTEL→SigNoz<br/>manual VM deploy (docker-compose copy)"]
        WPEExt["External: Azure OpenAI (region qua env)<br/>Azure AD / Entra (Microsoft v2.0)"]
    end

    subgraph FMH["aihub-F*H v0.186.0 (drift 104 minor)"]
        direction TB
        FMHAgents["Agents (3)<br/>handbook_agent · rules_agent · routing_agent"]
        FMHPipes["Pipelines (2)<br/>handbook_ingestion · position_ingestion<br/>(TARDOC / TARMED data)"]
        FMHAPI["Custom API + Bot (MS Bot Framework)"]
        FMHEval["evaluation/ framework<br/>own evaluators · testsets"]
        FMHExt["External: Azure OpenAI SUI<br/>(`*-openai-sui`) + Azure AI Search<br/>(KHÔNG dùng Milvus) · Azure Data Lake<br/>Azure AD · TARDOC/TARMED"]
    end

    Future["Other customers (TBD info):<br/>Ig*s · Balmer-E*<br/>(deployment gen + components pending)"]

    subgraph INFRA["Infrastructure Repos (Gen 2)"]
        direction TB
        Playbook["aihub-playbook<br/>Ansible Pull (every 15min)<br/>7 role: docker_runtime · traefik_proxy<br/>signoz · aihub_application<br/>os_backups (Restic→Swift) · custom_vars_sync<br/>restore_os_backup"]
        Ops["aihub-ops<br/>OpenStack VM provisioning<br/>setup-aihub.sh · cloud-init<br/>vault-vars-routing.yml<br/>nightly drift check"]
        CustomerRepo["aihub-{customer_id}<br/>Ansible Vault (encrypted)<br/>Custom config + secrets"]
    end

    subgraph K8S["aihub-k8s (Gen 3, mới nổi) — chart appVersion 0.1.0; pull qua ${CORE_VERSION:-latest}"]
        direction TB
        K8STerraform["Terraform<br/>Azure AKS (Switzerland North, OIDC + workload identity)<br/>+ Stoney OpenStack Magnum (Flannel, Cinder, floating IP)<br/>1 `deploy.sh` cho cả 2 cloud"]
        K8SCommon["Helm chart: `aihub-common`<br/>CloudNativePG (PostgreSQL 17 + pgvector)<br/>Keycloak Operator (1 instance, **realm per tenant**)<br/>SeaweedFS (shared, **bucket prefix per tenant**)<br/>Milvus (standalone; **DB per tenant**; scale-out optional)<br/>FerretDB · Langfuse · LiteLLM · MinerU · SearXNG"]
        K8STenant["Helm chart: `aihub-tenant`<br/>**namespace `tenant-<name>`** · subdomain `<name>.k8s.ai-agents.ch`<br/>~27 service (api · web · openwebui · dagster · bot ·<br/>NATS · Redis · Neo4j · Phoenix · Jupyter · Playwright ·<br/>Presidio · rclone · 9 agent · 2 RAG pipeline)<br/>NGINX Ingress + cert-manager (Let's Encrypt)"]
        K8STenants["Chỉ test tenant (chưa có prod customer):<br/>tenant1 · jointcreate · postgres-test"]
    end

    CORE -.->|git tag<br/>v0.279.2| B*D
    CORE -.->|git tag<br/>v0.274.3| C*C
    CORE -.->|git tag<br/>v0.246.4| DEMOSCOPE
    CORE -.->|git tag<br/>v0.255.6| WPE
    CORE -.->|git tag<br/>v0.186.0| FMH
    CORE -.->|git tag<br/>vX.Y.Z| Future
    CORE -.->|image pull qua<br/>${CORE_VERSION}| K8S

    Playbook -->|pulls every 15min| Future
    Ops -.->|provisions VM| Future
    CustomerRepo -.->|vault secrets| Future

    style CORE fill:#e8f0ff
    style B*D fill:#fff4e8
    style C*C fill:#fff4e8
    style DEMOSCOPE fill:#fff4e8
    style WPE fill:#fff4e8
    style FMH fill:#fff4e8
    style Future stroke-dasharray: 5 5,stroke:#888,fill:#f5f5f5
    style INFRA fill:#e8ffe8
    style K8S fill:#f0e8ff
```

**Customer Registry** (extend khi có customer mới)

Components format: `A` = agents, `P` = pipelines, `API` = custom API. Drift = số minor versions behind core latest.
Sovereignty annotation inline trong LLM Provider. **Deployment Gen**: Gen 1 = Azure VM + shell scripts (manual); Gen 2 =
OpenStack Infomaniak + Ansible Pull (aihub-playbook/aihub-ops).

| Customer              | Status            | Core ver (drift)     | Components      | Deployment Gen                                          | Data sources                         | LLM Provider                                        | Identity                |        Off-site Backup         | Own arc42 + ADRs | Test coverage              |
| --------------------- | ----------------- | -------------------- | --------------- | ------------------------------------------------------- | ------------------------------------ | --------------------------------------------------- | ----------------------- | :----------------------------: | :--------------: | -------------------------- |
| aihub-b\*d            | Production 4/2026 | v0.279.2 (sau 11) | 3A / 4P / -     | **Gen 1** - On-prem (SMB share)                         | SMB share (customer + supplier docs) | Azure OpenAI Sweden - **sovereignty violated**      | Keycloak SaaS           |        Không (same VM)         |      Không       | Minimal (58 dòng / 1 util) |
| aihub-c\*c            | Production        | v0.274.3 (sau 16) | 4A / 6P / 1 API | **Gen 1** - Azure VM (SUI+SWE)                          | Jira / Confluence / SharePoint       | Azure AI Foundry SUI+SWE - **sovereignty violated** | Keycloak + Azure AD B2C |        Không (same VM)         |      Không       | Minimal (3 file / 788 dòng trong `log_analysis_agent` only) |
| aihub-Ig\*s           | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| aihub-W\*P            | Production        | v0.255.6 (sau 35)    | - (deploy only) | **Gen 1** - manual VM (docker-compose copy-paste)       | OpenWebUI knowledge / RAG (Milvus + SeaweedFS, user upload) | Azure OpenAI (region không có trong repo - config qua env var) - **sovereignty chưa verified** | Azure AD / Entra ID (Microsoft v2.0) |    Không (không có trong repo)    |     Không     | N/A (không có custom code) |
| aihub-Dem\*scope      | Production        | v0.246.4 (sau 44)[^1] | 2A / 1P / 1 API | **Gen 1** - Azure VM (Pulumi theo README; IaC code không có trong repo) | MongoDB persona data + Milvus (questions, personas) | Azure OpenAI Switzerland + local vLLM (Gemma-3-12b/27b, gte-Qwen2 embedding, bge-reranker) - **partial sovereignty** | Azure AD / Entra ID (login.microsoftonline.com) |     Không (MinIO cùng VM)      |     Không     | Số 0 (không có file test)  |
| aihub-F\*H            | Production (commit gần nhất 4/2026) | v0.186.0 (sau 104) | 3A / 2P / 1 API / 1 bot | **Gen 1** - Azure (Pulumi đã commit: 10 deploy units) | Azure Data Lake Storage (TARDOC / TARMED: handbook + positions) | Azure OpenAI Switzerland North (`*-openai-sui`) + Azure AI Search (không phải Milvus) - **sovereignty Switzerland** | Azure AD (AUTH_AZURE_AD_*) |    Không (không có trong repo)    |     Không     | Minimal (5 test + 5 BDD)   |
| aihub-Balmer-E\*      | TBD               | TBD                  | TBD             | TBD                                                     | TBD                                  | TBD                                                 |                         |                                |                  |                            |
| Customer #N+ (future) | Template ready    | TBD                  | TBD             | **Gen 2** - OpenStack Infomaniak (Swiss) + Ansible Pull | TBD                                  | TBD                                                 | TBD                     | Restic → Swift (partial 3-2-1) | TBD via template | TBD                        |

______________________________________________________________________

## 3. Priority items cho go-live (CRITICAL + HIGH)

Section này highlight các items cần ưu tiên address để chuẩn bị go-live, group theo scope (Core / B*D / C*C /
Dem*scope / W*P / F*H). Severity:

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
| 20  | No K8s migration path **(đã đóng một phần: `aihub-k8s` Gen 3 đã có)**|     HIGH     | `aihub-k8s` đã có Terraform (AKS + Stoney Magnum) + Helm (`aihub-common` + `aihub-tenant`). Chart khai báo `appVersion: "0.1.0"` và pull image qua `${CORE_VERSION:-latest}` — chưa có chart-level pin (xem proposed `adr_040`). Còn lại: ADR adopt Gen 3 làm official path; chart-level core version pin policy; migrate ≥ 1 prod customer; validate cluster-mode Milvus + HPA; document Gen 1 → Gen 3 migration |
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
| 4   | SDK drift 11 minor versions (v0.279.2 vs v0.290.4)             |     HIGH     | SDK upgrade plan với security delta audit; extract reusable patterns (`resolve_selection`, HITL helpers) về core; CI gate block drift > N versions. **Near-latest pin — upgrade rủi ro thấp nhất trong các customer; làm trước như quick win (bump thẳng lên core tip)** |
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
| 4   | Test coverage minimal — 3 file / 788 dòng trong `log_analysis_agent` only; agent `chat / jira_issue / retrieval_orchestrator` + 6 pipeline + custom API + `lib/common` chưa test |     HIGH     | Mở rộng style coverage của `log_analysis_agent` ra tất cả component; smoke tests per agent; integration test với staging Jira/Confluence/SharePoint; coverage threshold 60% cho code mới                                                                                                                                                                                                                                |
| 5   | SDK drift 16 minor versions                                                    |     HIGH     | SDK upgrade với security delta audit; standardize uv workflow; deprecate poetry.lock; CI gate block drift                                                                                                                                                                                                                                                                                                                |
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
| 17  | Deep-import violations trong `ChatAgent.py` reach `swiss_ai_hub.core.generative_ai.{chat_history,guards}` và `swiss_ai_hub.core.i18n.locale_handler` — bypass public `__init__.py` API |     HIGH     | Refactor để import qua `from swiss_ai_hub.core import …` sau khi expose các symbol cần thiết ra public interface; thêm ruff/lint rule chặn deep import vượt scope boundary; CI gate (xem proposed `adr_038`) |
| 18  | MongoDB tenant-entry schema đã đổi giữa version pin và core hiện tại → cần migration trước khi upgrade SDK (rủi ro upgrade lớn nhất của C\*C) | **CRITICAL** | Dựa trên DB migration framework (ADR-NEW-003); viết migration forward + rollback; reconcile tenant docs với Keycloak (source of truth); dry-run trên bản restore trong maintenance window (xem proposed `adr_045`) |

### 3.4. aihub-Dem\*scope

Cơ sở evidence: code, configs, scripts, README trong repo `aihub-demoscope` (HEAD commit `abe968f 2026-01-13`).

| #   | Item                                                                                  |   Severity   | Recommendation actions                                                                                                                                                                                                                |
| --- | ------------------------------------------------------------------------------------- | :----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | SDK drift 44 minor versions (v0.246.4* vs v0.290.4) - đi sau 4.5+ tháng (*SDK pin không có trong `pyproject.toml`) | **CRITICAL** | Xác nhận SDK pin thực tế từ deploy manifests / CI logs trước; lập SDK upgrade plan + security delta audit (cover 44 minor fixes); CI gate chặn drift > N minor; coordinate breaking-change migration |
| 2   | Backup destination cùng VM (MinIO cùng host với Milvus / Mongo)                       | **CRITICAL** | Emergency cron sync sang Swiss off-site (Infomaniak / Exoscale / Hetzner); thay `backup_updater_script.py` ad-hoc bằng `milvus-backup` chính thức tới off-host bucket; restore drill có document                                      |
| 3   | Pulumi nêu trong README nhưng **IaC code không committed** (không có folder `.iac/`)  | **CRITICAL** | Commit Pulumi code thật hoặc xoá phần README đó; chọn 1 IaC approach (Pulumi vs Terraform); document quy trình deploy thực tế - hiện không reproducible từ repo                                                                       |
| 4   | Test coverage ZERO (không có `test_*.py`, không có `.feature` cho 2 agent + 1 pipe)   |     HIGH     | Baseline test plan (smoke test cho mỗi agent + pipeline); BDD `.feature` cho luồng questions phân vùng theo hash; integration test với staging Milvus                                                                                 |
| 5   | Migration production thủ công qua SSH + `screen` + `scp`                              |     HIGH     | Thay workflow `scp migrate_questions.py demoscope:aihub/scripts/...` + `screen -r migration` bằng Dagster job hoặc k8s Job; theo dõi migration trong DB, không phải `migration_log.json` trên VM                                      |
| 6   | Hash-partition Milvus hardcode 3 nơi (drift risk)                                     |     HIGH     | Single source of truth (đã làm 1 phần ở `lib/common/partition_utils.py`); CI test khẳng định agent + pipeline + migration script dùng cùng 1 hash function                                                                            |
| 7   | 4 agent variants deploy (persona / multi\_personas × public / private)                |     HIGH     | Document lý do split public/private trong ADR; verify 4 instance chạy cùng code hoặc merge thành 1 binary với config flag; giảm operational surface                                                                                   |
| 8   | Stack divergence so với core: MongoDB + Redis thay vì FerretDB + Valkey               |     HIGH     | ADR document tại sao Demoscope diverge khỏi core stack; migration plan hoặc accept divergence; check Demoscope có dùng feature riêng của Mongo (BSON types, transactions) ngăn migration không                                        |
| 9   | Phoenix v10.0.4 + LiteLLM v1.77.7 - pre-Langfuse (ADR `2026_02_10`) và LiteLLM cũ     |     HIGH     | Plan migration Phoenix → Langfuse theo ADR `2026_02_10`; bump LiteLLM lên stable hiện tại (v1.79+) cho security patches                                                                                                               |
| 10  | Sovereignty hỗn hợp: Azure OpenAI SUI + local vLLM (Gemma-3, gte-Qwen2, bge-reranker) |     HIGH     | Document vị trí partial-sovereignty trong ADR; làm rõ workload nào route Azure SUI vs local vLLM; gắn với Core sovereignty path (Option A/B/C)                                                                                        |
| 11  | Không có own arc42 + ADRs                                                             |     HIGH     | arc42 12 chapters + C4 L1/L2 + ADRs cho: stack divergence (Mongo/Redis), hash partition, 4-variant split, vị trí sovereignty, backup MinIO cùng VM, hash `persona_id` mod 1000                                                        |
| 12  | Agent crash khi khởi động lúc upgrade SDK (pin rất cũ) | **CRITICAL** | Reproduce crash trên bản staging; quyết định remediate tại chỗ vs rebuild trên core generation hiện tại; sắp xếp sau khi đã có backup verified (PO roadmap Q4) |
| 13  | Chưa thực sự build backup/restore (chỉ có `backup_updater_script.py` ad-hoc); không quản lý gia hạn token/key — khách hàng chính thức nhận trách nhiệm | **CRITICAL** | Ghi nhận là customer-accepted risk (RACI) có sign-off rõ ràng và document mức phơi nhiễm mất dữ liệu; vẫn cung cấp backup tối thiểu + runbook gia hạn key/token (xem `adr_030`) |
| 14  | Vector giữ in-memory (chỉ chạy được vì máy có 200 GB RAM) — bức tường chi phí khi data tăng | **HIGH** | Lên kế hoạch chuyển sang Milvus disk-backed / DISKANN trước khi data tăng; thêm dự phóng dung lượng; chạy RAG/vector-design gate (xem proposed `adr_044`, `adr_046`) |

### 3.5. aihub-W\*P

Cơ sở evidence: docker-compose, configs, README trong repo `aihub-wpe` (HEAD commit `c4b1527 2025-12-18`). Lưu ý:
`.env.prod` bị sensitive-file-guard chặn; chỉ đọc được **tên** env-var, không đọc được giá trị.

| #   | Item                                                                                       |   Severity   | Recommendation actions                                                                                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------ | :----------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **TLS private key được commit vào git** (`wpe.ai-agents.ch+1-key.pem` đang track, chỉ `.env` được ignore) | **CRITICAL** | Rotate cert + key **ngay lập tức** (re-issue Let's Encrypt qua Traefik); add `*.pem`, `*-key.pem`, `secrets/` vào `.gitignore`; rewrite git history (BFG / `git filter-repo`) để xoá key; audit xem ai đã pull repo sau đó      |
| 2   | Deploy VM thủ công bằng copy-paste (README: `cp docker-compose.latest.yml /opt/docker/config/bbv/`) | **CRITICAL** | Thêm minimum reproducible deploy: bash script + checksums, hoặc migrate sang Gen 2 (Ansible Pull) / Gen 3 (`aihub-k8s`); workflow hiện không có rollback, audit trail, drift detection                                          |
| 3   | LLM region không có trong repo (Azure OpenAI base URL chỉ có dạng env-var) → **sovereignty chưa verified** |     HIGH     | Commit file non-secret `litellm-region.md` hoặc `.env.example` ghi rõ Azure region; ADR align với Core sovereignty path; lựa chọn cần tường minh, không vùi trong `/opt/bbv/.env` của sysadmin                                  |
| 4   | SDK drift 35 minor versions (v0.255.6 vs v0.290.4)                                         |     HIGH     | Bump `CORE_VERSION` trong `.env.prod` kèm security delta review; CI gate chặn drift > N minor; pin theo tag, không fallback về `latest`                                                                                         |
| 5   | `${CORE_VERSION:-latest}` fallback về `latest` khi env-var thiếu                           |     HIGH     | Xoá default `:-latest` - bắt buộc pin tường minh; deploy phải fail-fast nếu `CORE_VERSION` không set; reproducible build cần version cụ thể                                                                                     |
| 6   | `VOLUME_ROOT:-./.docker-volumes` default về thư mục tương đối local trong production       |     HIGH     | Bắt buộc set `VOLUME_ROOT` (bỏ fallback `:-`); document production volume root (vd `/var/lib/aihub`) và chiến lược snapshot                                                                                                     |
| 7   | Off-site backup không có trong repo (không thấy Restic / Swift / cross-region sync)        |     HIGH     | Thêm backup config vào repo (cron + Restic tới Swiss off-site); follow 3-2-1; document RTO/RPO; nếu backup tồn tại ngoài repo, document chỗ                                                                                     |
| 8   | Không có own arc42 + ADRs - repo deploy-only không có design doc                           |     HIGH     | Minimal arc42 (context + deployment + crosscutting); ADRs cho: lựa chọn manual VM, identity provider, LLM region, vị trí sovereignty; giải thích vì sao WPE khác core defaults                                                  |
| 9   | Không có tests bất kỳ (repo deploy-only nhưng không có script smoke / health validation)    |     HIGH     | Thêm post-deploy smoke test (curl health endpoint, OAuth round-trip, ping LiteLLM, login OpenWebUI); fail fast khi deploy hỏng                                                                                                  |
| 10  | OTEL dùng SigNoz Cloud region "EU" - cùng caveat với core (sovereignty chưa rõ)            |     HIGH     | Kế thừa core ADR về SigNoz region khi có; document lựa chọn cục bộ trong WPE README                                                                                                                                             |
| 11  | Khách hàng báo platform chậm — chưa rõ root cause, khách hàng không phản hồi | **HIGH** | Review trace Langfuse/OTEL + chạy load-test baseline (Locust) trên bản replica config/hardware để định vị bottleneck; điều tra BỊ BLOCK do chờ input/data từ khách hàng (xem proposed `adr_046`) |

### 3.6. aihub-F\*H

Cơ sở evidence: code, configs, Pulumi IaC, evaluation framework, README trong repo `aihub-fmh` (HEAD commit
`5509d39 2026-04-07`).

| #   | Item                                                                                       |   Severity   | Recommendation actions                                                                                                                                                                                                                            |
| --- | ------------------------------------------------------------------------------------------ | :----------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | SDK drift 104 minor versions (v0.186.0 vs v0.290.4) - **lớn nhất trong tất cả customers** | **CRITICAL** | Lập multi-step SDK upgrade plan + security delta audit (104 minor = 10+ tháng patches bị miss); upgrade từng bước v0.186 → v0.220 → v0.260 → v0.290; CI gate chặn drift > N minor                                                              |
| 2   | **Monkey-patch** LlamaIndex cho GPT-5 (`lib/common/register_openai_models.py` chỉnh global của third-party module ở import time) | **CRITICAL** | Thay bằng support chính thức trong core (PR lên `aihub-core` thêm GPT-5 model registry); SDK upgrade sẽ tự loại bỏ patch này; document workaround trong ADR cho đến khi xoá                                                                    |
| 3   | Azure AI Search **thay vì** Milvus - stack divergence so với core                          | **CRITICAL** | ADR giải trình Azure AI Search vs Milvus của core (vendor lock-in, double inference cost, sovereignty); migration plan về Milvus hoặc accept divergence + cost analysis; trùng pattern với §3.3 C\*C "Azure stack triple redundancy"            |
| 4   | Backup status không có trong repo (Pulumi `stores/` deploy infra nhưng không thấy backup workload) | **CRITICAL** | Verify Azure backup policy trên `Storage Account` + `CosmosDB`/Mongo; cross-region replication cho TARDOC/TARMED handbook data; restore drill có document; nếu backup tồn tại ngoài Pulumi, document chỗ                                       |
| 5   | Stack divergence so với core: MongoDB + Redis + Phoenix (pre-Langfuse) - giống Dem\*scope  |     HIGH     | Plan migration Phoenix → Langfuse (ADR `2026_02_10`); plan MongoDB → FerretDB; gắn với SDK upgrade #1                                                                                                                                           |
| 6   | Test coverage tối thiểu (5 `test_*.py` + 5 BDD `.feature` cho 3 agent + 2 pipeline)        |     HIGH     | Coverage threshold 60% cho code mới; BDD feature cho luồng routing 3-agent (routing → handbook + rules); integration test với TARMED test fixtures                                                                                              |
| 7   | Azure OpenAI Switzerland North + Azure AD - vendor lock-in (giống C\*C)                    |     HIGH     | ADR document lý do chọn Azure (TARDOC/TARMED là dữ liệu chỉ Swiss, nên Switzerland North defensible); evaluate Keycloak federation làm identity alternative                                                                                     |
| 8   | Bot dùng MS Bot Framework + dev tunnel - rủi ro dev/prod parity                            |     HIGH     | Document deployment path cho MS Teams integration; xoá reference `agents/playground/bot_emulator/` khỏi prod docs; đảm bảo prod không phụ thuộc vào workflow `devtunnel`                                                                        |
| 9   | Pulumi state trong **Azure storage account** - phụ thuộc single-cloud                      |     HIGH     | Document Pulumi state account name / region trong repo (không chỉ credentials); plan state backup; nếu Azure account compromise, deployment không recover được                                                                                  |
| 10  | Không có own arc42 + ADRs - có IaC + evaluation framework tốt nhưng không có design docs   |     HIGH     | arc42 12 chapters + C4 L1/L2 + ADRs cho: Azure AI Search vs Milvus (#3), GPT-5 monkey-patch (#2), thiết kế 3-agent routing, ingestion TARDOC/TARMED, lý do chọn MS Bot Framework                                                                |
| 11  | Hardcode handbook namespace (`handbook_02_2026`) trong pipeline `__init__.py`              |     HIGH     | Pydantic Settings từ env; cho phép nhiều snapshot song song; document convention versioning (`handbook_MM_YYYY`)                                                                                                                                |
| 12  | Khách hàng không hài lòng về chất lượng câu trả lời — dữ liệu cấu trúc TARDOC/TARMED chưa được ingest theo vector schema được thiết kế; không có chiến lược testing/eval cho RAG (framework `evaluation/` có nhưng không dùng) | **CRITICAL** | Chạy RAG/vector-design gate (xem proposed `adr_044`): chunking theo field + metadata schema cho dữ liệu cấu trúc; wire eval harness trên framework `evaluation/` sẵn có + Langfuse datasets; baseline rồi tune; gắn với quyết định AI-Search-vs-Milvus (`adr_039`) |

______________________________________________________________________

## 4. Đánh giá

Đánh giá theo 2 perspectives song song. Phạm vi giờ bao gồm **5 Gen 1 production customers** (B*D / C*C / Dem*scope /
W*P / F*H); priority items theo từng customer được liệt kê chi tiết tại **§3.4 (Dem\*scope)**, **§3.5 (W\*P)**,
**§3.6 (F\*H)**. Ig*s và Balmer-E* vẫn TBD chờ thông tin từ team.

### 4.1. Theo khung 10 pillars

10 pillars dựa trên [Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/), mở rộng
thêm các trụ cột đặc thù cho platform multi-customer (Multi-Tenancy, SDK Versioning, Observability, Quality Assurance).
Mỗi cell liệt kê findings của scope đó. Cell `-` nghĩa là scope không có finding riêng.

| #   | Pillar - Status                                                          | Core                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | B\*D                                                                                                                                                                                                                                                                   | C\*C                                                                                                                                                                                                                                                                                                                                          | Ig\*s | Dem\*scope | W\*P | F\*H | Balmer-E\* | Cross-cutting                                                                                                                                                                                                              |
| --- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------- | ---- | ---- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Multi-Tenancy & Customer Isolation** - Critical                        | • NATS subjects không hierarchy `aihub.tenant.{id}.*`<br>• Milvus collections không namespace per-tenant<br>• MongoDB entities không có `tenant_id` field bắt buộc<br>• Valkey keys không có per-tenant prefix<br>• Neo4j graphs không namespace<br>• Không có tenant provisioning workflow / automation API<br>• Không có per-tenant feature flags<br>• Không có per-tenant resource quotas (rate limit, storage, LLM budget)<br>• Tenant chỉ tồn tại ở Keycloak layer (groups `/tenants/{id}`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD | Single-tenant deploy; 4-variant agent split (public/private), không phải multi-tenant thực sự | Single-tenant deploy; kế thừa gap của core | Single-tenant deploy; Pulumi không có deploy unit `tenants/` | TBD | • Mỗi customer = 1 Docker stack riêng biệt<br>• Không thể chạy shared SaaS multi-tenant<br>• Operational cost tuyến tính theo số customers<br>• Không có cross-tenant isolation test trong CI                              |
| 2   | **SDK Versioning & Extension Contract** - Gap                            | • Không có public SDK release (PyPI/internal registry), chỉ git+ssh<br>• Không có policy về breaking change, deprecation window<br>• Không có CHANGELOG categorization<br>• Không có downstream CI integration test với customers<br>• Không có lint rule chặn import từ internal modules                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | • Drift 11 minor versions (v0.279.2 vs v0.290.4)<br>• Internal import violation `pipelines/snk_enrichment.py:2`<br>• Patterns chưa extract về core (`resolve_selection()`, HITL helpers)                                                                              | • Drift 16 minor versions (v0.274.3 vs v0.290.4)<br>• Internal import violation `lib/common/types/RetrievalAgentInTheLoop.py:1-4`<br>• Deep imports trong `agents/chat_agent/chat_agent/ChatAgent.py` đến `swiss_ai_hub.core.generative_ai.{chat_history,guards}` + `swiss_ai_hub.core.i18n.locale_handler`<br>• Custom `switch_dependencies.py` thay standard uv workflow<br>• Dual lock files `poetry.lock` (84KB) + `uv.lock`<br>• Multi-agent orchestrator, Jira/Confluence/SharePoint connectors chưa extract     | TBD | • Drift 44 minor (v0.246.4*)<br>• *SDK pin không có trong repo `pyproject.toml`<br>• Poetry + custom `switch_dependencies.py` | • Drift 35 minor (v0.255.6)<br>• Chỉ image qua `CORE_VERSION` env (không có SDK code) | • Drift 104 minor (v0.186.0) — **lớn nhất**<br>• **Monkey-patch LlamaIndex** cho GPT-5 (`register_openai_models.py`) | TBD | -                                                                                                                                                                                                                          |
| 3   | **Security & Compliance** - Partial                                      | **Strengths**: 5 auth handlers (Keycloak/Token/Bearer/OAuth2/OpenWebUI) JWKS 6h cache; hierarchical permission template với wildcards; AccessChecker tenant-ceiling + BDD tests; two-stage access control tested.<br>**Gaps**:<br>• UsageLimits class defined nhưng KHÔNG wire vào middleware<br>• Không có `AuditLogEntity` (vi phạm GDPR Art. 30, ISO 27001 A.12.4, SOC2)<br>• Event payloads không signing (JetStream unsigned JSON)<br>• NATS token-only auth, no mTLS; MongoDB/Redis connection string<br>• Presidio claim ≠ thực tế (code dùng LLM-based fragile guard)<br>• MCP tool args bypass LiteLLM → Presidio guards bypass 100%<br>• File upload trust mime-type, no content sniffing<br>• OpenWebUI render model list bypass RBAC<br>• Docker volume chưa encrypt at rest<br>• No rate limiting per user/tenant ở API<br>• Không có SAST / dep vuln scan / SBOM / image signing / container vuln scan                                                                                                                                                                                                                                                                      | • Cohere reranking (US/Canada vendor)<br>• Hardcoded customer-specific config (SNK_ANCHOR, BASE_PATH)<br>• No secrets rotation policy                                                                                                                                  | • Service account shared key cho Jira/SharePoint/Confluence (vi phạm least-privilege)<br>• SharePoint Azure AD app-only `Sites.Read.All` tenant-wide<br>• Hardcoded Jira IDs (URL, Service Desk, Request Type, Project)<br>• Azure AD B2C federation thay pure Keycloak (vendor lock-in)                                                      | TBD | • Azure AD<br>• Presidio containers có trong compose; LiteLLM Presidio guard config chưa verified<br>• Sovereignty hỗn hợp (Azure SUI + local vLLM) | • **TLS private key committed vào git** (`wpe.ai-agents.ch+1-key.pem` đang track)<br>• Azure AD<br>• Kế thừa core Presidio config (mask + block, `default_on: false`) | • Azure AD (`AUTH_AZURE_AD_*`)<br>• LlamaIndex monkey-patch chỉnh third-party globals ở import time<br>• Pulumi state trong 1 Azure storage account (SPOF) | TBD | • Document ACL không inherit từ Jira/SharePoint/Confluence vào Milvus<br>• Service account ingest mọi thứ, user query được mọi document (cross-user leak)<br>• Presidio chỉ DE, Swiss multilingual FR/IT/EN PII không mask |
| 4   | **Reliability & Data Integrity** - Critical (Gen 2 partial fix)          | • Không có DB migration framework (schemas tạo implicit bởi Pydantic + MongoEngine startup)<br>• Cross-store consistency không đảm bảo (NATS + Mongo + Valkey)<br>• Không có RTO/RPO documented<br>• Không có automated DR test / restore drill<br>• Backup encryption at rest chưa rõ cho Gen 1<br>• Milvus không upsert-by-id → re-ingest = duplicate vectors<br>• Agent config schema không versioning<br>• No agent versioning cho in-flight runs<br>• No run / delegation timeout<br>• No circuit breaker cho external deps (LiteLLM, Keycloak, Milvus cascade)<br>• No DLQ cho JetStream poison messages<br>• No HA architecture (PostgreSQL/NATS/Valkey/Milvus/Keycloak/etcd đều single-instance)<br>• **Gen 2 partial fix**: Ansible Pull tự re-reconcile khi container drift; Restic backup ra OpenStack Swift container (off-host)<br>• Vẫn thiếu: cross-provider replication, HA stateful services, no DR drill automated                                                                                                                                                                                                                                                      | • **Gen 1 fatal**: Backup destination SeaweedFS cùng VM → VM chết = mất cả<br>• No off-site replication<br>• Production 3.9x storage multiplier (1 TB → 5.1 TB)<br>• Chưa migration sang Gen 2 (Restic→Swift)                                                          | • **Gen 1 fatal**: Backup destination cùng Azure VM<br>• Jira webhook không idempotent (`JiraWebhookController`): cùng event 2x = 2 agent runs<br>• External services cascade (Jira/Confluence/SharePoint/Azure outage)<br>• Chưa migration sang Gen 2 (Restic→Swift)                                                                         | TBD | • **Gen 1 fatal**: MinIO backup cùng VM<br>• Migration thủ công qua SSH + screen<br>• Không có off-site replication | • Không có off-site backup trong repo<br>• `VOLUME_ROOT:-./.docker-volumes` default về thư mục local tương đối trong prod | • Không thấy backup workload trong Pulumi `stores/`<br>• Pulumi state SPOF (1 Azure storage account) | TBD | • Gen 2 Restic→Swift đạt off-host nhưng **cùng cloud provider** (Infomaniak) - Infomaniak region outage = mất cả primary cộng backup<br>• Cross-provider replication chưa có                                               |
| 5   | **Operational Excellence** - Partial (improved with Gen 2)               | **Strengths**: CI/CD đầy đủ (lint-pr, semantic-pr, build-\* per package, deploy-docs, auto-tag); pre-commit hooks; 47 ADRs; Docker Compose Jinja2 templates; **Gen 2 Ansible Pull pattern** (aihub-playbook every 15min auto-reconcile); **customer onboarding automation** (`setup-aihub.sh`); **Ansible Vault encrypted secrets** với auto-gen via `vault-vars-routing.yml`; **Traefik + Let's Encrypt ACME** automated SSL; **env vars drift detection CI** (`check_env_drift.py` nightly).<br>**Gaps**:<br>• Không có Operations Guide / Runbook cho incident response<br>• Không có Incident Response Process (severity, escalation)<br>• Không có Upgrade Procedure documented<br>• Không có K8s/Helm chart cho production<br>• Health checks không tách liveness/readiness<br>• arc42 ch.11 (Risks) cần update với findings mới<br>• CLAUDE.md có false claims (Presidio integration)<br>• GDPR docs có false claims (right to erasure, audit logs immutable)<br>• Ansible Pull 15-min cadence chậm cho hot-fix<br>• GitHub là deploy SPOF (no local mirror)<br>• 3-repo version compatibility chưa có matrix / CI gate<br>• Deploy key rotation policy implicit, không automation | • Gen 1 deployment (Azure manual, chưa Gen 2)<br>• CI riêng (build-agents, build-pipelines, auto-tag)<br>• Không có arc42 docs riêng (12 chapters required)<br>• Không có ADRs riêng (8+ key decisions)<br>• 6 docker-compose files separation chưa document rationale | • Gen 1 deployment (Azure VM + shell scripts, chưa Gen 2)<br>• CI riêng (build-agents, build-pipelines, build-api, lint-pr)<br>• Không có arc42 docs riêng (12 chapters required)<br>• Không có ADRs riêng (13+ key decisions)<br>• Azure IaC `.iac/scripts/` shell scripts thay Pulumi<br>• Custom API deployment monitoring chưa documented | TBD | • Gen 1; **Pulumi nêu trong README nhưng IaC code KHÔNG committed**<br>• Own CI (build-agents, build-api-and-bot, build-dagster)<br>• Không có own arc42 / ADRs | • Gen 1 manual VM (copy-paste docker-compose)<br>• Không IaC, không CI cho deploy<br>• Không có own arc42 / ADRs | • Gen 1 với **Pulumi đã commit (10 deploy_units — IaC tốt nhất trong 3 customer mới)**<br>• Own CI cho builds<br>• Không có own arc42 / ADRs | TBD | • Không có alerting infrastructure formal (chỉ Slack on Ansible Pull failure)<br>• Customer documentation gate trước go-production chưa định nghĩa<br>• B*D/C*C migration path Gen 1 → Gen 2 chưa có                       |
| 6   | **Performance & Scalability** - Critical                                 | • Single-server ceiling (Docker Compose only, no K8s)<br>• Milvus single-node, HNSW memory wall (122 GB RAM cho 10M × 3072d × 4B)<br>• PostgreSQL single instance (no replica, no failover)<br>• SeaweedFS single master/volume/filer (no HA, replication="000")<br>• NATS single node, `max_memory_store: 512MB`, `max_file_store: 10GB` (dev config)<br>• Valkey single instance (SPOF)<br>• Pipeline ops dùng `in_process_executor` (single-thread)<br>• Dagster dynamic partition explosion risk (1 partition per file)<br>• Embedding batch size không tối ưu (recursive bisection fallback)<br>• LiteLLM throughput limit không documented<br>• Tenant membership không cache (Keycloak call per request)<br>• GPU pinned device 0, multi-GPU không tận dụng<br>• Không có resource limits trong docker-compose                                                                                                                                                                                                                                                                                                                                                                     | • Sizing production (4/2026): 16 CPU + 64 GiB RAM + 1.9 TB disk<br>• 1.9 TB disk insufficient cho 2+ customers shared                                                                                                                                                  | -                                                                                                                                                                                                                                                                                                                                             | TBD | • vLLM GPU containers (Gemma-3 12b/27b)<br>• Hash-partition Milvus (1000 partition cho personas) | • Single-VM core chuẩn<br>• Không custom scaling | • Azure AI Search (managed)<br>• Azure Data Lake (managed) | TBD | • Không có Load Test Baseline (k6, Locust)<br>• Không có Performance Baseline document<br>• Không có Horizontal Scaling Guide                                                                                              |
| 7   | **Observability** - Traces tốt, metrics yếu (improved with Gen 2 SigNoz) | **Strengths**: OTEL comprehensive (NATS/Mongo/Redis/Milvus/HTTP/asyncio); `SmartTracer` + `@trace_fn`; trace context cross-service qua NATS headers; Langfuse LLM observability (prompt/response, cost); Docker healthchecks; HealthController; **Gen 2 SigNoz OTEL collector role** (host metrics, OTLP traces, journald log collection); **Slack failure notifications** từ Ansible Pull.<br>**Gaps**:<br>• Bot scope (`packages/bot`) không OTEL → trace gãy ở bot boundary<br>• Không có business metrics (agent_runs, HITL escalations, ingestion rate, RAG latency)<br>• Không có SLO/SLI formal<br>• Không có Prometheus AlertManager với rules per service severity<br>• Không có Grafana dashboards<br>• Không có on-call routing (PagerDuty/OpsGenie)<br>• Logs unstructured, default WARNING level<br>• Không có log aggregation centralized (ELK/Loki tự host)<br>• Không có per-tenant cost attribution trong Langfuse<br>• Không có synthetic monitoring<br>• **SigNoz Cloud region "eu"** - data observability ra ngoài tenant infra; sovereignty implication chưa rõ<br>• SigNoz chỉ Gen 2; Gen 1 (B*D/C*C) không có                                                      | • Gen 1 - không SigNoz<br>• Business-level metrics chưa có                                                                                                                                                                                                             | • Gen 1 - không SigNoz<br>• Business-level metrics chưa có<br>• Custom API endpoints chưa monitoring                                                                                                                                                                                                                                          | TBD | • Phoenix v10.0.4 (pre-Langfuse, ADR `2026_02_10`)<br>• LiteLLM v1.77.7 (cũ) | • OTEL → SigNoz Cloud "EU"<br>• Phoenix v10.0.4 | • Phoenix v10.0.4 (pre-Langfuse)<br>• OTEL configured | TBD | -                                                                                                                                                                                                                          |
| 8   | **Quality Assurance** - Gap                                              | **Strengths**: ~150 test files trong `packages/core`, 35+ `packages/api`, 30+ `packages/agent`; BDD qua pytest-bdd; integration tests với real NATS (`SimulatedAgentApiTestRunner`); E2E key flows.<br>**Gaps**:<br>• Không có Load test trong CI<br>• Không có Chaos engineering<br>• Không có coverage threshold (no 80% gate)<br>• Không có SAST trong CI<br>• Không có dependency audit (pip-audit, trivy)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | • Test coverage: 58 dòng total (`tests/test_snk_enrichment.py`)<br>• 9 parametrized tests cho 1 utility function only<br>• Agents và pipelines chưa có tests                                                                                                           | • Test coverage minimal — 3 file / 788 dòng trong `agents/log_analysis_agent/log_analysis_agent/tests/` only<br>• `chat_agent`, `jira_issue_agent`, `retrieval_orchestrator_agent` + 6 pipeline + custom API + `lib/common` vẫn chưa test                                                                                                                                                                                                                        | TBD | Test coverage **ZERO** (không `test_*.py`, không `.feature`) | Không có tests (repo deploy-only, không có smoke validation) | 5 `test_*.py` + 5 BDD `.feature` cho 3 agent + 2 pipeline | TBD | • Không có integration test giữa core release và customer projects<br>• Không có E2E test cho multi-tenant isolation                                                                                                       |
| 9   | **Cost Optimization** - Critical                                         | • LLM cost tracking via `LLMCostEvent` (per-model, per-token rates)<br>• Per-agent run cost attribution via Langfuse<br>• S3 file expiration 7 days (`FILE_EXPIRATION_DAYS = 7`)<br>• Backup retention configured<br>• `UsageLimits` defined NHƯNG KHÔNG wire vào middleware → LLM cost unbounded<br>• Không có Pre-flight Cost Estimation<br>• Không có Hard Per-tenant Cost Cap<br>• Không có Storage Quota per tenant<br>• Không có Showback Mechanism<br>• Không có Budget Alert<br>• MCP tool costs KHÔNG tracked (external API costs invisible)<br>• Mongo collections unbounded (no TTL) = storage cost growth                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD | • LiteLLM cost tracking; vLLM per-token cost đã configure<br>• Hợp tác BBV Greece (offshore) | • Kế thừa core defaults<br>• Không per-tenant cost attribution | • **Azure AI Search per-query cost** (chi phí thêm so với Milvus self-host) | TBD | • Không có per-tenant cost attribution Langfuse<br>• Không có cold storage tier (tất cả data ở hot storage)                                                                                                                |
| 10  | **Sustainability** - Critical                                            | • Cloud-native capable in theory (containerized, stateless)<br>• License compliance OK (402 Python + 993 npm + 33 Docker all approved)<br>• Python 3.13 slim base images<br>• Không có Region/Data-Residency Strategy<br>• Không có Carbon Footprint Metrics<br>• Không có Energy Consumption Tracking<br>• Không có Sustainability Reporting<br>• LLM calls không optimize (no aggressive caching, batching, prompt compression)<br>• Không có Hardware Lifecycle Management<br>• Không có efficient algorithm benchmarking (HNSW vs DISKANN)<br>• Compute-heavy LLM calls không scheduling off-peak                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | -                                                                                                                                                                                                                                                                      | -                                                                                                                                                                                                                                                                                                                                             | TBD | • Local GPU vLLM = năng lượng on-prem<br>• Không có carbon metrics | • Phụ thuộc Azure (kế thừa claim renewables theo region)<br>• Không metrics | • Region Azure SUI<br>• Không có own metrics | TBD | -                                                                                                                                                                                                                          |

### 4.2. Business core values vs thực tế

| Core value                         | Statement / Source                                                            | Core (Platform)                                                                                                                                                                                                                                                             | b\*d                                         | c\*c                                                                               | Ig\*s | Dem\*scope | W\*P | F\*H | Balmer-E\* |       Status       |
| ---------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- | ----- | ---------- | ---- | ---- | ---------- | :----------------: |
| Swiss data sovereignty             | ADR `2026_02_24`: "All cloud inference must stay within Swiss infrastructure" | Declared via ADR, enforce qua self-hosted local LLM hoặc Swiss LLM Cloud                                                                                                                                                                                                    | 100% Azure OpenAI (Sweden region)            | 100% Azure AI Foundry (SUI+SWE) + Azure Document Intelligence                      | TBD | Azure OpenAI SUI + local vLLM | Azure region không có trong repo (chỉ env-var) | Azure OpenAI SUI + Azure AI Search | TBD |      VIOLATED      |
| No vendor lock-in                  | Platform principle                                                            | OK (no lock-in trong core)                                                                                                                                                                                                                                                  | Cohere reranking (US/Canada vendor)          | Lock-in Azure ở 5 tầng (VM, Key Vault, AD B2C, OpenAI, Doc Intelligence) + Jina AI | TBD | Azure OpenAI + Entra + stack vLLM cục bộ | Azure nặng (OpenAI + Entra) | Azure nặng nhất (OpenAI + AI Search + AD + Storage state) | TBD |      VIOLATED      |
| Self-hosted, on-premise capable    | Marketing claim                                                               | Infrastructure self-hosted OK                                                                                                                                                                                                                                               | Infra self-hosted, LLM Azure cloud           | Infra Azure VM, LLM Azure cloud                                                    | TBD | Infra Azure VM, LLM hỗn hợp (Azure + local vLLM) | Azure VM + Azure LLM (region chưa verified) | Azure VM + Azure OpenAI + Azure AI Search | TBD |      PARTIAL       |
| "Swiss Sovereign AI" marketing     | Public positioning                                                            | Infrastructure-level đúng                                                                                                                                                                                                                                                   | B\*D dùng Azure LLM → claim chưa align scope | C\*C dùng Azure LLM → claim chưa align scope                                       | TBD | Local vLLM hỗ trợ; phụ thuộc Azure vẫn còn | Azure region chưa rõ — rủi ro claim | Azure SUI defensible cho LLM; AI Search tăng phụ thuộc | TBD | Cần review wording |
| Open-source platform               | License declaration                                                           | OK (BSD/MIT/Apache verified)                                                                                                                                                                                                                                                | OK                                           | OK                                                                                 | TBD | OK | OK (deploy-only) | OK | TBD |         OK         |
| Multi-tenant SaaS support          | ADRs 2026_03_30, 2026_02_20                                                   | Tenant chỉ ở Keycloak; data layer không namespace                                                                                                                                                                                                                           | Single-tenant deployment                     | Single-tenant deployment                                                           | TBD | Triển khai single-tenant | Triển khai single-tenant | Triển khai single-tenant | TBD |     NOT READY      |
| GDPR Art. 17 right to erasure      | Compliance docs claim "implemented"                                           | Không có user/tenant DELETE endpoint                                                                                                                                                                                                                                        | N/A                                          | N/A                                                                                | TBD | N/A (kế thừa gap core) | N/A (kế thừa gap core) | N/A (kế thừa gap core) | TBD |    FALSE CLAIM     |
| Audit log immutability             | GDPR docs claim "audit logs remain immutable"                                 | Không có `AuditLogEntity` trong codebase                                                                                                                                                                                                                                    | N/A                                          | N/A                                                                                | TBD | N/A (kế thừa gap core) | N/A (kế thừa gap core) | N/A (kế thừa gap core) | TBD |    FALSE CLAIM     |
| Presidio PII protection            | CLAUDE.md claims integrated                                                   | Code dùng LLM-based fragile guard, không phải Presidio                                                                                                                                                                                                                      | N/A                                          | N/A                                                                                | TBD | Containers có trong compose; LiteLLM guard config chưa verified | Core config trong repo (mask + block, `default_on: false`) | Chưa verified (older core baseline) | TBD |    FALSE CLAIM     |
| MCP secure tool execution          | Implied by MCP integration                                                    | Tool args bypass LiteLLM → Presidio bypass 100%                                                                                                                                                                                                                             | N/A                                          | Risk cao do agent-heavy use case                                                   | TBD | N/A (kế thừa gap core) | N/A (kế thừa gap core) | N/A (kế thừa gap core) | TBD |     LEAK RISK      |
| Document ACL respect               | Implied by RBAC architecture                                                  | Milvus không có ACL field, retrieval không filter user                                                                                                                                                                                                                      | N/A                                          | Service account ingest mọi thứ; cross-user query data leak                         | TBD | N/A (kế thừa gap core) | N/A (kế thừa gap core) | N/A (kế thừa gap core) | TBD |     LEAK RISK      |
| Multi-language Swiss (DE/FR/IT/EN) | Platform i18n declared                                                        | Presidio hardcode `de` ở 16 cấu hình files                                                                                                                                                                                                                                  | i18n DE/EN/FR/IT translations có             | N/A                                                                                | TBD | DE primary (Swiss `allowed_plz.json`) | Kế thừa core (DE/EN/FR/IT) | DE primary (TARDOC/TARMED Swiss medical) | TBD |      PARTIAL       |
| Cost protection per tenant         | Implied by UsageLimits class                                                  | `UsageLimits` defined nhưng KHÔNG wire vào middleware                                                                                                                                                                                                                       | N/A                                          | N/A                                                                                | TBD | N/A (single-tenant) | N/A (single-tenant) | N/A (single-tenant) | TBD |    NOT ENFORCED    |
| Disaster recovery capability       | Backup service tồn tại                                                        | Backup destination = cùng SeaweedFS instance trên cùng VM                                                                                                                                                                                                                   | No off-site backup                           | No off-site backup                                                                 | TBD | FATAL (MinIO cùng VM) | Không có trong repo | Không có trong repo (Pulumi không có backup workload) | TBD |       FATAL        |
| Common enterprise AI patterns      | Agent framework capability                                                    | Conversational, RAG single+multi-source, document parsing, tool calling/MCP, HITL, multi-agent, voice STT/TTS, code execution, browser automation: working. Vision / predictive analytics / fine-tuned model serving: out of scope (xem `adr_aihub_supported_use_cases.md`) | RAG agents working                           | Multi-agent orchestration working                                                  | TBD | Personas + RAG hash-partitioned | Chỉ standard core | 3-agent routing + BITL events | TBD |         OK         |

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
  - Drift 11 minor versions (v0.279.2 vs core v0.290.4)
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
  - Test coverage = 58 lines (1 utility function)
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
  - Drift 16 minor versions (v0.274.3 vs core v0.290.4)
  - Deep imports trong `agents/chat_agent/chat_agent/ChatAgent.py` đến `swiss_ai_hub.core.generative_ai.{chat_history,guards}` + `swiss_ai_hub.core.i18n.locale_handler` (xem proposed `adr_038`)
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

### 5.4. aihub-Dem\*scope

Cơ sở evidence: repo `aihub-demoscope` HEAD `abe968f 2026-01-13`. Priority items liên kết: §3.4.

#### Concerns

**SDK drift 44 minor**

- _Concern_:
  - Drift 44 minor version (v0.246.4* vs core v0.290.4) — 4.5+ tháng patches bị bỏ (*SDK pin không có trong repo `pyproject.toml`; số liệu carry over từ snapshot trước)
  - Phải coordinate upgrade qua 4 variant agent (public/private của persona + multi_personas)
- _Direction_:
  - SDK upgrade plan + security delta audit qua 44 minor
  - CI gate chặn drift > N minor

**Backup destination cùng VM**

- _Concern_:
  - MinIO backup nằm cùng host với Milvus/Mongo
  - VM hỏng = mất toàn bộ; vi phạm 3-2-1
  - Recovery hiện phụ thuộc `backup_updater_script.py` ad-hoc
- _Direction_:
  - Emergency cron sync sang Swiss off-site (Infomaniak / Exoscale / Hetzner)
  - Thay script ad-hoc bằng `milvus-backup` chính thức tới off-host bucket

**Pulumi nêu trong README nhưng IaC code KHÔNG commit**

- _Concern_:
  - README có viết Pulumi stack init nhưng repo không có folder `.iac/`
  - Deployment không document được, không reproducible từ repo này
- _Direction_:
  - Commit code Pulumi thật hoặc xoá phần README đó
  - Chọn 1 IaC approach (Pulumi vs Terraform) và document end-to-end deployment

**Test coverage ZERO**

- _Concern_:
  - Không có `test_*.py`, không có `.feature` cho 2 agent + 1 pipeline
  - Rủi ro regression cao khi upgrade SDK 44 minor sắp tới
- _Direction_:
  - Smoke test baseline cho mỗi agent + pipeline
  - BDD `.feature` cho luồng questions phân vùng theo hash
  - Integration test với staging Milvus

**Migration thủ công qua SSH+screen+scp**

- _Concern_:
  - Workflow `scp migrate_questions.py demoscope:aihub/scripts/...` + `screen -r migration`
  - Tiến độ track qua `migration_log.json` trên VM (không qua DB)
  - Fragile, không audit trail
- _Direction_:
  - Thay bằng Dagster job (ưu tiên) hoặc k8s Job
  - Track tiến độ migration qua DB hoặc Dagster runs

**Thiết kế hash-partition Milvus duplicate ở 3 nơi**

- _Concern_:
  - Cùng 1 hash function ở `lib/common/partition_utils.py`, `persona_agent`, và script migration
  - Rủi ro drift: nếu 1 chỗ lệch, mọi query đều miss vector
- _Direction_:
  - Single source of truth (đã làm 1 phần ở `lib/common/partition_utils.py`)
  - CI test khẳng định agent + pipeline + migration dùng cùng hash

**4 agent variants deploy (public/private của 2 agent gốc)**

- _Concern_:
  - persona_agent_public / persona_agent_private / multi_personas_agent_public / multi_personas_agent_private
  - Operational surface gấp 2; lý do split chưa document
- _Direction_:
  - ADR document lý do split public/private
  - Verify 4 instance chạy cùng code hoặc merge thành 1 binary với config flag

**Stack divergence so với core (Mongo + Redis + Phoenix pre-Langfuse)**

- _Concern_:
  - Dùng `mongo:8.0.9` + `redis:8.0.1` + `phoenix:version-10.0.4` + `litellm:v1.77.7`
  - Core đã migrate sang FerretDB + Valkey + Langfuse (ADR `2026_02_10`)
  - Gắn với SDK drift 44 minor
- _Direction_:
  - ADR document lý do divergence (hoặc migration plan)
  - Check nếu Demoscope có dùng tính năng riêng của Mongo (BSON types, transactions) ngăn migration

**Sovereignty hỗn hợp (Azure OpenAI SUI + local vLLM)**

- _Concern_:
  - `demoscopeaihub-oai-sui.openai.azure.com` (Azure Switzerland) cho 1 số route
  - Local vLLM (Gemma-3 12b/27b, gte-Qwen2, bge-reranker) cho route khác
  - Vị trí hỗn hợp chưa document
- _Direction_:
  - ADR document vị trí partial-sovereignty
  - Làm rõ workload nào route Azure SUI vs local vLLM
  - Gắn với Core sovereignty path (Option A/B/C)

#### Documentation deliverables

- arc42 12 chương cho Dem\*scope
- C4 Level 1 (System Context) + C4 Level 2 (Container): 2 agent package (4 variant deploy) + 1 pipeline + custom API
- ADRs trả lời 9 design questions: stack divergence (Mongo/Redis), hash partition (1000 partition trên `persona_id`),
  split public/private 4-variant, vị trí sovereignty (Azure SUI + local vLLM), backup MinIO cùng VM, migration
  Phoenix → Langfuse, IaC approach (commit Pulumi hoặc chọn Terraform), test strategy, agent-config evolution

### 5.5. aihub-W\*P

Cơ sở evidence: repo `aihub-wpe` HEAD `c4b1527 2025-12-18`. `.env.prod` bị sensitive-file-guard chặn; chỉ đọc được
**tên** env-var, không đọc được giá trị. Priority items liên kết: §3.5.

#### Concerns

**TLS private key committed vào git**

- _Concern_:
  - `wpe.ai-agents.ch+1-key.pem` và `wpe.ai-agents.ch+1.pem` đang track trong git (chỉ `.env` có trong `.gitignore`)
  - Cert tên production-domain + private key tương ứng visible cho bất kỳ ai có read access repo
  - Dù là dev/mkcert cert thì pattern này vẫn nguy hiểm
- _Direction_:
  - Rotate cert + key **ngay lập tức** (re-issue qua Traefik + Let's Encrypt)
  - Add `*.pem`, `*-key.pem`, `secrets/` vào `.gitignore`
  - Rewrite git history (BFG / `git filter-repo`) để xoá key
  - Audit xem ai đã pull repo sau khi key được commit

**Deploy VM thủ công bằng copy-paste**

- _Concern_:
  - Workflow README: `cp docker-compose.latest.yml /opt/docker/config/bbv/docker-compose.latest.yml`
  - Không IaC, không rollback, không audit trail, không drift detection
  - `.env` của sysadmin nằm trong `/opt/bbv/.env` (ngoài repo)
- _Direction_:
  - Minimum: deploy script reproducible + checksums
  - Tốt hơn: migrate sang Gen 2 (Ansible Pull) hoặc Gen 3 (`aihub-k8s`)

**LLM region không có trong repo (sovereignty chưa verified)**

- _Concern_:
  - `AZURE_OPENAI_BASE_URL` chỉ có trong `.env.prod` (gitignore, sensitive-guarded)
  - Compliance status không review được từ repo
- _Direction_:
  - Commit file non-secret `litellm-region.md` hoặc `.env.example` ghi rõ Azure region
  - ADR align với Core sovereignty path

**SDK drift 35 minor + fallback `${CORE_VERSION:-latest}`**

- _Concern_:
  - `.env.prod` pin `CORE_VERSION="v0.255.6"`, nhưng `docker-compose.latest.yml` fallback `latest` nếu env thiếu
  - Reproducible build cần pin tường minh
- _Direction_:
  - Bỏ default `:-latest`; fail-fast nếu `CORE_VERSION` không set
  - SDK upgrade plan + security delta audit (35 minor)
  - Pattern fallback tương tự cũng tồn tại trong Helm chart `aihub-k8s` — xem proposed `adr_040`
  - CI gate chặn drift > N minor

**`VOLUME_ROOT:-./.docker-volumes` default về thư mục tương đối**

- _Concern_:
  - Trong production, default về path tương đối với working directory hiện tại
  - Đường dẫn snapshot/backup phụ thuộc vào `pwd` của operator khi chạy `docker compose`
- _Direction_:
  - Bắt buộc set tường minh `VOLUME_ROOT` (vd `/var/lib/aihub`)
  - Document chiến lược snapshot

**Off-site backup không có trong repo**

- _Concern_:
  - Không thấy config Restic / Swift / cross-region sync trong repo
  - Không rõ backup tồn tại ngoài repo hay không
- _Direction_:
  - Thêm backup config vào repo (cron + Restic tới Swiss off-site)
  - Tuân theo 3-2-1; document RTO/RPO

**Không có own arc42 + ADRs + không có smoke tests**

- _Concern_:
  - Repo deploy-only không có design doc giải thích các lựa chọn
  - Không có script validate sau deploy
- _Direction_:
  - arc42 tối thiểu (context + deployment + crosscutting)
  - ADRs cho: lựa chọn manual VM, identity provider, LLM region, vị trí sovereignty
  - Smoke test sau deploy (curl health endpoint, OAuth round-trip, LiteLLM ping)

#### Documentation deliverables

- arc42 3 chương cho W\*P (Context + Deployment + Crosscutting concepts)
- C4 Level 1 + C4 Level 2 ngắn gọn (5 ingress host qua Traefik + 30 container)
- ADRs trả lời 6 design questions: TLS key trong git (rotation + history rewrite), manual VM deployment,
  identity provider (Azure AD / Entra), LLM region + sovereignty, lý do không có own code, chiến lược backup
- Smoke test script sau deploy (commit vào repo)

### 5.6. aihub-F\*H

Cơ sở evidence: repo `aihub-fmh` HEAD `5509d39 2026-04-07`. Priority items liên kết: §3.6.

#### Concerns

**SDK drift 104 minor (lớn nhất trong tất cả customer)**

- _Concern_:
  - Drift v0.186.0 vs core v0.290.4 = 104 minor
  - 10+ tháng security patches bị miss
  - Breaking changes tích lũy nhiều, cần upgrade nhiều bước
- _Direction_:
  - Upgrade plan từng bước: v0.186 → v0.220 → v0.260 → v0.290
  - Security delta audit mỗi bước
  - CI gate chặn drift > N minor

**Monkey-patch LlamaIndex cho GPT-5**

- _Concern_:
  - `lib/common/register_openai_models.py` chỉnh third-party globals
    (`llama_index.llms.openai.utils.ALL_AVAILABLE_MODELS` và `CHAT_MODELS`) ở import time
  - Add `gpt-5-mini` và `gpt-5-nano` vì pinned `llama-index-llms-openai ^0.3.x` chưa biết
  - Vấn đề supply-chain hygiene: behaviour phụ thuộc import order; hỏng nếu upstream library thay đổi
- _Direction_:
  - Open PR lên `aihub-core` thêm GPT-5 model registry chính thức
  - SDK upgrade sẽ tự loại bỏ patch này
  - Document workaround trong ADR cho đến khi xoá

**Azure AI Search thay vì Milvus (stack divergence)**

- _Concern_:
  - F\*H dùng `mongo_aisearch_storage_context_resources` (Azure AI Search) thay vì Milvus của core
  - Vendor lock-in: indexer + retrieval gắn với Azure SDK
  - Double inference cost (AI Search query + LLM call)
  - Trùng pattern §3.3 C\*C "Azure stack triple redundancy"
- _Direction_:
  - ADR giải trình Azure AI Search vs Milvus của core
  - Migration plan về Milvus, hoặc accept divergence + cost analysis chính thức

**Backup status không có trong repo**

- _Concern_:
  - Pulumi `stores/` deploy infrastructure nhưng không thấy backup workload
  - Azure backup policy trên `Storage Account` và Cosmos/Mongo chưa verify được từ repo
  - Cross-region replication cho TARDOC/TARMED handbook data chưa rõ
- _Direction_:
  - Verify Azure backup policy + cross-region replication
  - Restore drill có document RTO/RPO
  - Nếu backup tồn tại ngoài Pulumi, document chỗ

**Stack divergence (Mongo + Redis + Phoenix pre-Langfuse)**

- _Concern_:
  - Cùng pattern divergence như Dem\*scope (core baseline cũ ở v0.186.0)
  - Gắn với SDK upgrade
- _Direction_:
  - Plan migration Phoenix → Langfuse (ADR `2026_02_10`)
  - Plan MongoDB → FerretDB
  - Gắn với SDK upgrade

**Test coverage tối thiểu (5 + 5 BDD)**

- _Concern_:
  - Chỉ 5 `test_*.py` + 5 BDD `.feature` cho 3 agent + 2 pipeline
  - Coverage gap trong luồng routing TARMED billing quan trọng
- _Direction_:
  - Coverage threshold 60% cho code mới
  - BDD `.feature` cho luồng routing 3-agent (routing → handbook + rules)
  - Integration test với TARMED test fixtures

**Azure vendor lock-in (OpenAI + AI Search + AD + Storage state)**

- _Concern_:
  - Azure OpenAI Switzerland North + Azure AI Search + Azure AD + Pulumi state trong Azure storage
  - 4 lớp phụ thuộc Azure; cross-cloud failover không khả thi
  - Pulumi state SPOF (1 Azure storage account)
- _Direction_:
  - ADR document lý do chọn Azure (TARDOC/TARMED là dữ liệu chỉ Swiss → Switzerland North defensible)
  - Document Pulumi state account name/region trong repo; plan state backup
  - Evaluate Keycloak federation làm identity alternative

**MS Bot Framework + dev tunnel workflow**

- _Concern_:
  - README reference `devtunnel` cho local bot dev; rủi ro prod follow dev pattern
  - `agents/playground/bot_emulator/fmh-local.bot` được reference từ prod docs
- _Direction_:
  - Document path deployment cho MS Teams integration tường minh
  - Xoá reference emulator khỏi prod docs
  - Đảm bảo prod không phụ thuộc `devtunnel`

**Hardcode handbook namespace `handbook_02_2026`**

- _Concern_:
  - Pipeline `handbook_ingestion/__init__.py` hardcode `CONTAINER_NAME`, `DIRECTORY_NAME`, `NAMESPACE_NAME`,
    `VECTOR_STORE_NAME`, `DOCUMENT_STORE_NAME`
  - Snapshot tháng mới yêu cầu code change
- _Direction_:
  - Pydantic Settings từ env
  - Cho phép nhiều snapshot song song
  - Document convention versioning `handbook_MM_YYYY`

#### Documentation deliverables

- arc42 12 chương cho F\*H
- C4 Level 1 + C4 Level 2 (3 agent + 2 pipeline + custom API + bot + evaluation framework)
- ADRs trả lời 9 design questions: Azure AI Search vs Milvus, monkey-patch GPT-5 (workaround + removal path),
  thiết kế routing 3-agent (handbook + rules + routing), ingestion TARDOC/TARMED data, lựa chọn MS Bot Framework,
  identity (Azure AD), Pulumi state SPOF, lý do evaluation framework, BITL events (DignityCheck /
  RecognitionCheck)

### 5.7. Other customer projects (placeholders pending input)

Các customer còn lại chưa có thông tin. Mỗi customer sẽ có §5 subsection riêng (tương tự §5.2-§5.6) khi có chi tiết.

| Customer         | Status placeholder        |
| ---------------- | ------------------------- |
| aihub-Ig\*s      | TBD - awaiting team input |
| aihub-Balmer-E\* | TBD - awaiting team input |

**Per-customer info cần cung cấp** (mỗi customer):

- Status (production date / pilot / onboarding)
- Core version + drift số minor versions
- Components (số agent / pipeline / custom API / bot)
- Deployment generation (Gen 1 Azure manual / Gen 2 Infomaniak Ansible Pull / Gen 3 `aihub-k8s` / khác)
- Data sources (SharePoint / Jira / SMB / custom / etc.)
- LLM provider + sovereignty annotation
- Identity provider (Keycloak / Azure AD / SaaS)
- Off-site backup status
- Own arc42 + ADRs available?
- Test coverage estimate
- Concerns / blockers chính của customer
- Migration plan Gen 1 → Gen 2 → Gen 3 (nếu applicable)

### 5.8. Cross-cutting (Infrastructure, Process, Governance)

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
- **Audit security delta** từ phiên bản pin của từng customer (B*D v0.279.2, C*C v0.274.3, W*P v0.255.6, Dem*scope v0.246.4*, F*H v0.186.0) → core hiện tại v0.290.4, force-upgrade customers nếu có security patches (*Demoscope SDK pin chưa verify được từ repo, xem footnote ở §Phiên bản các thành phần)
- **Dem\*scope remediate-vs-rebuild**: quyết định upgrade pin rất cũ tại chỗ (agent crash khi khởi động) hay rebuild trên core generation hiện tại; và **chính thức chấp nhận rủi ro backup / gia hạn key do khách hàng sở hữu** (RACI sign-off)
- **F\*H answer quality**: phê duyệt re-design RAG/vector cho dữ liệu cấu trúc và quyết định AI-Search-vs-Milvus (`adr_039`, `adr_044`)
- **Adopt standing gates**: RAG/vector-design gate (`adr_044`) và continuous component-update strategy (`adr_043`)

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
- **Component replaceability / continuous-update strategy**: ports & adapters cho các building block có thể swap (document parser, vector store, OCR — LLM đã provider-agnostic qua LiteLLM) + Renovate + eval-gated upgrades + fallback có tên cho lib commercial/EOL. Tổng quát hoá case MinerU→Docling (`adr_042`, `adr_043`)
- **Giảm upgrade pain mỗi customer**: mô hình single-tenant-per-deployment khiến mỗi lần upgrade customer là bespoke và đắt — multi-tenant data layer + SDK versioning policy chính thức là fix mang tính cấu trúc

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
- **Design/analysis gate trước implementation**: yêu cầu một design artefact ngắn — đặc biệt vector-DB chunking/schema/index tuning + eval plan — trước khi code. Khoảng trống quy trình này là root cause của các vấn đề chất lượng & performance ở F\*H/Dem\*scope/W\*P (`adr_044`)
- **Load-test baselines**: thiết lập baseline cho từng project + core (Locust) và chạy định kỳ; tiền đề cho SLI/SLO và để chẩn đoán complaint performance của W\*P (`adr_046`)

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

### Gen 3 Kubernetes deployment stack (aihub-k8s)

- **Kubernetes**: https://kubernetes.io/docs/
- **Helm 3** (chart packaging): https://helm.sh/docs/
- **Terraform** (multi-cloud IaC): https://developer.hashicorp.com/terraform/docs
- **Azure AKS** (managed Kubernetes): https://learn.microsoft.com/en-us/azure/aks/
- **OpenStack Magnum** (Container Infra; dùng trên Stoney cloud):
  https://docs.openstack.org/magnum/latest/
- **CloudNativePG** (PostgreSQL operator): https://cloudnative-pg.io/documentation/current/
- **Keycloak Operator**: https://www.keycloak.org/operator/installation
- **cert-manager** (TLS certificate automation trong K8s): https://cert-manager.io/docs/
- **NGINX Ingress Controller**: https://kubernetes.github.io/ingress-nginx/
- **External Secrets Operator**: https://external-secrets.io/latest/
- **SeaweedFS Helm chart**: https://github.com/seaweedfs/seaweedfs/tree/master/k8s/charts
- **Milvus Helm chart (Zilliztech)**: https://github.com/zilliztech/milvus-helm

### Công nghệ riêng cho customer (referenced in §3.4-§3.6)

- **Azure AI Search** (F\*H vector backend; thay thế Milvus):
  https://learn.microsoft.com/en-us/azure/search/
- **Azure Data Lake Storage Gen2** (F\*H source storage):
  https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction
- **Microsoft Bot Framework** (F\*H bot integration):
  https://learn.microsoft.com/en-us/azure/bot-service/
- **TARDOC** (biểu phí ngoại trú Swiss): https://www.tarmed-suisse.ch/tardoc.html
- **TARMED** (biểu phí billing y tế Swiss, tiền nhiệm): https://www.tarmed-suisse.ch/
- **vLLM** (LLM serving high-throughput; stack local của Dem\*scope):
  https://docs.vllm.ai/en/latest/
- **LlamaIndex** (RAG framework; F\*H monkey-patch để hỗ trợ GPT-5):
  https://docs.llamaindex.ai/
- **Pulumi** (IaC framework; ADR `2024_12_18`; F\*H đã commit code; Dem\*scope chỉ có trong README):
  https://www.pulumi.com/docs/
- **mkcert** (dev certs locally-trusted; liên quan tới audit `wpe.ai-agents.ch+1*.pem` của W\*P):
  https://github.com/FiloSottile/mkcert
- **BFG Repo-Cleaner** (rewrite history để xoá secret đã commit; liên quan W\*P §3.5 item #1):
  https://rtyley.github.io/bfg-repo-cleaner/
- **git-filter-repo** (tool rewrite history thay thế): https://github.com/newren/git-filter-repo

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
