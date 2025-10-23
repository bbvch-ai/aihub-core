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

## Deployment Models

### Model 1: Fully Isolated Instances (Recommended for Production)

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

**Use Cases**:
- Swiss municipalities (Stadt Zug, Stadt Zürich, Geneva)
- Canton governments (Kanton Zug, Kanton Bern)
- Federal agencies requiring strict data separation
- Regulated industries (healthcare, finance, legal)

**Advantages**:
- ✅ Maximum data isolation and sovereignty
- ✅ Independent scaling and resource allocation
- ✅ Custom configurations per tenant
- ✅ Flexible update schedules
- ✅ Clear compliance boundaries

**Considerations**:
- ⚠️ Higher infrastructure cost (one stack per tenant)
- ⚠️ More operational overhead (managing multiple instances)
- ⚠️ Requires orchestration for updates across instances

---

### Model 2: Development and Testing Environment

**Architecture**: Single-instance deployment for local development, testing, and demonstrations.

**Purpose**:
- Local development on developer workstations
- CI/CD testing environments
- Proof-of-concept and demonstration setups
- Integration testing before production deployment

**Key Differences from Production**:
- All services run in a single Docker Compose stack
- Reduced resource requirements (CPU, memory, storage)
- Simplified networking (localhost or `.nip.io` domains)
- Optional GPU support for local model testing
- Mock authentication for development workflows

**Deployment Command**:
```bash
# Local development with SSL and domain routing
docker compose -f docker-compose.local.yml up -d

# For GPU-enabled development
docker compose -f docker-compose-gpu.dev.yml up -d
```

---

## Hosting Options

The AI-Hub supports flexible hosting to meet organizational requirements and constraints.

### Option 1: Swiss Cloud Hosting (Recommended)

**Description**: Deploy each tenant instance in a Swiss-based cloud provider with full data residency guarantees.

**Supported Providers**:
- **Azure Switzerland**: Azure AI Search, Azure OpenAI, ADLS, Azure Kubernetes Service
- **Swiss cloud providers**: Exoscale, Cloudscale, SwissCloud
- **Hybrid**: Azure AI services + Swiss cloud infrastructure

**Benefits**:
- ✅ Data remains in Switzerland (Geneva, Zurich data centers)
- ✅ Swiss legal jurisdiction
- ✅ Scalable infrastructure (Kubernetes, managed databases)
- ✅ Enterprise-grade security and compliance certifications
- ✅ Simplified disaster recovery and high availability

**Network Requirements**:
- Internet connectivity for LLM proxy access (HTTPS)
- Optional VPN for administrative access
- Private networking between tenant services (internal DNS)

**Typical Architecture**:
```
Azure Switzerland (Tenant: Stadt Zug)
├── Azure Kubernetes Service (AKS)
│   ├── AI-Hub application services
│   ├── Agents, pipelines, API, web
│   └── Observability stack
│
├── Managed Services
│   ├── Azure Database for PostgreSQL (FerretDB backend)
│   ├── Azure AI Search (vector store)
│   └── Azure Data Lake Storage (documents)
│
└── Networking
    ├── Private VNet (tenant-isolated)
    ├── Azure Front Door (reverse proxy + WAF)
    └── VPN Gateway (admin access)

Connection to Shared LLM Layer
└── HTTPS API calls to centralized LiteLLM proxy
```

---

### Option 2: On-Premise Hosting

**Description**: Deploy tenant instances entirely within the organization's own data center or server infrastructure.

**Requirements**:
- **Container Orchestration**: Docker Compose, Kubernetes, or OpenShift
- **Database**: PostgreSQL 15+ (recommended), MSSQL, or Oracle
- **Compute**: Modern x86_64 servers with sufficient CPU, RAM, storage
- **Optional GPU**: NVIDIA GPUs for self-hosted LLM inference
- **Network**: Outbound HTTPS for shared LLM access (or fully air-gapped with local models)

