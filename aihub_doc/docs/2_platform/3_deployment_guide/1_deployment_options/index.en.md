---
title: Deployment Options
---

# Deployment Options

## Overview

The AI-Hub can be deployed as a single isolated instance for one organization, or as multiple isolated instances that optionally share backend LLM resources.

## Single tenant deployment

### Isolated instance

A single tenant deployment runs a complete, self-contained AI-Hub instance. The organization gets dedicated infrastructure: separate databases, vector stores, file storage, and application services. Unlike multi-tenant SaaS platforms where customers share databases and application servers, a tenant has its own dedicated stack.

The instance includes the API, agents, pipelines, web interface, and bot integrations. It has its own databases (FerretDB/PostgreSQL), vector stores (Milvus or Azure AI Search), and file storage (SeaweedFS or Azure Data Lake). Monitoring runs through SigNoz and Phoenix. NATS handles event streaming. The instance has its own LiteLLM proxy for cost tracking and version control.

### LLM backend

The instance connects to LLM services via its LiteLLM proxy. The proxy can connect to Azure OpenAI, Google Gemini, self-hosted models (vLLM, llama.cpp, HF-TEI), or a mix of these. The proxy handles model selection, budgets, rate limits, and versions. All prompts, responses, and user data stay within the tenant instance.

---

## Hosting options

The AI-Hub can be hosted in three ways depending on organizational requirements.

### On-premise (bring your own server)

You run the AI-Hub on your own servers in your data center.

You need x86_64 servers with CPU, RAM, and storage. NVIDIA GPUs work for self-hosted LLM inference. For network access, either outbound HTTPS for cloud-based LLM services, or air-gapped with local models.

Infrastructure is under your control. No cloud dependencies. Works in air-gapped environments with self-hosted LLMs.

---

### Private cloud (bring your own cloud)

You run the AI-Hub in your own cloud environment (Swiss cloud provider, Azure, AWS, GCP).

Data stays in your cloud account under your control. You choose the region (e.g., Switzerland for data residency). You manage the cloud resources and costs.

Cloud providers typically have security and compliance certifications. You need internet connectivity for LLM proxy access (HTTPS), optionally VPN for administrative access, and private networking between services (internal DNS).

---

### SaaS (Swiss cloud hosting)

bbv hosts and manages the AI-Hub for you on Swiss-based cloud infrastructure.

bbv handles infrastructure provisioning, updates, backups, monitoring, and operational tasks. Data stays in Switzerland under Swiss legal jurisdiction. Security and compliance certifications from the cloud provider.

You access the AI-Hub through a web interface and APIs. bbv provides SLAs for uptime and support. Less operational overhead for your team.

---

## Multi-tenant deployment

### Shared LLM backend

When deploying multiple tenant instances, they can share backend LLM resources. Multiple tenants use the same Azure OpenAI subscription, Google Gemini API keys, or self-hosted models. They can also share authentication infrastructure like Azure AD or Keycloak.

Each tenant still has their own LiteLLM proxy. The proxy handles model selection, budgets, rate limits, and versions per tenant. LLM usage is tracked per tenant. Prompts, responses, and user data stay within each tenant instance.

The shared LLM backends are stateless. They don't persist prompts or responses. Conversational context and history remain in each tenant's own infrastructure.

## Characteristics

### Data isolation

Each tenant's data stays in their instance. There's no shared database or vector store. Data can't leak between organizations. The setup meets Swiss Data Protection Law (revDSG), GDPR data isolation requirements, and Swiss public sector security standards.

### Configuration

Each instance can be configured independently. Tenants can deploy custom agents, specialized pipelines for their data sources, their own access control (RBAC, OIDC with local IdP), custom knowledge bases, and dedicated authentication providers like Azure AD or Keycloak.

### Scaling and updates

Resource allocation is per-tenant. You scale compute, memory, and storage based on actual usage. Each tenant can apply updates on their own schedule. Testing new features in one instance doesn't affect others. SLAs vary per contract.

### Compliance and auditing

Auditors can inspect a single tenant's infrastructure. Logs and traces stay within the tenant instance. Backup retention policies can be configured per tenant. Penetration testing can be scoped to individual instances.

