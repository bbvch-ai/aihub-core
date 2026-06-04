# C4 — aihub-bmd

> Snapshot: **aihub-bmd v0.279.2** (drift 11 minors behind core v0.290.4) as of 2026-05-28. Extracted from
> [`../03_c4_diagrams.md`](../03_c4_diagrams.md) §2.2 and refreshed with verified component counts.

## Level 0 — High-Level Solution Architecture

Boundary-first view: custom code (amber), core touchpoints (blue), Azure (purple), observability (green), known issues
(red). Less text, more wiring.

```mermaid
flowchart LR
  classDef custom fill:#fff4e1,stroke:#e8a33d,color:#000
  classDef core fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef azure fill:#e6ddff,stroke:#7a5cff,color:#000
  classDef obs fill:#e1ffe1,stroke:#3da35a,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  SMB[("SMB share<br/>customers + suppliers docs")]:::ext

  subgraph BMD["aihub-bmd · Gen 1 · docker-compose on VM + shell scripts (on-prem, SMB) · core v0.279.2 (near-latest → upgrade to tip)"]
    direction TB
    subgraph AG["Custom agents"]
      A1["bmd_agent"]:::custom
      A2["expert_rag_agent"]:::custom
      A3["expert_asking_agent"]:::custom
    end
    subgraph PI["Custom pipelines · Dagster"]
      P1["customers: FS → datalake → vector"]:::custom
      P2["suppliers: FS → datalake → vector"]:::custom
    end
    subgraph CO["Swiss AI Hub Core SDK"]
      C1["NATS + dispatcher"]:::core
      C2[("Milvus 2.6.7")]:::core
      C3[("FerretDB")]:::core
      C4[("SeaweedFS")]:::core
    end
    OBS["Observability<br/>Langfuse v3 (+ ClickHouse) + OTEL<br/>agent traces · LLM cost · eval"]:::obs
    BK["Backup Dagster<br/>⚠ same-VM destination (FATAL: VM loss = data + backup gone)"]:::warn
    GAP["⚠ Other BMD gaps<br/>tests ~0 (59 lines, 1 util) · no own arc42 / ADRs<br/>no docker resource limits · no secrets rotation<br/>hardcoded config (SNK_ANCHOR / BASE_PATH)<br/>internal import violation (snk_enrichment.py)<br/>weak-model JSON can break workflow · 3.9× storage (1.9 TB tight)"]:::warn
  end

  AOAI["Azure OpenAI Sweden<br/>chat · embed · image · STT/TTS<br/>⚠ sovereignty"]:::azure
  SLC["Swiss LLM Cloud<br/>MinerU OCR"]:::ext
  COH["Cohere rerank<br/>⚠ US/CA non-sovereign vendor"]:::warn
  KC["Keycloak SaaS · OIDC"]:::ext

  SMB -->|ingest| P1
  SMB -->|ingest| P2
  P1 --> C4
  P2 --> C4
  C4 --> C2
  P1 -->|OCR| SLC
  A2 -->|RAG search| C2
  A1 --> C1
  A2 --> C1
  A3 --> C1
  C1 --> OBS
  AG -.telemetry.-> OBS
  PI -.telemetry.-> OBS
  A1 -->|LLM cost via LiteLLM| AOAI
  A2 -->|rerank| COH
  BMD -.OIDC.-> KC
  C2 -.snapshot.-> BK
  C3 -.snapshot.-> BK
  C4 -.snapshot.-> BK
```

**Read in one line**: 3 custom agents + 2 filesystem→vector pipelines on stock core (Milvus/FerretDB/SeaweedFS); LLM via
**Azure OpenAI Sweden** (⚠ sovereignty); Cohere rerank; Swiss LLM Cloud for OCR; identity via Keycloak SaaS;
**observability via Langfuse v3 (ClickHouse) + OTEL** — agent traces, LLM cost and eval; backup runs but **lands on the
same VM** (⚠). Open gaps: near-zero tests, no own arc42/ADRs, no docker resource limits, hardcoded config, an
internal-import violation, weak-model JSON fragility, 3.9× storage growth, and a non-sovereign Cohere reranker.
Near-latest pin — the cheapest upgrade of all customers.

