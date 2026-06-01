# C4 — aihub-fmh

> Snapshot: **aihub-fmh v0.186.0** (drift 104 minors behind core v0.290.4 — **largest of any customer**) as of
> 2026-05-28. New file in this review. Uses **Azure AI Search instead of Milvus** (stack divergence) — see
> [`adr_039`](../05_proposed_adrs/adr_039_fmh_azure_ai_search_vs_milvus.md).

## Level 0 — High-Level Solution Architecture

Boundary-first view: custom code (amber), core touchpoints (blue), Azure (purple), known issues (red). Fully
Azure-native (Pulumi → Container Apps).

```mermaid
flowchart LR
  classDef custom fill:#fff4e1,stroke:#e8a33d,color:#000
  classDef core fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef azure fill:#e6ddff,stroke:#7a5cff,color:#000
  classDef obs fill:#e1ffe1,stroke:#3da35a,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  ADL[("Azure Data Lake Gen2<br/>TARDOC / TARMED handbook + positions<br/>structured data")]:::azure
  TEAMS["MS Teams<br/>Bot Framework"]:::ext

  subgraph FMH["aihub-fmh · Gen 1 · Pulumi → Azure Container Apps (cloud-native, 10 deploy units) · ⚠ Python 3.11 (oldest, EOL) · core v0.186.0 (very old · 104 behind — largest drift)"]
    direction TB
    subgraph AG["Custom agents · Container Apps · ⚠ LlamaIndex monkey-patch for GPT-5 (register_openai_models.py)"]
      A1["routing_agent"]:::custom
      A2["handbook_agent"]:::custom
      A3["rules_agent"]:::custom
    end
    subgraph PI["Custom pipelines · Dagster"]
      P1["handbook_ingestion"]:::custom
      P2["position_ingestion"]:::custom
    end
    subgraph CO["Core SDK (extended) + ⚠ divergent stack"]
      C1["NATS + dispatcher"]:::core
      BOT["bot adapter<br/>⚠ MS Bot Framework + dev tunnel (dev/prod parity risk)"]:::core
      C2[("MongoDB — ⚠ not FerretDB")]:::warn
      C3[("Redis — ⚠ not Valkey")]:::warn
    end
    EVAL["evaluation/ framework<br/>⚠ no test strategy · answers unsatisfactory"]:::warn
    OBS["Phoenix v10 + OTEL<br/>⚠ pre-Langfuse (diverges from core)"]:::warn
    BK["Backup / restore<br/>⚠ no backup workload in Pulumi (status unknown)"]:::warn
    GAP["⚠ Other FMH gaps<br/>minimal tests (5 test_*.py + 5 .feature for 3 agents / 2 pipelines) · no own arc42 / ADRs<br/>hardcoded handbook namespace (handbook_02_2026) in pipeline __init__.py<br/>SDK drift 104 minors — largest of all customers → multi-step upgrade"]:::warn
  end

  AIS[("Azure AI Search<br/>⚠ NOT Milvus · vendor lock<br/>⚠ vector design for structured data not optimised")]:::warn
  AOAI["Azure OpenAI EUR + SUI<br/>chat · embed"]:::azure
  EID["Azure AD · OIDC · ⚠ vendor lock-in"]:::azure
  PST["Azure Storage<br/>Pulumi state · ⚠ SPOF"]:::azure

  ADL -->|ingest structured| P1
  ADL -->|ingest structured| P2
  P1 --> AIS
  P2 --> AIS
  A1 --> A2
  A1 --> A3
  A2 -->|RAG search| AIS
  A1 --> C1
  A2 --> C1
  A3 --> C1
  TEAMS -->|webhook| BOT
  BOT --> C1
  C1 --> OBS
  C1 -.events.-> C2
  C1 -.steps.-> C3
  A2 -->|LLM via LiteLLM| AOAI
  EVAL -.evaluates.-> A2
  FMH -.OIDC.-> EID
  FMH -.state.-> PST
```

