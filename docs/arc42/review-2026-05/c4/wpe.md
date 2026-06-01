# C4 — aihub-wpe

> Snapshot: **aihub-wpe v0.255.6** (drift 35 minors behind core v0.290.4) as of 2026-05-28.
> New file in this review. **Deploy-only repo**: no custom agents, pipelines, API, or bot. **Security incident**:
> TLS private key committed to git — see [`adr_041`](../05_proposed_adrs/adr_041_tls_key_committed_remediation.md).

## Level 0 — High-Level Solution Architecture

Boundary-first view: core touchpoints (blue), Azure (purple), observability (green), known issues (red). WPE has **no
custom code** — it is a pure platform deployment.

```mermaid
flowchart LR
  classDef core fill:#e1f5ff,stroke:#3d8be8,color:#000
  classDef azure fill:#e6ddff,stroke:#7a5cff,color:#000
  classDef obs fill:#e1ffe1,stroke:#3da35a,color:#000
  classDef ext fill:#eeeeee,stroke:#888888,color:#000
  classDef warn fill:#ffe1e1,stroke:#e05a5a,color:#000

  ADMIN["Sys Admin<br/>manual cp docker-compose.latest.yml"]:::ext

  subgraph WPE["aihub-wpe · Gen 1 · manual VM copy-paste (⚠ no rollback / audit / drift detection) · stock core images @ CORE_VERSION v0.255.6 (drift 35) · DEPLOY-ONLY"]
    direction TB
    NOTE["No custom agents · no custom pipelines<br/>pure platform deployment"]:::ext
    subgraph CO["Swiss AI Hub Core (stock images)"]
      C0["OpenWebUI + API + agents"]:::core
      C1["NATS + dispatcher"]:::core
      C2[("Milvus")]:::core
      C3[("FerretDB · SeaweedFS")]:::core
      TR["Traefik<br/>⚠ TLS private key committed to git"]:::warn
    end
    OBS["OTEL → SigNoz Cloud (EU) · Phoenix<br/>⚠ obs data leaves tenant infra (sovereignty unclear)"]:::obs
    BK["Backup Dagster<br/>⚠ no off-site backup config in repo"]:::warn
    PERF["⚠ Platform perf complaint UNRESOLVED<br/>root cause unknown · customer unresponsive<br/>→ needs obs review + load-test baseline"]:::warn
    GAP["⚠ Other WPE gaps (deploy-only repo)<br/>${CORE_VERSION:-latest} fallback to 'latest' (no fail-fast pin)<br/>VOLUME_ROOT defaults to local relative dir in prod<br/>no tests / no post-deploy smoke check · no own arc42 / ADRs"]:::warn
  end

  AOAI["Azure OpenAI<br/>⚠ region unverified (env-only)"]:::azure
  EID["Azure AD / Entra · OIDC"]:::azure
  LE["Let's Encrypt · ACME"]:::ext

  ADMIN -->|deploy| WPE
  C0 --> C1
  C1 --> OBS
  C0 -->|LLM via LiteLLM| AOAI
  C2 -.snapshot.-> BK
  C3 -.snapshot.-> BK
  WPE -.OIDC.-> EID
  TR -.ACME.-> LE
```

**Read in one line**: deploy-only — stock core images pinned by `CORE_VERSION`, no custom agents/pipelines; LLM via Azure
OpenAI (⚠ region unverified); identity Azure AD; Traefik holds a **TLS key that leaked into git** (adr_041). The open
problem: the customer reports **poor platform performance**, root cause is unknown and they are **unresponsive** — needs
observability review + a load-test baseline to diagnose. Other gaps: manual copy-paste deploy (no rollback/audit),
`${CORE_VERSION:-latest}` fallback, VOLUME_ROOT local default, no off-site backup in repo, no tests/smoke, no own
arc42/ADRs, SigNoz Cloud EU (sovereignty), drift 35.

## Level 1 — System Context