**Benefits**:
- ✅ Complete infrastructure control
- ✅ No cloud dependencies
- ✅ Existing data center infrastructure reuse
- ✅ Compatible with air-gapped environments (with self-hosted LLMs)

**Considerations**:
- ⚠️ Requires in-house Kubernetes/Docker expertise
- ⚠️ Manual infrastructure management (backups, updates, scaling)
- ⚠️ Higher operational complexity
- ⚠️ Outbound connectivity required for cloud-based LLMs (unless self-hosted)

**Typical Architecture**:
```
On-Premise Data Center (Tenant: Kanton Bern)
├── Kubernetes Cluster (or Docker Compose)
│   ├── AI-Hub application pods/containers
│   ├── Agent, pipeline, API, web services
│   └── Observability stack
│
├── Database Cluster
│   ├── PostgreSQL HA (Patroni/Stolon)
│   └── FerretDB (MongoDB compatibility layer)
│
├── Vector Store
│   ├── Milvus cluster
│   └── Persistent volume storage
│
└── Storage Infrastructure
    ├── SeaweedFS (S3-compatible object storage)
    └── NFS/CIFS for shared volumes

Network Connectivity
├── Internal: Private network (10.x.x.x, 172.x.x.x)
├── Outbound: Firewall rules for HTTPS to LiteLLM proxy
└── Admin Access: VPN or bastion host
```

---

### Option 3: Hybrid Deployment

**Description**: Tenant instance on-premise or Swiss cloud, with centralized LLM infrastructure in a separate cloud region.

**Example Scenarios**:
- **Tenant instance**: Azure Switzerland
- **Shared LLM**: Azure OpenAI in EU regions (with data residency agreements)

**Benefits**:
- ✅ Flexibility in infrastructure placement
- ✅ Cost optimization for LLM hosting
- ✅ Performance optimization (LLM proximity to users vs. data sovereignty)

**Compliance Notes**:
- Ensure LLM provider has data processing agreements (DPA)
- Validate GDPR/revDSG compliance for LLM API usage
- Use anonymization (Presidio) if required

---

## Environment Types

The AI-Hub provides pre-configured Docker Compose files for different deployment scenarios:

### 1. Local Development (`docker-compose.local.yml`)

**Purpose**: Local development on developer workstations with SSL and domain routing.

**Features**:
- Self-signed SSL certificates via mkcert
- Domain-based routing (`.nip.io` or `.localhost`)
- Traefik reverse proxy with SSL termination
- Minimal resource requirements
- Fast startup and teardown

**Usage**:
```bash
# Generate local SSL certificates
make local-cert

# Start the local stack
docker compose -f docker-compose.local.yml up -d

# Access points
# https://127.0.0.1.nip.io (main web interface)
# https://openwebui.127.0.0.1.nip.io (OpenWebUI)
# https://dagster.127.0.0.1.nip.io (Dagster)
```

---

### 2. Nightly/Testing (`docker-compose.nightly.yml`)

**Purpose**: Automated testing in CI/CD pipelines with the latest development builds.

**Features**:
- Uses `nightly` tagged images (built from `main` branch)
- Suitable for integration testing
- Ephemeral data (no persistent volumes in CI)

**Usage**:
```bash
docker compose -f docker-compose.nightly.yml up -d
```

---

### 3. Production (`docker-compose.latest.yml`)

**Purpose**: Stable production deployments with tagged releases.

**Features**:
- Uses `latest` or versioned images (e.g., `v1.2.3`)
- Production-grade configurations
- Persistent volumes for all data
- Let's Encrypt SSL certificates
- Health checks and restart policies

**Usage**:
```bash
# Production deployment
docker compose -f docker-compose.latest.yml up -d
```

---

### 4. GPU-Enabled Deployments

**Purpose**: Environments requiring GPU acceleration for self-hosted LLM inference.

**Variants**:
- `docker-compose-gpu.dev.yml`: Development with GPU support
- `docker-compose-gpu.latest.yml`: Production with GPU support