**Read in one line**: routing/handbook/rules agents on **Azure Container Apps** (Pulumi-deployed), ingesting **structured
TARDOC/TARMED** data into **Azure AI Search** (⚠ not Milvus — vendor lock); LLM via Azure OpenAI EUR+SUI; Teams bot front
door. The customer is **unhappy with answer quality** — the likely root cause is **vector/ingestion design for structured
data** plus the **absence of a testing/eval strategy** (the eval framework exists but is unused). Oldest pin of all
customers (104 minors behind) → multi-step upgrade. Other gaps: GPT-5 LlamaIndex monkey-patch, Mongo/Redis/Phoenix
divergence, bot dev-tunnel parity risk, Azure vendor lock-in, no backup workload in Pulumi, Pulumi-state SPOF, Python 3.11
(EOL), hardcoded handbook namespace, no own arc42/ADRs.

## Level 1 — System Context

```mermaid
C4Context
    title System Context — aihub-fmh (v0.186.0)

    Person(end_user, "End User", "Swiss medical professional — TARDOC / TARMED queries")
    Person(tenant_admin, "Tenant Admin", "Manage configs / handbook snapshots")
    Person(teams_user, "MS Teams User", "Bot conversation via Microsoft Bot Framework")
    Person(evaluator, "Evaluator", "Runs aihub-fmh/evaluation/ framework against testsets")

    System(fmh, "aihub-fmh", "FMH customer deployment — Swiss medical billing AI")

    System_Ext(core_sdk, "aihub-core SDK", "Git tag v0.186.0 — 104 minors behind")
    System_Ext(azure_openai_sui, "Azure OpenAI Switzerland North", "*-openai-sui — chat + embed; defensible Swiss region")
    System_Ext(azure_ai_search, "Azure AI Search", "Vector backend — ⚠️ NOT Milvus (adr_039)")
    System_Ext(azure_data_lake, "Azure Data Lake Gen2", "TARDOC / TARMED handbook + positions source")
    System_Ext(azure_ad, "Azure AD", "AUTH_AZURE_AD_* — identity")
    System_Ext(teams_platform, "MS Bot Framework", "Teams integration")
    System_Ext(pulumi_state, "Azure Storage Account", "Pulumi state — SPOF (single Azure account)")

    Rel(end_user, fmh, "TARDOC billing queries via chat + Teams bot", "HTTPS")
    Rel(teams_user, teams_platform, "Bot message", "Teams")
    Rel(teams_platform, fmh, "Bot Framework webhook", "REST")
    Rel(tenant_admin, fmh, "Manage handbook snapshots", "HTTPS")
    Rel(evaluator, fmh, "Run evaluation framework", "Python / Excel test catalogue")

    Rel(fmh, core_sdk, "Build dependency", "git+ssh tag")
    Rel(fmh, azure_openai_sui, "LLM completion / embed", "HTTPS")
    Rel(fmh, azure_ai_search, "Vector search + index", "Azure SDK")
    Rel(fmh, azure_data_lake, "TARDOC / TARMED docs", "Azure SDK")
    Rel(fmh, azure_ad, "OAuth", "OIDC")
    Rel(fmh, pulumi_state, "Deploy state", "Azure SDK")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Trust boundary**: end users / tenant admin / Teams users / evaluators / FMH deployment / Azure AD are *trusted*.
**Azure OpenAI Switzerland North** is *defensible* — TARDOC/TARMED data is Swiss-only by mandate. **Azure AI
Search** is *managed external service* — every retrieval is a paid query call. **Pulumi state in single Azure
storage account** is a SPOF (Overview §3.6 #9).

## Level 2 — Container

```mermaid
C4Container
    title Container Diagram — aihub-fmh (Customer Project, v0.186.0)

    System_Ext(aihub_core_sdk, "Swiss AI Hub Core SDK", "v0.186.0 git tag — 104 minors behind")
    System_Ext(azure_openai_sui, "Azure OpenAI Switzerland", "via LiteLLM")
    System_Ext(azure_ai_search, "Azure AI Search", "Vector + retrieval — NOT Milvus")
    System_Ext(azure_data_lake, "Azure Data Lake Gen2", "TARDOC / TARMED source")
    System_Ext(teams_platform, "MS Bot Framework", "Teams")
    System_Ext(aihub_platform, "aihub-core Platform", "Deployed via Pulumi (10 deploy units)")

    System_Boundary(fmh, "aihub-fmh (Customer Deployment)") {
        Container(handbook_agent, "handbook_agent", "FastAPI", "TARDOC handbook Q&A")
        Container(rules_agent, "rules_agent", "FastAPI", "Billing rules logic")
        Container(routing_agent, "routing_agent", "FastAPI", "Routes to handbook or rules")
        Container(handbook_pipeline, "handbook_ingestion", "Dagster", "⚠️ hardcoded namespace `handbook_02_2026`")
        Container(position_pipeline, "position_ingestion", "Dagster", "TARMED positions")
        Container(custom_api, "Custom API", "FastAPI", "FMH-specific endpoints")
        Container(bot, "Bot Service", "MS Bot Framework", "Teams integration; ⚠️ devtunnel ref in repo")
        Container(eval_framework, "evaluation/", "Python", "Own evaluators + testsets + Excel test catalogue")
        Container(lib_common, "lib/common/", "Python lib", "⚠️ register_openai_models.py — LlamaIndex monkey-patch for GPT-5")

        ContainerDb(mongo, "MongoDB", "⚠️ Not FerretDB (divergence)")
        ContainerDb(redis, "Redis", "⚠️ Not Valkey (divergence)")
        Container(phoenix, "Phoenix v10.0.4", "Observability", "⚠️ Pre-Langfuse (ADR 2026_02_10)")
        ContainerDb(seaweedfs, "SeaweedFS", "S3-compat", "Document staging")
    }

    Rel(routing_agent, handbook_agent, "AgentInTheLoop")
    Rel(routing_agent, rules_agent, "AgentInTheLoop")

    Rel(handbook_agent, lib_common, "Import")
    Rel(rules_agent, lib_common, "Import")
    Rel(routing_agent, lib_common, "Import")
    Rel(handbook_pipeline, lib_common, "Import")
    Rel(position_pipeline, lib_common, "Import")
    Rel(lib_common, aihub_core_sdk, "Imports + ⚠️ LlamaIndex monkey-patch at import time")

    Rel(handbook_pipeline, azure_data_lake, "Pull TARDOC handbook")
    Rel(handbook_pipeline, azure_ai_search, "Insert embeddings")
    Rel(position_pipeline, azure_data_lake, "Pull TARMED positions")
    Rel(position_pipeline, azure_ai_search, "Insert embeddings")

    Rel(handbook_agent, azure_ai_search, "Vector search — per-query cost")
    Rel(rules_agent, azure_ai_search, "Vector search")
    Rel(handbook_agent, azure_openai_sui, "LLM completion via LiteLLM")
    Rel(rules_agent, azure_openai_sui, "LLM completion via LiteLLM")

    Rel(bot, teams_platform, "Bot Framework webhook")
    Rel(bot, routing_agent, "Forward user message via NATS")

    Rel(eval_framework, handbook_agent, "Run testsets — DignityCheck / RecognitionCheck BITL events")
    Rel(eval_framework, rules_agent, "Run testsets")

    Rel(custom_api, mongo, "FMH-specific entities")
    Rel(handbook_agent, phoenix, "Tracing")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### FMH-specific observations