```mermaid
C4Context
    title System Context — aihub-wpe (v0.255.6, deploy-only)

    Person(end_user, "End User", "WPE user — chat, RAG via OpenWebUI knowledge")
    Person(sys_admin, "Sys Admin", "Manual cp docker-compose.latest.yml /opt/docker/config/bbv/")

    System(wpe, "aihub-wpe", "WPE deploy-only — pulls core images via CORE_VERSION env")

    System_Ext(core_images, "ghcr.io/bbvch-ai/aihub-core", "Core container images — pinned via CORE_VERSION")
    System_Ext(azure_openai, "Azure OpenAI", "⚠️ Region NOT in repo (env-only) — sovereignty unverified")
    System_Ext(azure_ad, "Azure AD / Entra ID", "Microsoft v2.0 — OAuth")
    System_Ext(letsencrypt, "Let's Encrypt", "Traefik ACME — cert lifecycle")

    Rel(end_user, wpe, "OpenWebUI chat, RAG queries", "HTTPS")
    Rel(sys_admin, wpe, "Manual deploy: cp docker-compose.latest.yml + docker compose up -d", "SSH")

    Rel(wpe, core_images, "docker pull at deploy time", "OCI")
    Rel(wpe, azure_openai, "LLM completion / embed", "HTTPS")
    Rel(wpe, azure_ad, "OAuth login", "OIDC")
    Rel(wpe, letsencrypt, "ACME challenge for *.ai-agents.ch", "HTTP-01")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Trust boundary**: end user / sys admin / WPE deployment / Azure AD / Let's Encrypt are *trusted*. **Azure OpenAI
region is unverifiable from repo** — only `AZURE_OPENAI_BASE_URL` env var in `.env.prod` (sensitive-file-guarded);
sovereignty status undefined (Overview §3.5 #3). **`wpe.ai-agents.ch+1-key.pem` and `wpe.ai-agents.ch+1.pem`
are tracked in git** alongside production-domain certificate — see remediation runbook
[`adr_041`](../05_proposed_adrs/adr_041_tls_key_committed_remediation.md).

## Level 2 — Container

```mermaid
C4Container
    title Container Diagram — aihub-wpe (Deploy-only Manual VM, v0.255.6)

    System_Ext(core_images, "ghcr.io/bbvch-ai/aihub-core", "Image registry — CORE_VERSION pin")
    System_Ext(azure_openai, "Azure OpenAI", "via LiteLLM proxy")
    System_Ext(azure_ad, "Azure AD / Entra", "OAuth")
    System_Ext(letsencrypt, "Let's Encrypt", "TLS cert issuer")

    System_Boundary(wpe, "aihub-wpe (Manual VM Deployment, ~30 containers)") {
        Container(traefik, "Traefik", "Reverse proxy", "5 ingress hosts; TLS via Let's Encrypt")
        Container(oauth_proxy, "oauth2-proxy", "Auth proxy", "Bridges Azure AD to internal services")
        Container(openwebui, "OpenWebUI", "Chat UI", "User-facing chat")
        Container(api, "API Gateway", "FastAPI (core image)", "REST + SSE")
        Container(litellm, "LiteLLM Proxy", "core image", "Routes to Azure OpenAI base URL from .env.prod")
        Container(llm_wrapping_agent, "llm_wrapping_agent", "core image", "Core default agent")
        Container(rag_agent, "rag_agent", "core image", "Core default RAG agent")
        Container(default_rag_pipeline, "default_rag_pipeline", "core Dagster", "User-uploaded docs ingestion")

        ContainerDb(ferretdb, "FerretDB", "core image", "Document store")
        ContainerDb(milvus, "Milvus v2.5.15", "Vector DB", "User RAG knowledge")
        ContainerDb(seaweedfs, "SeaweedFS", "core image", "User uploads")
        ContainerDb(postgres, "PostgreSQL", "core image", "Multiple DBs")
        ContainerDb(valkey, "Valkey", "core image", "Cache / sessions")
        ContainerQueue(nats, "NATS JetStream", "core image", "Events")
        Container(phoenix, "Phoenix v10.0.4", "Observability", "⚠️ Pre-Langfuse (ADR 2026_02_10)")
        Container(signoz_collector, "SigNoz OTEL collector", "host metrics + OTLP", "Ships to SigNoz Cloud EU")

        Container(tls_cert_in_git, "wpe.ai-agents.ch+1*.pem", "⚠️ Tracked in git", "Cert + private key — adr_041")
    }

    Rel(traefik, oauth_proxy, "Auth gate")
    Rel(traefik, openwebui, "After auth")
    Rel(traefik, api, "After auth")
    Rel(oauth_proxy, azure_ad, "OAuth", "OIDC")
    Rel(traefik, letsencrypt, "ACME cert lifecycle", "HTTP-01")

    Rel(openwebui, api, "OpenAI-compat", "HTTPS")
    Rel(api, litellm, "LLM calls")
    Rel(litellm, azure_openai, "Completion / embed", "HTTPS (region from .env)")
    Rel(api, ferretdb, "Entities")
    Rel(api, valkey, "Sessions")
    Rel(api, nats, "Events")

    Rel(llm_wrapping_agent, nats, "Events")
    Rel(rag_agent, milvus, "Vector search")
    Rel(rag_agent, litellm, "LLM calls")

    Rel(default_rag_pipeline, seaweedfs, "Documents")
    Rel(default_rag_pipeline, milvus, "Insert vectors")

    Rel(ferretdb, postgres, "Storage backend")
    Rel(signoz_collector, nats, "Trace ingest")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

