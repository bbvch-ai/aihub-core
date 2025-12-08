---
title: One-Command Deployment
---

# One-Command Deployment: Launch Your AI Platform

The Swiss AI Hub platform deploys with a single Docker Compose command. This streamlined process gets your complete AI
infrastructure running in minutes, not hours.

## Deployment Overview

::: tip Two Deployment Options
The Swiss AI Hub supports two deployment modes. Follow the same steps for both, using the appropriate commands for your
deployment type:

- **Production Deployment**: Deploy to a server with a real domain name (e.g., `aihub.yourcompany.com`)

  - Uses `docker-compose.latest.yml`
  - Uses Let's Encrypt for automatic SSL certificates
  - Requires DNS configuration pointing to your server

- **Local Deployment**: Run on your local machine for development/testing

  - Uses `docker-compose.local.yml`
  - Uses self-signed SSL certificates (mkcert)
  - Uses `127.0.0.1.nip.io` domain (automatically resolves to localhost)

Each step below shows commands for both deployment types. Simply follow the commands that match your chosen deployment
mode.
:::

---

## Step 1: Get Deployment Files

**For Production:**

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the production deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml

# Download the configs directory
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"
```

**For Local Deployment:**

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the local deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.local.yml

# Download the configs directory
curl -L https://github.com/bbvch-ai/aihub-core/tarball/main | tar -xz --strip=2 "*/configs"

# Generate SSL certificates with mkcert
mkcert -install  # Install local CA (only needed once)
mkcert -key-file configs/traefik/certs/dev-key.pem -cert-file configs/traefik/certs/dev-cert.pem \
  "localhost" "*.localhost" \
  "127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
```

::: tip What is nip.io?
The `*.127.0.0.1.nip.io` domain automatically resolves to your localhost (127.0.0.1), providing wildcard DNS resolution
without needing to modify your hosts file. This allows subdomain-based routing in local development.
:::

---

## Step 2: Configure Environment Variables

### Create Environment Configuration

Create a `.env` file with your configuration settings:

```bash
touch .env
```

### Essential Configuration Template

Copy this template into your `.env` file and replace placeholder values:

```env
# =============================================================================
# AI-Hub Production Environment Configuration
# =============================================================================
# This file contains ONLY the environment variables that must be configured.
# All internal Docker network endpoints are hardcoded in the compose files.
# =============================================================================

# -----------------------------------------------------------------------------
# General Settings
# -----------------------------------------------------------------------------
LOG_LEVEL="INFO"
ENV="prod"
DOMAIN="REPLACE_WITH_YOUR_DOMAIN"

# Let's Encrypt / Traefik
ACME_EMAIL="admin@your-company.com"
ADMIN_PASSWORD_HASH=""

# -----------------------------------------------------------------------------
# API Keys (External Services) - Configure at least one LLM provider
# -----------------------------------------------------------------------------
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
GEMINI_API_KEY=""
JINA_API_KEY=""
HUGGINGFACE_API_KEY=""

# Optional providers
SWISS_LLM_CLOUD_API_URL=""
SWISS_LLM_CLOUD_API_KEY=""
COHERE_API_BASE=""
COHERE_API_KEY=""

# -----------------------------------------------------------------------------
# OAuth2 / OIDC Configuration (REQUIRED)
# -----------------------------------------------------------------------------
AUTH_IDENTITY_PROVIDER="azure"
OAUTH_PROVIDER_NAME="Azure AD"
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_16_HEX_CHARS"

# Azure-specific OAuth (same values as above)
AZURE_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
AZURE_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
AZURE_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"

# OAuth Custom Branding (optional)
OAUTH_CUSTOM_SIGN_IN_LOGO=""

# -----------------------------------------------------------------------------
# Authentication & Security (REQUIRED - Generate new secrets!)
# -----------------------------------------------------------------------------
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# Superuser Configuration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Database Credentials (REQUIRED - Use strong passwords!)
# -----------------------------------------------------------------------------
# PostgreSQL 
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# MongoDB (FerretDB) 
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# S3 Storage (SeaweedFS) 
S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="REPLACE_WITH_RANDOM_STRING"
# Public endpoint for presigned URLs (auto-configured as https://s3.${DOMAIN} in docker-compose)
# S3_STORAGE_PUBLIC_ENDPOINT is set automatically - only override if using a custom S3 domain

# -----------------------------------------------------------------------------
# LiteLLM Configuration (REQUIRED)
# -----------------------------------------------------------------------------
LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"

# -----------------------------------------------------------------------------
# Service Configuration
# -----------------------------------------------------------------------------
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"

# Docling Configuration
DOCLING_API_TIMEOUT="600"
DOCLING_VLM_MODEL_NAME="text-generation/ocr"

# Milvus Configuration (must match your embedding model dimensions)
MILVUS_DIMENSION="3072"

# -----------------------------------------------------------------------------
# AI-Hub Application Settings
# -----------------------------------------------------------------------------
AIHUB_API_VERSION="latest"
AIHUB_CREATE_DEFAULT_ROLES="True"

# Admin Settings
ADMIN_EMAIL="admin@your-company.com"

# OAuth Group Restrictions (Azure AD group names)
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubAdmin"

# -----------------------------------------------------------------------------
# OpenTelemetry Configuration (Optional)
# -----------------------------------------------------------------------------
OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_RESOURCE_SERVICE_VERSION="1.0.0"
OTEL_RESOURCE_SERVICE_NAMESPACE="swiss-ai-hub"

# Cloud OTEL (optional - for external observability platforms)
OTEL_CLOUD_ENDPOINT="placeholder:1234"
OTEL_CLOUD_HEADERS=""
```

