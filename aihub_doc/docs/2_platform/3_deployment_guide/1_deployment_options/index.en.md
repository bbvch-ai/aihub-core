---
title: Deployment Options
index: 1
---

# Deployment Options

## Overview

The AI-Hub platform is designed to meet the stringent data sovereignty, security, and compliance requirements of Swiss private and public sector organizations. Our deployment architecture balances **complete data isolation** with **operational efficiency** through a multi-instance model.

## Core Deployment Philosophy: Fully Isolated Instances with Shared LLM Backend

### The Multi-Instance Model

Unlike traditional multi-tenant SaaS platforms where customers share the same application and database infrastructure, the AI-Hub uses a **separate instance per tenant** approach. Each tenant (municipality, canton, department, or organization) receives a completely isolated AI-Hub deployment with dedicated:

- **Application Services**: API, agents, pipelines, web interface, bot integrations
- **Data Storage**: Databases (FerretDB/PostgreSQL), vector stores (Milvus/Azure AI Search)
- **File Storage**: Document storage (SeaweedFS/Azure Data Lake)
- **Observability Stack**: Monitoring, tracing, and logging infrastructure (SigNoz, Phoenix)
- **Message Bus**: Event streaming and communication (NATS)
- **LLM Proxy**: Each tenant has their own LiteLLM proxy instance for independent cost tracking and version control

### Shared Infrastructure: LLM Backend Resources

While each tenant operates a **fully isolated instance** (including their own LiteLLM proxy), certain **backend LLM resources can be shared** across tenants to optimize costs and infrastructure:

**Optionally shared Resources**:
- **API Credentials**: Shared Azure OpenAI subscriptions, Google Gemini API keys (accessed via tenant-specific LiteLLM proxies)
- **Self-Hosted Models**: Centralized vLLM, llama.cpp, or HF-TEI deployments serving multiple tenants
- **Authentication**: Central Azure AD or Keycloak for organizations managing multiple tenant instances

**Why This Hybrid Approach?**
- **Cost Efficiency**: Share expensive LLM API subscriptions and GPU infrastructure across tenants
- **Per-Tenant Control**: Each tenant configures their own LiteLLM proxy (model selection, budgets, rate limits, versions)
- **Independent Versioning**: Tenants can use different LiteLLM versions and model routing configurations
- **Granular Cost Tracking**: Each tenant's LLM usage is tracked independently through their LiteLLM proxy
- **Complete Data Isolation**: Prompts, responses, and user data never leave the tenant instance

**Privacy Guarantee**: Shared LLM backends (Azure OpenAI, Google Gemini, self-hosted models) are stateless and do not persist tenant prompts or responses. All conversational context, history, and user data remain within the isolated tenant instance.

## Why This Architecture?

This deployment model is specifically designed for organizations with strict data sovereignty and compliance needs.

### 1. Complete Data Sovereignty

Each tenant's data never leaves their isolated instance. There is no shared database, no shared vector store, and no possibility of data leakage between organizations.

**Compliance Coverage**:
- ✅ Swiss Data Protection Law (revDSG)
- ✅ GDPR requirements for data isolation
- ✅ Swiss public sector security standards

### 2. Independent Configuration and Customization

Each instance can be configured independently:
- **Custom agents** tailored to specific organizational needs
- **Specialized pipelines** for unique data sources and formats
- **Organization-specific access control** (RBAC, OIDC integration with local IdP)
- **Custom knowledge bases** and RAG configurations
- **Dedicated authentication** providers (Azure AD, Keycloak, etc.)

### 3. Independent Scaling and Updates

- **Isolated resource allocation**: Scale compute, memory, and storage per tenant's actual usage
- **Flexible update schedules**: Each tenant can apply updates at their own pace
- **Independent testing**: Test new features in one instance without affecting others
- **Tenant-specific SLAs**: Adjust uptime guarantees and support levels per contract