## Deployment model

### Single tenant infrastructure

A single tenant deployment contains:

```
Tenant Instance
├── Application Layer
│   ├── API Service (FastAPI + WebSocket gateway)
│   ├── Web Interface (Nuxt.js frontend)
│   ├── OpenWebUI (LLM chat interface)
│   ├── Agent Services (RAG, specialized agents)
│   ├── Pipeline Services (Dagster + custom pipelines)
│   └── Bot Service (MS Teams, Slack integrations)
│
├── Data Layer
│   ├── Database (FerretDB + PostgreSQL)
│   ├── Vector Store (Milvus or Azure AI Search)
│   ├── Document Store (SeaweedFS or Azure Data Lake)
│   └── Cache (Valkey)
│
├── LLM Layer
│   ├── LiteLLM Proxy
│   │   ├── Cost tracking and budgets
│   │   ├── Model routing configuration
│   │   ├── Rate limiting
│   │   └── Version control
│   └── Presidio (PII anonymization)
│
├── Observability Layer
│   ├── Phoenix (AI tracing and evaluation)
│   └── OpenTelemetry (distributed tracing)
│
└── Infrastructure Layer
    ├── NATS (message bus)
    ├── Docling (document processing)
    └── Traefik (reverse proxy + SSL termination)
```

The LiteLLM proxy connects to LLM services (Azure OpenAI, Google Gemini, self-hosted models).

### Multi-tenant infrastructure

When deploying multiple tenants, each tenant gets the same infrastructure shown above. They can share backend LLM resources:

```
Shared LLM Backend Resources
├── LLM API Subscriptions
│   ├── Azure OpenAI subscription (shared API keys)
│   ├── Google Gemini API keys
│   └── Other cloud provider credentials
│
├── Self-Hosted Model Infrastructure
│   ├── vLLM deployment (GPU cluster)
│   ├── llama.cpp servers
│   └── HF-TEI instances
│
└── Optional Shared Services
    ├── Central Authentication (Azure AD, Keycloak)
    └── Central Monitoring Dashboard (optional)
```

