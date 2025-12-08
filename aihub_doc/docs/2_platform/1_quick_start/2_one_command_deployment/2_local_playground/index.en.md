---
title: "Local Playground"
description: "Quick setup guide for trying out the Swiss AI Hub on your local machine"
---

# Local Playground

This guide walks you through setting up a complete Swiss AI Hub installation on your local machine. Perfect for evaluation, demos, and testingeverything runs in Docker with a single command, using pre-built images and self-signed SSL certificates.

## What is Local Playground Mode?

Local Playground mode deploys the complete Swiss AI Hub stack on your local machine using Docker Compose with pre-built images. Unlike the Development Setup (which runs services locally for code changes), this mode runs everything in containersideal for trying out the platform without modifying code.

### Key Features

- **Complete Platform**: All services (API, web, agents, pipelines, infrastructure) run in Docker
- **Local Domain**: Uses `127.0.0.1.nip.io` wildcard DNS (no /etc/hosts editing needed)
- **Self-Signed SSL**: HTTPS enabled via mkcert (browsers trust the certificates)
- **Pre-Built Images**: Downloads images from the registry (no local builds)
- **Quick Setup**: From zero to running in 15-30 minutes

### When to Use Local Playground

- **Evaluating** the platform for your organization
- **Demonstrating** AI Hub capabilities to stakeholders
- **Testing** features before production deployment
- **Learning** the platform architecture and components

### When NOT to Use Local Playground

- **Active Development**: Use Development Setup instead (enables hot-reload, debugging)
- **Production**: Use Production Deployment (real domain, automatic SSL, hardened security)

## Prerequisites

### Hardware Requirements

::: code-group

```txt [CPU Variant]
- 16 GB RAM minimum (32 GB recommended)
- 50 GB free disk space
- External LLM API access (Azure OpenAI, Google Gemini, etc.)
```

```txt [GPU Variant]
- 32 GB RAM minimum (64 GB recommended)
- 100 GB free disk space
- NVIDIA GPU with 16+ GB VRAM (RTX 3090, RTX 4090, A100, etc.)
- NVIDIA drivers installed (version 525+)
- NVIDIA Container Toolkit installed
```

:::

### Software Requirements

- **Docker** (v24+) and **Docker Compose** (v2.20+)
  - Installation: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
- **Git** for cloning the repository
  - Installation: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **mkcert** for self-signed SSL certificates (will install in Step 3)

### External Services

- **Azure AD / Entra ID** application registration
  - Required for user authentication
  - See [Azure AD Setup Guide](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)

- **LLM Provider API** (CPU variant only)
  - Azure OpenAI (recommended)
  - Google Gemini (alternative)
  - API keys and endpoint URLs

::: info GPU Variant
The GPU variant includes self-hosted AI models (llama.cpp, vLLM), so external LLM API access is optional.
:::

::: tip Quick Start Tip
If you already have Docker and Azure AD configured, you can get the platform running in under 15 minutes!
:::

### Time Estimate

- **With prerequisites ready**: ~15 minutes
- **First-time setup**: ~30 minutes (includes Azure AD setup, mkcert install)

## Step 1: Clone the Repository

Clone the AI Hub repository to your local machine:

```bash
git clone https://github.com/bbvch-ai/aihub-core.git
cd aihub-core
```

## Step 2: Configure Environment Variables

Create a `.env` file in the repository root with your configuration settings.

### Generate the .env File

Start by copying the development template:

```bash
cp .env.dev .env
```

### Essential Configuration

Edit the `.env` file and update these critical values:

::: code-group