**Requirements**:
- NVIDIA GPU with CUDA support
- Docker with NVIDIA Container Runtime
- Sufficient GPU memory (16GB+ recommended for 7B models)

**Usage**:
```bash
# GPU-enabled development
docker compose -f docker-compose-gpu.dev.yml up -d
```

---

## Deployment Decision Matrix

| Use Case | Deployment Model | Hosting Option | Environment Type | Key Benefits |
|----------|------------------|----------------|------------------|--------------|
| **Production (Municipal)** | Fully Isolated Instances | Swiss Cloud (Azure CH) | `docker-compose.latest.yml` | Complete data sovereignty, compliance, scalability |
| **Production (Canton)** | Fully Isolated Instances | On-Premise (Kubernetes) | `docker-compose.latest.yml` | Infrastructure control, air-gapped option |
| **Pilot/Demo** | Fully Isolated Instances | Swiss Cloud (Managed) | `docker-compose.latest.yml` | Fast provisioning, low initial cost |
| **Development** | Single Instance | Local Workstation | `docker-compose.local.yml` | Fast iteration, SSL support, easy debugging |
| **CI/CD Testing** | Single Instance | GitHub Actions | `docker-compose.nightly.yml` | Automated testing, latest builds |
| **Self-Hosted LLM** | Fully Isolated Instances | On-Premise (GPU) | `docker-compose-gpu.latest.yml` | No cloud LLM dependency, data never leaves premises |

---

## Architecture Diagrams

### Multi-Instance Deployment with Shared LLM Backend

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Shared LLM Backend Resources                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Cloud LLM APIs                    Self-Hosted Models         │ │
│  │  ┌─────────────────┐              ┌─────────────────┐        │ │
│  │  │ Azure OpenAI    │              │ vLLM (GPU)      │        │ │
│  │  │ (Shared creds)  │              │ llama.cpp       │        │ │
│  │  └─────────────────┘              │ Ollama          │        │ │
│  │  ┌─────────────────┐              └─────────────────┘        │ │
│  │  │ Google Gemini   │                                          │ │
│  │  │ (Shared API key)│                                          │ │
│  │  └─────────────────┘                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
└────────────▲──────────────────▲──────────────────▲─────────────────┘
             │                  │                  │
     HTTPS API Calls    HTTPS API Calls    HTTPS API Calls
             │                  │                  │