## Level 1 — System Context

```mermaid
C4Context
    title System Context — aihub-bmd (v0.279.2)

    Person(end_user, "End User", "BMD employee — chat, RAG queries")
    Person(tenant_admin, "Tenant Admin", "Manage agents / users in BMD tenant")

    System(bmd, "aihub-bmd", "BMD customer deployment of Swiss AI Hub Core SDK")

    System_Ext(core_sdk, "aihub-core SDK", "Git tag v0.279.2 — pulled at build time")
    System_Ext(smb, "SMB Share", "On-prem file source: /mnt/smb_b*d/30 GP/31 Kunden")
    System_Ext(azure_openai_swe, "Azure OpenAI (Sweden)", "Chat + embed + image gen + STT/TTS — sovereignty violated")
    System_Ext(cohere, "Cohere Rerank API", "US/Canada vendor — rerank-english-v3.0")
    System_Ext(keycloak_saas, "Keycloak SaaS", "Identity (OIDC)")

    Rel(end_user, bmd, "Chat, RAG query", "HTTPS")
    Rel(tenant_admin, bmd, "Manage tenant", "HTTPS")

    Rel(bmd, core_sdk, "Build dependency", "git+ssh tag")
    Rel(bmd, smb, "Ingest customer + supplier docs", "SMB protocol")
    Rel(bmd, azure_openai_swe, "LLM completion / embed / image / STT-TTS", "HTTPS")
    Rel(bmd, cohere, "Rerank retrieved chunks", "HTTPS")
    Rel(bmd, keycloak_saas, "Auth", "OIDC")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Trust boundary**: end users / tenant admins / BMD deployment / Keycloak SaaS are *trusted*. SMB on customer's on-prem
is *trusted*. **Azure OpenAI Sweden** and **Cohere** are *untrusted external* — this is the sovereignty violation
flagged in Overview §1 Weaknesses and addressed by proposed
[`adr_000`](../05_proposed_adrs/adr_000_sovereignty_compliance_path.md).

## Level 2 — Container

```mermaid
C4Container
    title Container Diagram — aihub-bmd (Customer Project, v0.279.2)

    System_Ext(aihub_core_sdk, "Swiss AI Hub Core SDK", "v0.279.2 git tag")
    System_Ext(smb_share, "SMB Share", "Customer file source")
    System_Ext(aihub_platform, "aihub-core Platform", "Deployed separately")
    System_Ext(azure_openai_swe, "Azure OpenAI Sweden", "via LiteLLM")
    System_Ext(cohere, "Cohere", "Reranking")

    System_Boundary(bmd, "aihub-bmd (Customer Deployment)") {
        Container(bmd_agent_svc, "BMD Agent Service", "Python FastAPI", "Selection router")
        Container(expert_rag_svc, "Expert RAG Service", "Python FastAPI", "RAG responder")
        Container(expert_asking_svc, "Expert Asking Service", "Python FastAPI", "Expert escalation")
        Container(pipeline_customers_l1, "customers_filesystem_to_data_lake", "Dagster", "Stage 1: SMB→S3")
        Container(pipeline_customers_l2, "customers_data_lake_to_vector_store", "Dagster", "Stage 2: S3→Milvus")
        Container(pipeline_suppliers_l1, "suppliers_filesystem_to_data_lake", "Dagster", "Stage 1: SMB→S3")
        Container(pipeline_suppliers_l2, "suppliers_data_lake_to_vector_store", "Dagster", "Stage 2: S3→Milvus")
        Container(bmd_dagster_ui, "Dagster Webserver", "Dagster", "Pipeline orchestration UI")
        Container(configs, "Configs", "16 service configs (Jinja2)", "Traefik, Keycloak, OTEL, LiteLLM, etc.")
        Container(tests, "Tests", "pytest, 58 lines / 1 utility", "test_snk_enrichment.py only")
    }

    Rel(bmd_agent_svc, aihub_core_sdk, "Extends Agent base", "Python import")
    Rel(expert_rag_svc, aihub_core_sdk, "Extends Agent", "Python import")
    Rel(expert_asking_svc, aihub_core_sdk, "Extends Agent", "Python import")
    Rel(pipeline_customers_l1, aihub_core_sdk, "Uses default_definitions()", "Python import")
    Rel(pipeline_customers_l2, aihub_core_sdk, "Uses default_definitions()", "Python import")
    Rel(pipeline_suppliers_l1, aihub_core_sdk, "⚠️ snk_enrichment.py:2 internal import", "Python import")
    Rel(pipeline_suppliers_l2, aihub_core_sdk, "Uses default_definitions()", "Python import")

    Rel(pipeline_customers_l1, smb_share, "Watch + download", "SMB protocol")
    Rel(pipeline_suppliers_l1, smb_share, "Watch + download", "SMB protocol")
    Rel(pipeline_customers_l2, aihub_platform, "S3 write, Milvus insert, NATS events")
    Rel(pipeline_suppliers_l2, aihub_platform, "S3 write, Milvus insert, NATS events")

    Rel(bmd_agent_svc, aihub_platform, "NATS subscribe/publish")
    Rel(expert_rag_svc, aihub_platform, "NATS subscribe/publish + Milvus query")
    Rel(expert_rag_svc, azure_openai_swe, "LLM/embed via LiteLLM proxy")
    Rel(expert_rag_svc, cohere, "Rerank top-k chunks")
    Rel(expert_asking_svc, aihub_platform, "NATS + Teams escalation")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### BMD-specific observations

