---
title: One-Command Deployment
index: 2
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
ENV="prod"                            # Options: dev, test, prod

# =============================================================================
# AUTHENTICATION CONFIGURATION  
# =============================================================================

# General Authentication Settings
AUTH_ENABLE_API_ACCESS="True"
AUTH_OPEN_WEBUI_SIGNING_SECRET="REPLACE_WITH_RANDOM_STRING_1"
AUTH_IDENTITY_PROVIDER="azure"

# OAuth2 Configuration (from Prerequisites setup)
OAUTH_CLIENT_ID="REPLACE_WITH_YOUR_CLIENT_ID"
OAUTH_CLIENT_SECRET="REPLACE_WITH_YOUR_CLIENT_SECRET"  
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="REPLACE_WITH_YOUR_TENANT_ID"
OAUTH_COOKIE_SECRET="REPLACE_WITH_RANDOM_STRING_2"

# =============================================================================
# PLATFORM ACCESS CONFIGURATION
# =============================================================================

# Superuser Configuration
SUPERUSER_ENABLED="True"
SUPERUSER_NAME="AI-Hub Administrator"
SUPERUSER_EMAIL="admin@your-company.com"              # Replace with admin email
SUPERUSER_OID="REPLACE_WITH_RANDOM_STRING_3"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="REPLACE_WITH_RANDOM_STRING_4"

# Platform Settings
AIHUB_API_VERSION="dev"
AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"     # Change for production domain
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Recommended)
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_IMAGE="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_AUDIO="REPLACE_WITH_AZURE_OPENAI_KEY"

# Google Gemini (Alternative)
GEMINI_API_KEY="REPLACE_WITH_GEMINI_KEY"

# =============================================================================
# LITELLM PROXY CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="REPLACE_WITH_RANDOM_STRING_5"
LITELLM_MASTER_KEY="REPLACE_WITH_RANDOM_STRING_6"
LITE_LLM_PROXY_BASE_URL="http://litellm:4000"
LITE_LLM_PROXY_API_KEY="REPLACE_WITH_RANDOM_STRING_7"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# PostgreSQL
POSTGRES_USER="admin"
POSTGRES_PASSWORD="REPLACE_WITH_RANDOM_STRING_8"

# MongoDB  
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING_9"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@mongo:27017/"

# Redis (uses defaults)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# MinIO S3 Storage
MINIO_ROOT_USER="admin"
MINIO_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING_10"
S3_STORAGE_ENDPOINT="http://minio:9000"
S3_STORAGE_ACCESS_KEY="admin"                         # Must match MINIO_ROOT_USER
S3_STORAGE_SECRET_KEY="REPLACE_WITH_SAME_MINIO_PASSWORD"

# =============================================================================
# SERVICE ENDPOINTS (Internal - Don't Change)
# =============================================================================

DOCLING_API_ENDPOINT="http://docling:5001"
DOCLING_API_TIMEOUT="600"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING_11"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING_12"
MILVUS_URL="http://localhost"
MILVUS_DIMENSION="3072"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Jina AI Search (Optional)
# JINA_API_KEY="your_jina_api_key"
```

### Configuration Guidelines

**Critical Values to Replace:**

1. **Authentication Values** (from Prerequisites):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Your Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Your Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Your Azure Tenant ID (appears twice)

2. **AI Model Access** (configure at least one):

   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Your Azure OpenAI API key
   - `REPLACE_WITH_GEMINI_KEY` → Your Google Gemini API key

3. **Random Strings** (generate unique values):

   - Replace all `REPLACE_WITH_RANDOM_STRING_X` with unique random strings
   - Use different values for each placeholder
   - Minimum 32 characters recommended for security

**Domain Configuration:**

- For local testing: Keep `AIHUB_FRONTEND_ORIGIN="https://127.0.0.1.nip.io"`
- For production: Change to your actual domain (e.g., `https://ai-hub.your-company.com`)

::: tip Generate Random Strings
Use this command to generate secure random strings:

```bash
openssl rand -base64 32
```

Run it multiple times to get different values for each placeholder.
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
- **Databases** (MongoDB, PostgreSQL, Redis)
- **Vector Database** (Milvus)
- **LLM Proxy** (LiteLLM)
- **Document Processing** (Docling)
- **Observability** (Phoenix)
- **Message Queue** (NATS)
- **Storage** (MinIO)

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