### 4. Simplified Compliance and Auditing

- **Clear data boundaries**: Auditors can inspect a single tenant's infrastructure
- **Isolated audit trails**: All logs and traces remain within the tenant instance
- **Tenant-specific backup policies**: Configure retention periods per organizational requirements
- **Independent security scanning**: Penetration testing can be scoped to individual instances

## Deployment Model

**Architecture**: Each tenant receives a complete, independent AI-Hub deployment.

**Infrastructure Components per Tenant**:
```
Tenant Instance
├── Application Layer
│   ├── API Service (FastAPI + WebSocket gateway)
│   ├── Web Interface (Nuxt.js frontend)
│   ├── Agent Services (RAG, specialized agents)
│   ├── Pipeline Services (Dagster + custom pipelines)
│   └── Bot Service (MS Teams, Slack integrations)
│
├── Data Layer
│   ├── Database (FerretDB + PostgreSQL)
│   ├── Vector Store (Milvus or Azure AI Search)
│   └── Document Store (SeaweedFS or Azure Data Lake)
│
├── LLM Layer (Per-Tenant)
│   ├── LiteLLM Proxy (tenant-specific instance)
│   │   ├── Cost tracking and budgets
│   │   ├── Model routing configuration
│   │   ├── Rate limiting
│   │   └── Version control
│   └── Presidio (PII anonymization)
│
├── Observability Layer
│   ├── Phoenix (AI tracing and evaluation)
│   ├── SigNoz (metrics, logs, traces)
│   └── OpenTelemetry Collector
│
└── Infrastructure Layer
    ├── NATS (message bus)
    ├── Docling (document processing)
    └── Traefik (reverse proxy + SSL termination)
```

**Shared Infrastructure (Across All Tenants)**:
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