```env [CPU Variant - Azure OpenAI]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="INFO"
ENV="local"
DOMAIN="127.0.0.1.nip.io"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"
OAUTH_CLIENT_SECRET="your-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="$(openssl rand -hex 16)"

# Redirect URI to configure in Azure AD:
# https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
# https://admin.127.0.0.1.nip.io/oauth2/callback

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="$(openssl rand -hex 32)"

# =============================================================================
# SUPERUSER CONFIGURATION (OPTIONAL - for development/testing)
# =============================================================================

SUPERUSER_ENABLED="True"
SUPERUSER_NAME="Admin"
SUPERUSER_EMAIL="admin@localhost"
SUPERUSER_OID="$(openssl rand -hex 16)"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="$(openssl rand -hex 32)"

# =============================================================================
# AI MODEL ACCESS
# =============================================================================

# Azure OpenAI
AZURE_OPENAI_BASE_URL="https://your-instance.openai.azure.com"
AZURE_OPENAI_KEY="your-azure-openai-key"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="$(openssl rand -hex 16)"

MONGO_USERNAME="admin"
MONGO_PASSWORD="$(openssl rand -hex 16)"
# Note: Update connection string with same password
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@mongodb:27017/"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="$(openssl rand -hex 16)"
S3_STORAGE_URL_SIGNING_SECRET="$(openssl rand -hex 32)"

# Internal endpoint (Docker network)
S3_STORAGE_ENDPOINT="http://seaweedfs-s3:9000"

# Public endpoint (browser access) - matches DOMAIN
S3_STORAGE_PUBLIC_ENDPOINT="https://s3.127.0.0.1.nip.io"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="$(openssl rand -hex 16)"
LITELLM_MASTER_KEY="$(openssl rand -hex 32)"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="$(openssl rand -hex 16)"
PHOENIX_SECRET="$(openssl rand -hex 16)"
NATS_TOKEN="$(openssl rand -hex 16)"
MILVUS_DIMENSION="3072"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# OBSERVABILITY
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search functionality
```

```env [CPU Variant - Google Gemini]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="INFO"
ENV="local"
DOMAIN="127.0.0.1.nip.io"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"
OAUTH_CLIENT_SECRET="your-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="$(openssl rand -hex 16)"

# Redirect URI to configure in Azure AD:
# https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
# https://admin.127.0.0.1.nip.io/oauth2/callback

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="$(openssl rand -hex 32)"

# =============================================================================
# SUPERUSER CONFIGURATION (OPTIONAL - for development/testing)
# =============================================================================

SUPERUSER_ENABLED="True"
SUPERUSER_NAME="Admin"
SUPERUSER_EMAIL="admin@localhost"
SUPERUSER_OID="$(openssl rand -hex 16)"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="$(openssl rand -hex 32)"

# =============================================================================
# AI MODEL ACCESS
# =============================================================================

# Google Gemini
GEMINI_API_KEY="your-gemini-api-key"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="$(openssl rand -hex 16)"

MONGO_USERNAME="admin"
MONGO_PASSWORD="$(openssl rand -hex 16)"
# Note: Update connection string with same password
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@mongodb:27017/"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="$(openssl rand -hex 16)"
S3_STORAGE_URL_SIGNING_SECRET="$(openssl rand -hex 32)"

# Internal endpoint (Docker network)
S3_STORAGE_ENDPOINT="http://seaweedfs-s3:9000"

# Public endpoint (browser access) - matches DOMAIN
S3_STORAGE_PUBLIC_ENDPOINT="https://s3.127.0.0.1.nip.io"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="$(openssl rand -hex 16)"
LITELLM_MASTER_KEY="$(openssl rand -hex 32)"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="$(openssl rand -hex 16)"
PHOENIX_SECRET="$(openssl rand -hex 16)"
NATS_TOKEN="$(openssl rand -hex 16)"
MILVUS_DIMENSION="3072"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# OBSERVABILITY
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search functionality
```

