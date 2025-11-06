---
title: One-Command Deployment
---

# One-Command Deployment: Launch Your AI Platform

The Swiss AI Hub platform deploys with a single Docker Compose command. This streamlined process gets your complete AI
infrastructure running in minutes, not hours.

## Deployment Overview

The deployment consists of three simple steps:

1. **Download** the deployment configuration
2. **Configure** environment variables with your settings
3. **Deploy** with one command

The entire platform runs as containerized services, automatically handling service discovery, networking, and startup
orchestration.

## Step 1: Download Deployment Files

### Get the Docker Compose Configuration

Download the latest deployment configuration:

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download the latest deployment configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml
```

Alternatively, navigate to the [aihub-core repository](https://github.com/bbvch-ai/aihub-core) and download
`docker-compose.latest.yml` manually.

### Verify Download

Check that you have the deployment file:

```bash
ls -la docker-compose.latest.yml
```

You should see the compose file in your deployment directory.

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
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="WARNING"                    # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="prod"                             # Options: dev, test, prod
DOMAIN="aihub.your-company.com"        # Domain for the platform (e.g., ai-hub.your-company.com)

# Traefik Configuration
ACME_EMAIL="admin@your-company.com"    # Replace with admin email
ADMIN_PASSWORD_HASH=""                 # Generate with: htpasswd -nb admin yourpassword

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# General Authentication Settings
AUTH_ENABLE_API_ACCESS="True"
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"
AUTH_IDENTITY_PROVIDER="azure"

# OAuth2 Configuration (from Prerequisites setup)
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_16_HEX_CHARS"

# =============================================================================
# PLATFORM ACCESS CONFIGURATION
# =============================================================================

# Superuser Configuration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Superuser"
SUPERUSER_EMAIL="admin@your-company.com"              # Replace with admin email
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING"

# Platform Settings
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://aihub.your-company.com" # Replace with your URL
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Recommended)
AZURE_OPENAI_BASE_URL="REPLACE_WITH_AZURE_OPENAI_BASE_URL"
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# =============================================================================
# LITELLM PROXY CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING"

# FerretDB (MongoDB-compatible)
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@ferretdb:27017/"

# Valkey (Redis-compatible)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# SeaweedFS S3 Storage
SEAWEEDFS_ROOT_USER="admin"
SEAWEEDFS_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING"
S3_STORAGE_ENDPOINT="http://seaweedfs:8333"
S3_STORAGE_ACCESS_KEY="admin"                         # Must match SEAWEEDFS_ROOT_USER
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_SEAWEEDFS_PASSWORD"
S3_STORAGE_URL_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING"

# =============================================================================
# SERVICE ENDPOINTS (Internal - Don't Change)
# =============================================================================

DOCLING_API_ENDPOINT="http://docling:5001"
DOCLING_API_TIMEOUT="600"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING"
MILVUS_DIMENSION="3072"

# =============================================================================
# BOT DEVELOPMENT CONFIGURATION
# =============================================================================

BOT_AUTH_FAKE_NAME="Bot"
BOT_AUTH_FAKE_EMAIL="bot@bot.com"
BOT_AUTH_FAKE_OID="00000000-0000-0000-0000-000000000000"
BOT_AUTH_FAKE_ROLES="AIHubBot"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Jina AI Search (Optional)
JINA_API_KEY=""

# Signoz Telemetry (Optional)
SIGNOZ_INGESTION_CLOUD_ENDPOINT=""
SIGNOZ_INGESTION_KEY=""

```

### Configuration Guidelines

**Critical Values to Replace:**

1. **Authentication Values** (from Prerequisites):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Your Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Your Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Your Azure Tenant ID (appears twice)

2. **AI Model Access** (configure at least one):

   - `REPLACE_WITH_AZURE_OPENAI_BASE_URL` → Your Azure OpenAI endpoint URL
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Your Azure OpenAI API key
   - `REPLACE_WITH_GEMINI_KEY` → Your Google Gemini API key

3. **Random Strings** (generate unique values):

   - Replace all `REPLACE_WITH_RANDOM_STRING` with unique random strings (use `openssl rand -hex 32`)
   - Replace `REPLACE_WITH_16_HEX_CHARS` with a 16-byte hex string (use `openssl rand -hex 16`)
   - Use different values for each placeholder
   - Minimum 32 characters recommended for security

**Domain Configuration:**

- For local testing: Keep `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"`
- For production: Change to your actual domain (e.g., `https://aihub.your-company.com`)

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