Network architecture:
- Each tenant has their own LiteLLM proxy instance
- Tenant LiteLLM proxies connect to shared LLM backends (Azure OpenAI, Gemini, self-hosted models)
- Shared LLM backends use common API credentials (configured per tenant's LiteLLM)
- No direct communication between tenant instances
- Optional: Shared authentication provider (Azure AD, Keycloak)

Data isolation and sovereignty. Independent scaling and resource allocation. Custom configurations per tenant. Flexible update schedules. Clear compliance boundaries.

---

## Architecture diagrams

### Single tenant deployment

```mermaid
graph TB
    subgraph Tenant["Tenant Instance"]
        Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        Proxy["LiteLLM Proxy"]
        Stack --- Proxy
    end

    Backend["LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

    Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

The tenant instance connects to LLM services via its LiteLLM proxy.

### Multi-tenant deployment with shared LLM backend

```mermaid
graph TB
    Backend["Shared LLM Backend<br/>(Azure OpenAI, Gemini, vLLM)"]

    subgraph Tenant1["Tenant 1"]
        T1Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T1Proxy["LiteLLM Proxy"]
        T1Stack --- T1Proxy
    end

    subgraph Tenant2["Tenant 2"]
        T2Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T2Proxy["LiteLLM Proxy"]
        T2Stack --- T2Proxy
    end

    subgraph Tenant3["Tenant 3"]
        T3Stack["Full Stack<br/>(API, Agents, DB, Vector Store)"]
        T3Proxy["LiteLLM Proxy"]
        T3Stack --- T3Proxy
    end

    T1Proxy -->|HTTPS| Backend
    T2Proxy -->|HTTPS| Backend
    T3Proxy -->|HTTPS| Backend

    classDef default font-size:16px,padding:20px
```

Each tenant has their own LiteLLM proxy instance (independent cost tracking, versioning, configuration). All tenant LiteLLM proxies connect to shared LLM backend resources (Azure OpenAI subscriptions, self-hosted models). Prompts, responses, and user data stay within tenant boundaries.

---

## Security considerations

### Tenant isolation

Tenant instances do not communicate with each other. Each tenant has separate databases, vector stores, and file storage. Each tenant connects to their own IdP (Azure AD, Keycloak). LiteLLM enforces per-tenant API keys and quotas.

### LLM proxy security

LiteLLM does not persist prompts or responses (stateless operation). API key management includes secure key generation, rotation, and revocation. Per-tenant request limits prevent abuse. All LLM requests are logged with tenant ID but without prompt content. Presidio integration is optional for PII detection and redaction.

### Data in transit

All communication is encrypted with TLS (tenant to LLM proxy). Certificate management uses Let's Encrypt for production and mkcert for development. API authentication uses bearer tokens (OAuth 2.0, JWT).

### Data at rest

PostgreSQL uses transparent data encryption (TDE). Persistent volumes are encrypted (LUKS, Azure Disk Encryption). Secrets are managed via environment variables, Azure Key Vault, or Docker secrets.

---

## Next steps

- [Production Configuration](../2_production_configuration/) - Configuration guide for production deployments
- [Scaling Considerations](../3_scaling_considerations/) - Scaling tenant instances
- [Backup and Recovery](../4_backup_and_recovery/) - Backup strategies for per-tenant architecture
- [Updates and Maintenance](../6_updates_and_maintenance/) - Managing updates across multiple instances

---

## FAQ

::: details Can tenants share agents or pipelines?

No. Each tenant instance has its own isolated set of agents and pipelines. However, the same agent definitions (code) can be deployed across multiple tenant instances. Customizations are tenant-specific.
:::

::: details What data does the shared LLM backend see?

Each tenant has their own LiteLLM proxy, so prompts and responses stay within the tenant instance. The shared LLM backends (Azure OpenAI, Gemini, self-hosted models) see API requests from multiple tenant LiteLLM proxies (stateless, not persisted), model inference requests (prompts and completions in transit only), no tenant identification or context, and anonymous PII data if enabled.

They do not see which tenant made the request, conversational history, or any stored data. All context remains in the tenant's LiteLLM proxy and database.
:::

::: details Can a tenant use self-hosted models exclusively?

Yes. For air-gapped or fully on-premise deployments, you can deploy self-hosted LLMs (vLLM, llama.cpp, HF-TEI), configure LiteLLM to route to local models, and run with no outbound internet connectivity required.
:::

::: details How are costs tracked per tenant?

LiteLLM tracks API usage per tenant and user: token counts (input/output), model usage (GPT-4, Gemini, etc.), cost calculations based on model pricing, and monthly budget enforcement.

Data is available in the LiteLLM admin UI and exportable for billing.
:::

::: details Can tenants have different LLM access?

Yes. LiteLLM configuration allows per-tenant model access. For example, Tenant A might only use GPT-4o for strict compliance, Tenant B might use GPT-4o plus Gemini 2.0 for more flexibility, and Tenant C might use self-hosted models only for air-gapped deployment.

:::

::: details What happens if the LLM proxy is unavailable?

Tenant instances will experience LLM-dependent feature degradation. RAG agents cannot generate responses. Embeddings cannot be created for new documents. However, existing data and UI remain accessible, and non-LLM features (document upload, RBAC, observability) continue working.

Mitigation: Deploy LiteLLM with high availability (multiple replicas, load balancing).
:::

::: details How do you manage updates across many tenant instances?

See [Updates and Maintenance](../6_updates_and_maintenance/) for strategies including phased rollouts (pilot to production), blue-green deployments, automated update orchestration (Ansible, Kubernetes operators), and per-tenant update schedules.

:::

## Related documentation

- [Core Components](../../2_architecture/1_core_components/) - AI-Hub architecture
- [Authentication & Authorization](../../11_access_management/1_authentication_setup/) - Tenant authentication configuration
- [Monitoring and Alerting](../5_monitoring_and_alerting/) - Observability for multi-instance deployments
- [Swiss Data Protection](../../19_compliance/3_dsg/) - revDSG compliance for public sector