```env [GPU Variant]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="INFO"
ENV="local"
DOMAIN="127.0.0.1.nip.io"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"
OAUTH_CLIENT_SECRET="your-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="$(openssl rand -hex 16)"

# Redirect URI to configure in Azure AD:
# https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback
# https://admin.127.0.0.1.nip.io/oauth2/callback

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="$(openssl rand -hex 32)"

# =============================================================================
# SUPERUSER CONFIGURATION (OPTIONAL - for development/testing)
# =============================================================================

SUPERUSER_ENABLED="True"
SUPERUSER_NAME="Admin"
SUPERUSER_EMAIL="admin@localhost"
SUPERUSER_OID="$(openssl rand -hex 16)"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="$(openssl rand -hex 32)"

# =============================================================================
# AI MODEL ACCESS
# =============================================================================

# HuggingFace (required for GPU model downloads)
HUGGINGFACE_API_KEY="your-huggingface-token"

# Optional: External providers as fallback
AZURE_OPENAI_BASE_URL=""
AZURE_OPENAI_KEY=""
GEMINI_API_KEY=""

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="$(openssl rand -hex 16)"

MONGO_USERNAME="admin"
MONGO_PASSWORD="$(openssl rand -hex 16)"
# Note: Update connection string with same password
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@mongodb:27017/"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="$(openssl rand -hex 16)"
S3_STORAGE_URL_SIGNING_SECRET="$(openssl rand -hex 32)"

# Internal endpoint (Docker network)
S3_STORAGE_ENDPOINT="http://seaweedfs-s3:9000"

# Public endpoint (browser access) - matches DOMAIN
S3_STORAGE_PUBLIC_ENDPOINT="https://s3.127.0.0.1.nip.io"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="$(openssl rand -hex 16)"
LITELLM_MASTER_KEY="$(openssl rand -hex 32)"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="$(openssl rand -hex 16)"
PHOENIX_SECRET="$(openssl rand -hex 16)"
NATS_TOKEN="$(openssl rand -hex 16)"
MILVUS_DIMENSION="3072"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# OBSERVABILITY
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search functionality
```

:::

### Generate Random Secrets

The examples above show `$(openssl rand -hex 16)` or `$(openssl rand -hex 32)`. Generate actual secrets with these commands:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For shorter secrets like OAUTH_COOKIE_SECRET (32 characters)
openssl rand -hex 16
```

Replace each `$(openssl rand -hex XX)` placeholder with the generated value.

### Validate Configuration

Ensure all placeholders are replaced:

```bash
grep -n "your-\|XXX\|\$(openssl" .env
```

This should return no results if all values are configured.

### Configure Azure AD Redirect URIs

In your Azure AD app registration, add these redirect URIs:

- `https://openwebui.127.0.0.1.nip.io/oauth/oidc/callback`
- `https://admin.127.0.0.1.nip.io/oauth2/callback`
- `https://dagster.127.0.0.1.nip.io/oauth2/callback`

Save the app registration after adding the URIs.

## Step 3: Install mkcert

mkcert creates self-signed SSL certificates that your browser trusts. This enables HTTPS on localhost without certificate warnings.

### Install mkcert

::: code-group

```bash [Linux]
# Using Homebrew (if installed)
brew install mkcert

# Or using pre-built binary
curl -L https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64 -o mkcert
chmod +x mkcert
sudo mv mkcert /usr/local/bin/
```

```bash [macOS]
brew install mkcert
brew install nss  # For Firefox support
```

```bash [Windows (PowerShell)]
# Using Chocolatey
choco install mkcert

# Or download from releases:
# https://github.com/FiloSottile/mkcert/releases
```

:::

### Generate and Install Certificates

```bash
# Install the local certificate authority
mkcert -install

# Generate certificates for the platform
mkdir -p certs
cd certs

# Create wildcard certificate for 127.0.0.1.nip.io
mkcert "*.127.0.0.1.nip.io" 127.0.0.1 localhost

# Rename files for Traefik
mv _wildcard.127.0.0.1.nip.io+2.pem cert.pem
mv _wildcard.127.0.0.1.nip.io+2-key.pem key.pem

cd ..
```

### Verify Certificate Installation

Check that certificates were created:

```bash
ls -la certs/
# Should show: cert.pem and key.pem
```

## Step 4: Launch the Platform

Start all AI Hub services with Docker Compose:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml up -d
```

:::

### Monitor Startup Progress

Watch the services initialize:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml logs -f
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml logs -f
```

:::

**Initial Startup Time:**
- **CPU Variant**: 2-5 minutes
- **GPU Variant**: 15-30 minutes (downloads AI models on first start)

Press `Ctrl+C` to stop following logs. Services continue running in the background.

### Check Service Status