**Network Architecture**:
- Each tenant has their own LiteLLM proxy instance
- Tenant LiteLLM proxies connect to shared LLM backends (Azure OpenAI, Gemini, self-hosted models)
- Shared LLM backends use common API credentials (configured per tenant's LiteLLM)
- No direct communication between tenant instances
- Optional: Shared authentication provider (Azure AD, Keycloak)

**Advantages**:
- ✅ Maximum data isolation and sovereignty
- ✅ Independent scaling and resource allocation
- ✅ Custom configurations per tenant
- ✅ Flexible update schedules
- ✅ Clear compliance boundaries

---

## Hosting Options

The AI-Hub supports flexible hosting to meet organizational requirements and constraints.

### Option 1: Swiss Cloud Hosting (Recommended)

**Description**: Deploy each tenant instance to a Swiss-based cloud provider with full data residency guarantees.

**Benefits**:
- ✅ Data remains in Switzerland
- ✅ Swiss legal jurisdiction
- ✅ Enterprise-grade security and compliance certifications
- ✅ Simplified disaster recovery and high availability

**Network Requirements**:
- Internet connectivity for LLM proxy access (HTTPS)
- Optional VPN for administrative access
- Private networking between tenant services (internal DNS)

---

### Option 2: On-Premise Hosting

**Description**: Deploy tenant instances entirely within the organization's own data center or server infrastructure.

**Requirements**:
- **Compute**: Modern x86_64 servers with sufficient CPU, RAM, storage
- **Optional GPU**: NVIDIA GPUs for self-hosted LLM inference
- **Network**: Outbound HTTPS for shared LLM access (or fully air-gapped with local models)

**Benefits**:
- ✅ Complete infrastructure control
- ✅ No cloud dependencies
- ✅ Existing data center infrastructure reuse
- ✅ Compatible with air-gapped environments (with self-hosted LLMs)

---

### Option 3: Hybrid Deployment

**Description**: Tenant instance on-premise or Swiss cloud, with centralized LLM infrastructure in a separate cloud region.

**Example Scenarios**:
- **Tenant instance**: Swiss cloud or on-premise
- **Shared LLM**: Azure OpenAI in EU regions or other LLM providers

**Benefits**:
- ✅ Flexibility in infrastructure placement
- ✅ Cost optimization for LLM hosting
- ✅ Greater model availability
- ✅ All data stays in Switzerland (stateless LLM access)
- ✅ Anonymization of PII data (Presidio)

---

## Architecture Diagrams

### Multi-Instance Deployment with Shared LLM Backend

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Shared LLM Backend Resources                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Cloud LLM APIs                    Self-Hosted Models         │  │
│  │  ┌─────────────────┐              ┌─────────────────┐         │  │
│  │  │ Azure OpenAI    │              │ vLLM (GPU)      │         │  │
│  │  │ (Shared creds)  │              │ llama.cpp       │         │  │
│  │  └─────────────────┘              │ HF-TEI          │         │  │
│  │  ┌─────────────────┐              └─────────────────┘         │  │
│  │  │ Google Gemini   │                                          │  │
│  │  │ (Shared API key)│                                          │  │
│  │  └─────────────────┘                                          │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────────▲──────────────────▲──────────────────▲──────────────────┘
             │                  │                  │
     HTTPS API Calls    HTTPS API Calls     HTTPS API Calls
             │                  │                  │
┌────────────┴────────┐  ┌──────┴──────────┐  ┌────┴────────────────┐
│  Tenant 1           │  │  Tenant 2       │  │  Tenant 3           │
├─────────────────────┤  ├─────────────────┤  ├─────────────────────┤
│ ┌─────────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────────┐ │
│ │ LiteLLM Proxy   │ │  │ │ LiteLLM     │ │  │ │ LiteLLM Proxy   │ │
│ │ • Cost tracking │ │  │ │ • Budgets   │ │  │ │ • Cost tracking │ │
│ │ • Rate limits   │ │  │ │ • Routing   │ │  │ │ • Rate limits   │ │
│ └─────────────────┘ │  │ └─────────────┘ │  │ └─────────────────┘ │
│                     │  │                 │  │                     │
│ • API Service       │  │ • API Service   │  │ • API Service       │
│ • Web Interface     │  │ • Web Interface │  │ • Web Interface     │
│ • Agents            │  │ • Agents        │  │ • Agents            │
│ • Pipelines         │  │ • Pipelines     │  │ • Pipelines         │
│ • Database          │  │ • Database      │  │ • Database          │
│ • Vector Store      │  │ • Vector Store  │  │ • Vector Store      │
│ • File Storage      │  │ • File Storage  │  │ • File Storage      │
│ • Observability     │  │ • Observability │  │ • Observability     │
└─────────────────────┘  └─────────────────┘  └─────────────────────┘
```

**Key Points**:
- Each tenant has their **own LiteLLM proxy instance** (independent cost tracking, versioning, configuration)
- All tenant LiteLLM proxies connect to **shared LLM backend resources** (Azure OpenAI subscriptions, self-hosted models)
- **Complete data isolation**: Prompts, responses, and user data stay within tenant boundaries
- **Cost efficiency**: Shared expensive LLM API subscriptions and GPU infrastructure

---

## Security Considerations

### Tenant Isolation

- **Network Isolation**: Tenant instances do not communicate with each other
- **Data Isolation**: Separate databases, vector stores, and file storage per tenant
- **Authentication Isolation**: Each tenant connects to their own IdP (Azure AD, Keycloak)
- **API Key Isolation**: LiteLLM enforces per-tenant API keys and quotas

### LLM Proxy Security

- **Stateless Operation**: LiteLLM does not persist prompts or responses
- **API Key Management**: Secure key generation, rotation, and revocation
- **Rate Limiting**: Per-tenant request limits to prevent abuse
- **Audit Logging**: All LLM requests logged with tenant ID (without prompt content)
- **PII Anonymization**: Optional Presidio integration for PII detection/redaction

### Data in Transit

- **TLS**: All communication encrypted (tenant ↔ LLM proxy)
- **Certificate Management**: Let's Encrypt for production, mkcert for development
- **API Authentication**: Bearer tokens (OAuth 2.0, JWT)

### Data at Rest

- **Database Encryption**: PostgreSQL with transparent data encryption (TDE)
- **Volume Encryption**: Encrypted persistent volumes (LUKS, Azure Disk Encryption)
- **Secret Management**: Environment variables, Azure Key Vault, Docker secrets

---

## Next Steps

- [Production Configuration](../2_production_configuration/) - Detailed configuration guide for production deployments
- [Scaling Considerations](../3_scaling_considerations/) - How to scale tenant instances
- [Backup and Recovery](../4_backup_and_recovery/) - Backup strategies for per-tenant architecture
- [Updates and Maintenance](../6_updates_and_maintenance/) - Managing updates across multiple instances

---

## FAQ

::: details Q: Can tenants share agents or pipelines?

**A**: No. Each tenant instance has its own isolated set of agents and pipelines. However, the same agent *definitions* (code) can be deployed across multiple tenant instances. Customizations are tenant-specific.
:::

::: details Q: What data does the shared LLM backend see?

**A**: Each tenant has their own LiteLLM proxy, so prompts/responses stay within the tenant instance. The shared LLM backends (Azure OpenAI, Gemini, self-hosted models) see:
- API requests from multiple tenant LiteLLM proxies (stateless, not persisted)
- Model inference requests (prompts and completions in transit only)
- No tenant identification or context
- Anonymous PII data (if enabled)

**They do NOT see**: Which tenant made the request, conversational history, or any stored data. All context remains in the tenant's LiteLLM proxy and database.
:::

::: details Q: Can a tenant use self-hosted models exclusively?

**A**: Yes. For air-gapped or fully on-premise deployments, you can:
1. Deploy self-hosted LLMs (vLLM, llama.cpp, HF-TEI)
2. Configure LiteLLM to route to local models
3. No outbound internet connectivity required
:::

::: details Q: How are costs tracked per tenant?

**A**: LiteLLM tracks API usage per tenant and user:
- Token counts (input/output)
- Model usage (GPT-4, Gemini, etc.)
- Cost calculations (based on model pricing)
- Monthly budget enforcement

Data is available in the LiteLLM admin UI and exportable for billing.
:::

::: details Q: Can tenants have different LLM access?

**A**: Yes. LiteLLM configuration allows per-tenant model access:
- Tenant A: Only GPT-4o (strict compliance)
- Tenant B: GPT-4o + Gemini 2.0 (flexibility)
- Tenant C: Self-hosted models only (air-gapped)

:::

::: details Q: What happens if the LLM proxy is unavailable?

**A**: Tenant instances will experience LLM-dependent feature degradation:
- ❌ RAG agents cannot generate responses
- ❌ Embeddings cannot be created for new documents
- ✅ Existing data and UI remain accessible
- ✅ Non-LLM features (document upload, RBAC, observability) continue working

**Mitigation**: Deploy LiteLLM with high availability (multiple replicas, load balancing).
:::

::: details Q: How do you manage updates across many tenant instances?

**A**: See [Updates and Maintenance](../6_updates_and_maintenance/) for detailed strategies:
- Phased rollouts (pilot → production)
- Blue-green deployments
- Automated update orchestration (Ansible, Kubernetes operators)
- Per-tenant update schedules

:::

## Related Documentation

- **Architecture**: [Core Components](../../2_architecture/1_core_components/) - Understand the AI-Hub architecture
- **Security**: [Authentication & Authorization](../../11_access_management/1_authentication_setup/) - Configure tenant authentication
- **Operations**: [Monitoring and Alerting](../5_monitoring_and_alerting/) - Observability for multi-instance deployments
- **Compliance**: [Swiss Data Protection](../../19_compliance/3_dsg/) - revDSG compliance for public sector