- **3 agents** (bmd_agent, expert_rag, expert_asking) + **4 pipelines** (customers × 2-stage, suppliers × 2-stage). No
  custom API.
- All consume `aihub-core SDK v0.279.2` via git tag — **11 minors drift behind core v0.290.4**.
- **One deep-import violation**: `pipelines/snk_enrichment.py:2` reaches internal module. Tracked in
  [`adr_038`](../05_proposed_adrs/adr_038_sdk_import_discipline.md).
- **6 docker-compose files** split by concern (agents, pipelines, backfill). Separation rationale undocumented (Overview
  §5.2).
- **Configs/** holds 16 Jinja2 templates — duplicate effort with core platform configs.
- **Sovereignty violation**: Azure OpenAI Sweden (LLM) + Cohere US/Canada (rerank). Subject to
  [`adr_000`](../05_proposed_adrs/adr_000_sovereignty_compliance_path.md).
- **Test coverage**: 58 lines / 1 utility test (`tests/test_snk_enrichment.py`). Agents and pipelines untested.
- **Backup**: same VM as primary (FATAL pattern, Overview §3.2 #1).
- **Identity**: Keycloak SaaS (shared realm).

### Scaling readiness

| Container         | Stateless? | Horizontal scale ready? | Notes                                              |
| ----------------- | :--------: | :---------------------: | -------------------------------------------------- |
| BMD Agent Service |     ✅     |           ✅            | Stateless dispatcher                               |
| Expert RAG        |     ✅     |           ✅            | Reads Milvus + Azure OpenAI; per-request           |
| Expert Asking     |     ✅     |           ✅            | NATS-driven                                        |
| Pipelines (L1/L2) |     ❌     |           ❌            | Dagster `in_process_executor`; inherits core DTC-6 |
| Dagster Webserver |     ❌     |           ⚠️            | Singleton; needs persistent DB                     |
| Configs           |    N/A     |           N/A           | Static at deploy time                              |

## Cross-reference

- Customer priority items:
  [`../01_architecture_review_overview.en.md#32-aihub-bd`](../01_architecture_review_overview.en.md).
- Customer concerns: [`../01_architecture_review_overview.en.md#52-aihub-bd`](../01_architecture_review_overview.en.md).
- Sovereignty path:
  [`../05_proposed_adrs/adr_000_sovereignty_compliance_path.md`](../05_proposed_adrs/adr_000_sovereignty_compliance_path.md).
- Import discipline:
  [`../05_proposed_adrs/adr_038_sdk_import_discipline.md`](../05_proposed_adrs/adr_038_sdk_import_discipline.md).
- Backup off-site:
  [`../05_proposed_adrs/adr_030_offsite_backup_replication.md`](../05_proposed_adrs/adr_030_offsite_backup_replication.md).
- Aggregate deployment + multi-customer topology: [`../03_c4_diagrams.md`](../03_c4_diagrams.md).