Verify all services are healthy:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml ps
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml ps
```

:::

Look for `healthy` or `running` status for all services.

## Step 5: Verify Deployment

Once services are running, access the platform through your browser:

### Primary Interfaces

| Service | URL | Description |
|---------|-----|-------------|
| **Open WebUI** | https://openwebui.127.0.0.1.nip.io | Chat interface (primary user entry point) |
| **Admin UI** | https://admin.127.0.0.1.nip.io | Platform administration and configuration |
| **API Docs** | https://api.127.0.0.1.nip.io/docs | Interactive API documentation (Swagger) |

### Observability & Tools

| Service | URL | Description |
|---------|-----|-------------|
| **Phoenix** | https://phoenix.127.0.0.1.nip.io | AI observability and tracing |
| **Dagster** | https://dagster.127.0.0.1.nip.io | Data pipeline orchestration |
| **SeaweedFS** | https://s3.127.0.0.1.nip.io | S3-compatible object storage browser |
| **Attu** | https://attu.127.0.0.1.nip.io | Milvus vector database UI |
| **LiteLLM** | https://litellm.127.0.0.1.nip.io | LLM proxy and cost tracking |

::: warning Certificate Warning
On first access, your browser may show a certificate warning. This is expected for self-signed certificates. Click "Advanced"  "Proceed to site" to continue.
:::

### Health Check

Verify the API is responding:

```bash
curl -k https://api.127.0.0.1.nip.io/health
```

Should return: `{"status":"healthy"}`

## Step 6: First Login

Navigate to https://openwebui.127.0.0.1.nip.io in your browser.

### Option 1: Azure AD Login (Recommended)

1. Click **"Sign in with Azure AD"**
2. Authenticate with your Azure credentials
3. Accept permissions if prompted
4. You'll be redirected back to Open WebUI

::: info User Roles
Your Azure AD user must be assigned a role in the Azure Enterprise Application. Default roles: `AIHubUser`, `AIHubAdmin`, `AIHubSuperuser`.
:::

### Option 2: Superuser Token (Development/Testing)

If `SUPERUSER_ENABLED=True` in your `.env`:

1. Navigate to https://openwebui.127.0.0.1.nip.io
2. Click **"Use Superuser Token"** (if available)
3. Enter the `SUPERUSER_TOKEN` from your `.env` file
4. Click **"Sign In"**

::: warning Production Warning
Disable superuser authentication in production deployments (`SUPERUSER_ENABLED=False`).
:::

## Common Operations

### View Logs

::: code-group

```bash [All Services (CPU)]
docker compose -f docker-compose.local.yml logs -f
```

```bash [All Services (GPU)]
docker compose -f docker-compose.local.gpu.yml logs -f
```

```bash [Specific Service (CPU)]
docker compose -f docker-compose.local.yml logs -f api
```

```bash [Specific Service (GPU)]
docker compose -f docker-compose.local.gpu.yml logs -f api
```

:::

### Stop the Platform

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml down
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml down
```

:::

### Restart a Service

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml restart api
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml restart api
```

:::

### Reset All Data

::: danger Data Loss Warning
This operation deletes all data permanently, including user accounts, knowledge bases, vector embeddings, and all file storage. There is no undo. Only proceed if you want to completely reset the platform.
:::

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml down -v
rm -rf .docker-volumes
docker compose -f docker-compose.local.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml down -v
rm -rf .docker-volumes
docker compose -f docker-compose.local.gpu.yml up -d
```

:::

### Update to Latest Images

Pull the latest pre-built images and restart:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.local.yml pull
docker compose -f docker-compose.local.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.local.gpu.yml pull
docker compose -f docker-compose.local.gpu.yml up -d
```

:::

## Next Steps

Now that your AI Hub is running:

1. **Create a Knowledge Base**: Upload documents and configure RAG pipelines
2. **Test Chat Interface**: Try conversational AI with your data
3. **Explore Admin UI**: Configure models, agents, and workflows
4. **Review Traces**: Use Phoenix to observe AI agent execution
5. **Try the API**: Explore interactive docs at https://api.127.0.0.1.nip.io/docs

### Learn More

- **User Documentation**: [Coming soon]
- **Architecture Overview**: [docs/2_platform/2_architecture](../../2_architecture/index.en.md)
- **Developer Guide**: For code contributions, see [Development Setup](../1_development_setup/index.en.md)
- **Production Deployment**: Ready to deploy for real users? See [Production Deployment](../3_production_deployment/index.en.md)