- **3 agents** (`handbook_agent`, `rules_agent`, `routing_agent`) + **2 pipelines** (`handbook_ingestion`,
  `position_ingestion`) + **custom API** + **bot** (MS Bot Framework) + **evaluation framework**.
- **SDK drift 104 minors** (v0.186.0 vs core v0.290.4) — **largest of all customers**. ~10+ months of patches
  missed. Incremental upgrade plan: v0.186 → v0.220 → v0.260 → v0.290 (Overview §3.6 #1).
- **LlamaIndex monkey-patch** for GPT-5 (`lib/common/register_openai_models.py`) — modifies third-party globals
  at import time. Will drop on SDK upgrade if not first-classed. See Overview §3.6 #2 and
  [`adr_038`](../05_proposed_adrs/adr_038_sdk_import_discipline.md).
- **Azure AI Search instead of Milvus** (Overview §3.6 #3) — vendor lock-in + double inference cost (AI Search
  query fee + LLM call). Formal decision needed: see
  [`adr_039`](../05_proposed_adrs/adr_039_fmh_azure_ai_search_vs_milvus.md).
- **Stack divergence** (Overview §3.6 #5): MongoDB + Redis + Phoenix v10.0.4 (pre-Langfuse) — same pattern as
  Demoscope. Tied to SDK upgrade.
- **Hardcoded handbook namespace** `handbook_02_2026` in `pipelines/handbook_ingestion/__init__.py` (Overview
  §3.6 #11). Monthly snapshots require code change.
- **Pulumi committed** (10 deploy units: `agents`, `ai`, `api`, `bot`, `dagster`, `nats`, `network`, `openwebui`,
  `phoenix`, `stores`) — **best IaC of any new customer**. But state in single Azure storage account → SPOF
  (Overview §3.6 #9).
- **Test coverage**: 5 `test_*.py` + 5 BDD `.feature` files for 3 agents + 2 pipelines. Plus own evaluation
  framework in `evaluation/` (12 Python files + own evaluators + testsets + Excel test catalogue) —
  **best evaluation framework of any customer**.
- **Bot**: MS Bot Framework + dev tunnel workflow. README references `devtunnel` (Overview §3.6 #8) — dev/prod
  parity risk.
- **Backup**: not visible in Pulumi `stores/` (Overview §3.6 #4) — Azure Backup policy + cross-region replication
  for TARDOC/TARMED data unverified.
- **Sovereignty**: Azure OpenAI Switzerland North is defensible for Swiss-only data. Azure AI Search is paid +
  vendor lock-in. See [`adr_039`](../05_proposed_adrs/adr_039_fmh_azure_ai_search_vs_milvus.md).

### Scaling readiness

| Container               | Stateless? | Horizontal scale ready? | Notes                                                                |
| ----------------------- | :--------: | :---------------------: | -------------------------------------------------------------------- |
| handbook_agent          |     ✅     |           ✅            | Per-request                                                          |
| rules_agent             |     ✅     |           ✅            | Per-request                                                          |
| routing_agent           |     ✅     |           ✅            | Stateless dispatcher                                                 |
| Custom API              |     ✅     |           ✅            | -                                                                    |
| Bot                     |     ✅     |           ⚠️            | MS Bot Framework session handling                                    |
| Pipelines (handbook / position) | ❌  |           ❌            | Dagster `in_process_executor`; hardcoded namespace                   |
| evaluation/             |     N/A    |           N/A           | Offline runner                                                       |
| MongoDB / Redis / Phoenix | ❌       |           ❌            | Single instance each                                                 |
| Azure AI Search         |     N/A    |           ✅            | Managed service — paid scaling                                       |

## Cross-reference

- Customer priority items: [`../01_architecture_review_overview.en.md#36-aihub-fh`](../01_architecture_review_overview.en.md).
- Customer concerns: [`../01_architecture_review_overview.en.md#56-aihub-fh`](../01_architecture_review_overview.en.md).
- **Azure AI Search vs Milvus decision**:
  [`../05_proposed_adrs/adr_039_fmh_azure_ai_search_vs_milvus.md`](../05_proposed_adrs/adr_039_fmh_azure_ai_search_vs_milvus.md).
- Import discipline (covers LlamaIndex monkey-patch removal path):
  [`../05_proposed_adrs/adr_038_sdk_import_discipline.md`](../05_proposed_adrs/adr_038_sdk_import_discipline.md).
- Sovereignty path: [`../05_proposed_adrs/adr_000_sovereignty_compliance_path.md`](../05_proposed_adrs/adr_000_sovereignty_compliance_path.md).
- Backup off-site: [`../05_proposed_adrs/adr_030_offsite_backup_replication.md`](../05_proposed_adrs/adr_030_offsite_backup_replication.md).
- Aggregate deployment + multi-customer topology: [`../03_c4_diagrams.md`](../03_c4_diagrams.md).