### WPE-specific observations

- **Deploy-only**: no custom agents, pipelines, API, or bot. Uses core `llm_wrapping_agent` + `rag_agent` +
  `default_rag_pipeline` from images pulled via `CORE_VERSION` env.
- **`CORE_VERSION="v0.255.6"`** pinned in `.env.prod`, but `docker-compose.latest.yml` has
  `${CORE_VERSION:-latest}` fallback — Overview §3.5 #5. Reproducibility risk if env var unset.
  Same anti-pattern as `aihub-k8s` (see [`adr_040`](../05_proposed_adrs/adr_040_k8s_chart_core_version_pinning.md)).
- **TLS key + cert tracked in git** (`wpe.ai-agents.ch+1-key.pem`, `wpe.ai-agents.ch+1.pem`). `.gitignore` only
  excludes `.env`. **Critical security issue** — see
  [`adr_041`](../05_proposed_adrs/adr_041_tls_key_committed_remediation.md). Production runs Traefik + Let's
  Encrypt ACME, so the committed cert is dead weight but the private key is permanently disclosed until history
  is rewritten.
- **LLM region unverifiable** from repo (Overview §3.5 #3). Sovereignty status undefined.
- **`VOLUME_ROOT:-./.docker-volumes` defaults to relative dir** — snapshot paths depend on `pwd` at compose
  invocation (Overview §3.5 #6).
- **Off-site backup not in repo** (Overview §3.5 #7). Unknown if backup exists out-of-repo.
- **Test coverage**: N/A — deploy-only, no custom code. **No smoke tests either** (Overview §3.5 #9).
- **Stack**: Phoenix v10.0.4 (pre-Langfuse), Milvus v2.5.15. Inherits core baseline at the pin's version.
- **OTEL**: SigNoz Cloud "EU" region — sovereignty implication unclear (Overview §5.8 SigNoz Cloud concern).

### Scaling readiness

| Container          | Stateless? | Horizontal scale ready? | Notes                                                  |
| ------------------ | :--------: | :---------------------: | ------------------------------------------------------ |
| Traefik            |     ✅     |           ⚠️            | ACME cert state local; would need shared store         |
| oauth2-proxy       |     ✅     |           ✅            | Token verification                                     |
| OpenWebUI          |     ⚠️     |           ⚠️            | DB-backed sessions; inherits core issue                |
| API Gateway        |     ✅     |           ✅            | Core image                                             |
| llm_wrapping_agent |     ✅     |           ✅            | Core image                                             |
| rag_agent          |     ✅     |           ✅            | Core image                                             |
| default_rag_pipeline |   ❌     |           ❌            | Core Dagster `in_process_executor`                     |
| Milvus / FerretDB / SeaweedFS / Valkey / NATS / PG | ❌ | ❌  | All single-instance; core defaults                     |

## Cross-reference

- Customer priority items: [`../01_architecture_review_overview.en.md#35-aihub-wp`](../01_architecture_review_overview.en.md).
- Customer concerns: [`../01_architecture_review_overview.en.md#55-aihub-wp`](../01_architecture_review_overview.en.md).
- **TLS-key incident remediation**: [`../05_proposed_adrs/adr_041_tls_key_committed_remediation.md`](../05_proposed_adrs/adr_041_tls_key_committed_remediation.md).
- K8s chart pinning policy (relates to CORE_VERSION fallback):
  [`../05_proposed_adrs/adr_040_k8s_chart_core_version_pinning.md`](../05_proposed_adrs/adr_040_k8s_chart_core_version_pinning.md).
- Sovereignty path: [`../05_proposed_adrs/adr_000_sovereignty_compliance_path.md`](../05_proposed_adrs/adr_000_sovereignty_compliance_path.md).
- Aggregate deployment + multi-customer topology: [`../03_c4_diagrams.md`](../03_c4_diagrams.md).