┌────────────┴────────┐  ┌──────┴──────────┐  ┌───┴─────────────────┐
│  Tenant: Zug        │  │  Tenant: Zürich │  │  Tenant: Geneva     │
│  (Isolated Stack)   │  │  (Isolated Stack│  │  (Isolated Stack)   │
├─────────────────────┤  ├─────────────────┤  ├─────────────────────┤
│ ┌─────────────────┐ │  │ ┌─────────────┐ │  │ ┌─────────────────┐ │
│ │ LiteLLM Proxy   │ │  │ │ LiteLLM     │ │  │ │ LiteLLM Proxy   │ │
│ │ (Zug instance)  │ │  │ │ (ZH inst.)  │ │  │ │ (Geneva inst.)  │ │
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
     Zug Users               Zürich Users            Geneva Users
```

**Key Points**:
- Each tenant has their **own LiteLLM proxy instance** (independent cost tracking, versioning, configuration)
- All tenant LiteLLM proxies connect to **shared LLM backend resources** (Azure OpenAI subscriptions, self-hosted models)
- **Complete data isolation**: Prompts, responses, and user data stay within tenant boundaries
- **Cost efficiency**: Shared expensive LLM API subscriptions and GPU infrastructure

---

## Configuration Management

### Per-Tenant Configuration

Each tenant instance is configured via environment variables (`.env` file) that define:

**Tenant Identity**:
```bash
# Tenant-specific domain
DOMAIN=ai-hub.stadt-zug.ch

# Tenant-specific branding
TENANT_NAME="Stadt Zug"
TENANT_LOGO_URL="https://..."
```

**Authentication**:
```bash
# Connect to tenant's Azure AD
OAUTH_CLIENT_ID="..."
OAUTH_CLIENT_SECRET="..."
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/{tenant-id}"
```

**LLM Configuration**:
```bash
# Tenant-specific LiteLLM proxy (part of tenant instance)
# Connects to shared LLM backends (Azure OpenAI, Gemini, self-hosted)
AZURE_OPENAI_KEY="<shared-azure-subscription-key>"
GEMINI_API_KEY="<shared-gemini-api-key>"
VLLM_ENDPOINT="https://vllm.shared-infrastructure.ch/v1"
```

**Data Storage**:
```bash
# Tenant-specific database credentials
MONGO_USERNAME="tenant_zug"
MONGO_PASSWORD="..."
POSTGRES_USER="tenant_zug"
POSTGRES_PASSWORD="..."

# Tenant-specific vector store
AZURE_AI_SEARCH_ENDPOINT="https://search-zug.search.windows.net"
```

### Per-Tenant LiteLLM Configuration

Each tenant configures their own LiteLLM proxy through `configs/litellm/config.yaml` within their instance:

**`configs/litellm/config.yaml` (Per-Tenant)**:
```yaml
model_list:
  # Azure OpenAI using shared subscription
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_key: os.environ/AZURE_OPENAI_KEY  # Shared Azure subscription

  # Google Gemini using shared API key
  - model_name: gemini-2.0-flash
    litellm_params:
      model: gemini/gemini-2.0-flash-001
      api_key: os.environ/GEMINI_API_KEY  # Shared Gemini key

  # Self-hosted vLLM (shared infrastructure)
  - model_name: llama-3-70b
    litellm_params:
      model: openai/llama-3-70b-instruct
      api_base: https://vllm.shared-infrastructure.ch/v1

general_settings:
  master_key: ${LITELLM_MASTER_KEY}  # Tenant-specific master key
  database_url: "postgresql://..."   # Tenant-specific database

  # Tenant-specific budget controls
  max_budget: 1000.00  # USD per month
  budget_duration: "monthly"
```

**Key Configuration Points**:
- Each tenant's LiteLLM uses **shared LLM backend credentials** (Azure, Gemini, vLLM)
- Each tenant sets their **own budget limits** and rate limiting
- Each tenant tracks **their own costs** independently
- Tenants can use **different LiteLLM versions** (updated independently)

---

## Tenant Provisioning Workflow

### Step 1: Prepare Infrastructure

**For Swiss Cloud**:
1. Create Azure resource group or Kubernetes namespace
2. Provision managed services (database, storage, AI search)
3. Configure networking (VNet, DNS, firewall rules)

**For On-Premise**:
1. Allocate compute resources (VMs, K8s nodes)
2. Provision storage volumes
3. Configure network connectivity

### Step 2: Configure Tenant Instance

1. Clone the AI-Hub repository:
   ```bash
   git clone https://github.com/bbvch-ai/aihub-core
   cd aihub-core
   ```

2. Create tenant-specific `.env` file:
   ```bash
   cp .env.example .env.tenant-zug
   # Edit with tenant-specific values
   ```

3. Generate SSL certificates (if on-premise):
   ```bash
   # Let's Encrypt for production
   # or self-signed for testing
   ```

### Step 3: Deploy Tenant Instance

```bash
# Load tenant configuration
export $(cat .env.tenant-zug | xargs)

# Deploy the stack
docker compose -f docker-compose.latest.yml up -d

# Verify health
docker compose ps
```

### Step 4: Configure Tenant Settings

1. Access the admin interface: `https://{DOMAIN}/admin`
2. Configure:
   - Default knowledge bases
   - Agent permissions
   - RBAC roles
   - Data retention policies

### Step 5: User Onboarding

1. Configure OIDC/SAML integration with tenant's IdP
2. Assign roles to users (admin, data steward, end user)
3. Conduct user training and provide documentation

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

- **TLS 1.3**: All communication encrypted (tenant ↔ LLM proxy)
- **Certificate Management**: Let's Encrypt for production, mkcert for development
- **API Authentication**: Bearer tokens (OAuth 2.0, JWT)

### Data at Rest

- **Database Encryption**: PostgreSQL with transparent data encryption (TDE)
- **Volume Encryption**: Encrypted persistent volumes (LUKS, Azure Disk Encryption)
- **Secret Management**: Environment variables, Azure Key Vault, Kubernetes Secrets

---

## Next Steps

- [Production Configuration](../2_production_configuration/) - Detailed configuration guide for production deployments
- [Scaling Considerations](../3_scaling_considerations/) - How to scale tenant instances
- [Backup and Recovery](../4_backup_and_recovery/) - Backup strategies for per-tenant architecture
- [Updates and Maintenance](../6_updates_and_maintenance/) - Managing updates across multiple instances

---

## FAQ

### Q: Can tenants share agents or pipelines?

**A**: No. Each tenant instance has its own isolated set of agents and pipelines. However, the same agent *definitions* (code) can be deployed across multiple tenant instances. Customizations are tenant-specific.

### Q: What data does the shared LLM backend see?

**A**: Each tenant has their own LiteLLM proxy, so prompts/responses stay within the tenant instance. The shared LLM backends (Azure OpenAI, Gemini, self-hosted models) see:
- API requests from multiple tenant LiteLLM proxies (stateless, not persisted)
- Model inference requests (prompts and completions in transit only)
- No tenant identification or context

**They do NOT see**: Which tenant made the request, conversational history, or any stored data. All context remains in the tenant's LiteLLM proxy and database.

### Q: Can a tenant use self-hosted models exclusively?

**A**: Yes. For air-gapped or fully on-premise deployments, you can:
1. Deploy self-hosted LLMs (vLLM, llama.cpp, Ollama)
2. Configure LiteLLM to route to local models
3. No outbound internet connectivity required

### Q: How are costs tracked per tenant?

**A**: LiteLLM tracks API usage per tenant key:
- Token counts (input/output)
- Model usage (GPT-4, Gemini, etc.)
- Cost calculations (based on model pricing)
- Monthly budget enforcement

Data is available in the LiteLLM admin UI and exportable for billing.

### Q: Can tenants have different LLM access?

**A**: Yes. LiteLLM configuration allows per-tenant model access:
- Tenant A: Only GPT-4o (strict compliance)
- Tenant B: GPT-4o + Gemini 2.0 (flexibility)
- Tenant C: Self-hosted models only (air-gapped)

### Q: What happens if the LLM proxy is unavailable?

**A**: Tenant instances will experience LLM-dependent feature degradation:
- ❌ RAG agents cannot generate responses
- ❌ Embeddings cannot be created for new documents
- ✅ Existing data and UI remain accessible
- ✅ Non-LLM features (document upload, RBAC, observability) continue working

**Mitigation**: Deploy LiteLLM with high availability (multiple replicas, load balancing).

### Q: How do you manage updates across many tenant instances?

**A**: See [Updates and Maintenance](../6_updates_and_maintenance/) for detailed strategies:
- Phased rollouts (pilot → production)
- Blue-green deployments
- Automated update orchestration (Ansible, Kubernetes operators)
- Per-tenant update schedules

---

## Related Documentation

- **Architecture**: [Core Components](../../2_architecture/1_core_components/) - Understand the AI-Hub architecture
- **Security**: [Authentication & Authorization](../../11_access_management/1_authentication_setup/) - Configure tenant authentication
- **Operations**: [Monitoring and Alerting](../5_monitoring_and_alerting/) - Observability for multi-instance deployments
- **Compliance**: [Swiss Data Protection](../../13_compliance/2_swiss_dsg/) - revDSG compliance for public sector