### Configuration Guidelines

**Critical Values to Replace:**

1. **Domain** - Set `DOMAIN` to your production domain (e.g., `aihub.yourcompany.com`) or `127.0.0.1.nip.io` for local
   testing

2. **Authentication Values** (from Prerequisites):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Your Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Your Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Your Azure Tenant ID

3. **AI Model Access** (configure at least one):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Your Azure OpenAI endpoint URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Your Azure OpenAI API key

4. **Secrets** (generate unique values for each):

   - Replace all `REPLACE_WITH_RANDOM_STRING` with: `openssl rand -hex 32`
   - Replace `REPLACE_WITH_16_HEX_CHARS` with: `openssl rand -hex 16`

::: info Simplified Configuration
Internal service endpoints (like database URLs, message queues, etc.) are now hardcoded in the Docker Compose files. You
only need to configure credentials and external service connections.
:::

::: tip Generate Random Strings
Use these commands to generate secure random strings:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For OAUTH_COOKIE_SECRET (32 characters)
openssl rand -hex 16
```

Run the appropriate command for each placeholder.
:::

### Environment Validation

Before deployment, verify your configuration:

```bash
# Check for placeholder values that need replacement
grep -n "REPLACE_WITH" .env
```

This should return no results if all placeholders are replaced.

## Step 3: Deploy the Platform

### Launch All Services

Deploy the complete platform with one command:

```bash
docker compose -f docker-compose.latest.yml up -d
```

This command will:

- Download all necessary Docker images
- Create required networks and volumes
- Start all platform services in the correct order
- Configure service discovery and communication

### Monitor Deployment Progress

Watch the deployment progress:

```bash
# See all services starting
docker compose -f docker-compose.latest.yml logs -f

# Check service health status
docker compose -f docker-compose.latest.yml ps
```

**Expected Services:** The platform includes these core services:

- **Web Interface** (aihub-web)
- **API** (aihub-api)
- **Authentication** (auth services)
- **Databases** (FerretDB, PostgreSQL, Valkey)
- **Vector Database** (Milvus)
- **LLM Proxy** (LiteLLM)
- **Document Processing** (Docling)
- **Observability** (Phoenix)
- **Message Queue** (NATS)
- **Storage** (SeaweedFS)

### Wait for Service Initialization

Initial startup takes 3-5 minutes while services initialize. All services should show "healthy" status:

```bash
# Wait for healthy status
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"
```

## Step 4: Verify Successful Deployment

### Access the Platform

1. **Make sure your User that you test with have the role "AIHubAdmin" assigned in the Azure Enterprise Application**

2. **Web Interface:**

   - Local: `https://127.0.0.1.nip.io`
   - Production: `https://your-domain.com`

3. **Expected Login Flow:**

   - Redirects to Azure authentication
   - After login, returns to AI-Hub interface
   - Should see the main dashboard

## Summary: Key Differences Between Deployments

| Feature                 | Production (`docker-compose.latest.yml`) | Local (`docker-compose.local.yml`) |
| ----------------------- | ---------------------------------------- | ---------------------------------- |
| **SSL Certificates**    | Let's Encrypt (automatic)                | mkcert (manual generation)         |
| **Domain**              | Your production domain                   | `127.0.0.1.nip.io`                 |
| **Configuration Files** | `*.latest.*` configs                     | `*.local.*` configs                |
| **Purpose**             | Production deployments                   | Local deployment and development   |

::: warning
Never use self-signed SSL certificates in production. The local deployment configuration is designed exclusively for
development and testing on your local machine.
:::