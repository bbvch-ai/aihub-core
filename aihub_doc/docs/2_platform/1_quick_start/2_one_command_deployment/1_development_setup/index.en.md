---
title: "Development Setup"
---

# Development Setup

This guide helps you set up a development environment for actively building and extending the Swiss AI Hub platform. The Docker Compose configuration starts all infrastructure services while you run the API, web frontend, and agents locally from source — enabling rapid iteration with hot-reloading and debugging.

## What is Development Setup Mode?

The Swiss AI Hub follows a simple deployment philosophy: **one command to launch everything**. The platform ships with pre-configured Docker Compose files that orchestrate all necessary services — databases, message queues, vector stores, authentication, observability, and supporting infrastructure.

For development, the compose file starts only the third-party infrastructure services. You then run the AI Hub's core services (API, web frontend, agents) locally from the repository, giving you full control over the development experience with hot-reloading, debugging, and rapid iteration.

Your main task is selecting the right configuration for your hardware and setting up environment variables. The Docker Compose files handle service dependencies, health checks, networking, and startup order automatically.

::: tip When to Use Development Setup
- **Active development** on the platform codebase
- **Debugging** with IDE breakpoints and local tools
- **Hot-reloading** for rapid iteration
- **Testing local changes** before committing
:::


::: danger When NOT to Use Development Setup
- **Trying out the platform** - Use Local Playground instead (everything in Docker)
- **Production deployment** - Use Production Deployment (hardened security, real domain)
- **Docker configuration testing** - Use Build Mode (see end of this guide)
:::

## What's Included

The development Docker Compose starts these infrastructure services:

| Category | Services |
|----------|----------|
| **Storage** | SeaweedFS (S3-compatible object storage), PostgreSQL, FerretDB (MongoDB-compatible) |
| **Vector Database** | Milvus with etcd, Attu (Milvus UI) |
| **Messaging & Cache** | NATS (message queue), Valkey (Redis-compatible cache) |
| **LLM Proxy** | LiteLLM with Presidio (PII anonymization) |
| **Document Processing** | Docling (OCR and document parsing) |
| **Code Execution** | Jupyter, Playwright (browser automation) |
| **Observability** | Phoenix (ML tracing), OpenTelemetry Collector |
| **Chat Interface** | Open WebUI (connected to your local API) |

::: info GPU Variant Additions
The GPU variant additionally includes self-hosted AI models for text generation, embeddings, reranking, and document OCR. This enables fully offline development without external LLM API calls.
:::

After starting the infrastructure, you run these services from your local repository:

- **aihub_api** — The core API server
- **aihub_web** — The frontend UI
- **aihub_agent** — Agents for RAG, LLM wrapping, etc.



## Prerequisites


### Required Software

- **Docker** and **Docker Compose** (v2.20+)
- **Git** for cloning the repository
- **Node.js** (v20+) and **pnpm** for the web frontend
- **Python** (3.11+) and **poetry** for the API and agents


::: details Verify Installation

Before starting, verify all tools are installed:

```bash
# Check Docker (need v24.0+)
docker --version

# Check Docker Compose (need v2.20+)
docker compose version

# Check Git
git --version

# Check Python (need 3.11+)
python3 --version

# Check Poetry (need v1.6+)
poetry --version

# Check Node.js (need v20+)
node --version

# Check pnpm
pnpm --version
```
:::

::: warning Missing Tools?
If any command fails, install that tool first:
- **Docker**: https://docs.docker.com/get-docker/
- **Poetry**: https://python-poetry.org/docs/#installation
- **Node.js**: https://nodejs.org/ (includes npm)
- **pnpm**: `npm install -g pnpm`
:::

### Hardware Requirements

::: code-group

```txt [CPU Variant]
- 16 GB RAM minimum (32 GB recommended)
- 50 GB free disk space
- External LLM API access (Azure OpenAI, Google Gemini, etc.)
```

```txt [GPU Variant]
- 32 GB RAM minimum
- 100 GB free disk space
- NVIDIA GPU with 16+ GB VRAM
- NVIDIA Container Toolkit installed
```

:::

## Step 1: Set Up Azure AD Authentication

**Why this step?** The Swiss AI Hub uses Azure AD (Microsoft Entra ID) for authentication. Users log in with their Microsoft accounts, and Azure AD handles authorization. You need to register the AI Hub as an "application" in Azure so it can authenticate users.

### Step 1.1: Access Azure Portal

1. Navigate to https://portal.azure.com
2. Sign in with your Microsoft account (work/school or personal)
3. If you don't have an Azure subscription, you can use the free tier (no credit card required for app registration)

### Step 1.2: Create App Registration

1. In the Azure Portal search bar (top), type **"App registrations"** and select it
2. Click **"+ New registration"**
3. Configure the registration:
   - **Name**: `AI Hub Dev` (or any name you prefer)
   - **Supported account types**: Select **"Accounts in this organizational directory only"**
     - This restricts login to users in your Azure tenant
   - **Redirect URI**: Leave blank for now (we'll add this later)
4. Click **"Register"**

### Step 1.3: Copy Application IDs

After registration, you'll see the app overview page. Copy these values (you'll need them for `.env` file in Step 3):

1. **Application (client) ID**:
   - This is a GUID like `12345678-1234-1234-1234-123456789abc`
   - Copy this as your `OAUTH_CLIENT_ID`

2. **Directory (tenant) ID**:
   - Also a GUID
   - Copy this as your `OAUTH_TENANT_ID`
   - Also use this to construct `OAUTH_AUTHORITY_URL`:
     ```
     OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/<paste-tenant-id>"
     ```

### Step 1.4: Create Client Secret

1. In the left menu, click **"Certificates & secrets"**
2. Click **"+ New client secret"**
3. Configure:
   - **Description**: `Dev secret`
   - **Expires**: 6 months (you can choose longer for convenience)
4. Click **"Add"**
5. **⚠️ CRITICAL**: Immediately copy the **Value** (not the Secret ID)
   - This is your `OAUTH_CLIENT_SECRET`
   - You cannot view this value again after leaving this page
   - If you lose it, you'll need to create a new secret

### Step 1.5: Configure Redirect URIs

**Why?** After users log in, Azure AD redirects them back to your application. You must whitelist these redirect URLs.

1. In the left menu, click **"Authentication"**
2. Click **"+ Add a platform"**
3. Select **"Web"**
4. Add these **Redirect URIs** (one per line):
   ```
   http://localhost:8080/oauth/oidc/callback
   http://localhost:3000/oauth2/callback
   http://localhost:3007/oauth2/callback
   ```
   - `8080`: Open WebUI (chat interface)
   - `3000`: Admin web interface
   - `3007`: Dagster (pipeline UI)
5. Under **"Implicit grant and hybrid flows"**, check:
   - ✅ **ID tokens** (used for user authentication)
6. Click **"Configure"**

### Step 1.6: Assign Yourself Access

**Why?** Creating an app registration doesn't automatically give anyone access. You must explicitly assign users/groups.

1. In the Azure Portal search bar, type **"Enterprise applications"** (different from App registrations!)
2. Find your **"AI Hub Dev"** application
   - Filter by "Application type: All applications" if you don't see it
3. In the left menu, click **"Users and groups"**
4. Click **"+ Add user/group"**
5. Click **"None Selected"** under Users
6. Search for and select your user account
7. Click **"Select"**
8. Click **"Assign"**

::: tip Multiple Developers?
Repeat this step to add each team member who needs access to the development environment.
:::

### Verification

You now have these values for your `.env` file (Step 3):
- ✅ `OAUTH_CLIENT_ID` (from Step 1.3)
- ✅ `OAUTH_CLIENT_SECRET` (from Step 1.4)
- ✅ `OAUTH_TENANT_ID` (from Step 1.3)
- ✅ `OAUTH_AUTHORITY_URL` (constructed from tenant ID)

::: details Troubleshooting Azure AD

**"I don't see 'App registrations' in Azure Portal"**
- You might not have permission in your organization's Azure tenant
- Try using a personal Microsoft account to create a free Azure subscription
- Or use Superuser Mode (Option A)

**"AADSTS50011: The redirect URI specified in the request does not match"**
- Double-check redirect URIs in Authentication settings
- Ensure they match exactly: `http://localhost:8080/oauth/oidc/callback` (no trailing slash)

**"Access denied after logging in"**
- Check Step 1.6: Did you assign yourself access in Enterprise Applications?
- Make sure you're logging in with the same account you assigned

**"AADSTS700016: Application not found in directory"**
- You might be logged into a different Azure tenant
- Check the tenant ID in your `.env` matches the Azure Portal tenant

:::

## Step 2: Clone the Repository

```bash
git clone https://github.com/bbvch-ai/aihub-core.git
cd aihub-core
```

## Step 3: Configure Environment Variables

**Why this step?** The `.env` file contains all configuration for the Swiss AI Hub—database passwords, API keys, authentication settings, and service endpoints. Each service reads from this single file, ensuring consistent configuration across the platform.

### Step 3.1: Create .env File

Copy the development template:

```bash
cp .env.dev .env
```

This creates a `.env` file with sensible defaults for development. You need to fill in platform-specific values (marked with `your-*` or `generate-with-*` placeholders).

### Step 3.2: Configure Required Values

Open `.env` in your text editor. The file is organized into sections. Here's what you **must** configure:

#### 🔐 Authentication (REQUIRED)

Find these lines and replace with your values from Step 1:

```env
# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"              # ← From Step 1.3
OAUTH_CLIENT_SECRET="your-azure-client-secret"      # ← From Step 1.4
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"  # ← Use your tenant ID from Step 1.3
OAUTH_TENANT_ID="your-tenant-id"                    # ← From Step 1.3
```

#### 🔑 Generate Security Secrets (REQUIRED)

The platform uses random secrets for encryption, signing, and authentication. Generate them now:

```bash
# Run these commands and copy the output into your .env file
echo "OAUTH_COOKIE_SECRET=\"$(openssl rand -hex 16)\""
echo "AUTH_OPEN_WEBUI_SIGNING_SECRET=\"$(openssl rand -hex 32)\""
echo "SUPERUSER_TOKEN=\"$(openssl rand -hex 32)\""
echo "POSTGRES_PASSWORD=\"$(openssl rand -hex 16)\""
echo "MONGO_PASSWORD=\"$(openssl rand -hex 16)\""
echo "S3_STORAGE_SECRET_KEY=\"$(openssl rand -hex 16)\""
echo "LITELLM_MASTER_KEY=\"$(openssl rand -hex 32)\""
```

**What each secret does:**
- `OAUTH_COOKIE_SECRET`: Encrypts OAuth session cookies
- `AUTH_OPEN_WEBUI_SIGNING_SECRET`: Signs JWT tokens for Open WebUI chat interface
- `SUPERUSER_TOKEN`: API Token used by other docker services that communicate to the platform as superusers
- `POSTGRES_PASSWORD`: Database password for PostgreSQL
- `MONGO_PASSWORD`: Database password for MongoDB/FerretDB
- `S3_STORAGE_SECRET_KEY`: Object storage authentication
- `LITELLM_MASTER_KEY`: LiteLLM proxy authentication

Copy each generated line and paste into your `.env` file, replacing the placeholder.

#### 🔗 Update Connection Strings (REQUIRED)

Update LiteLLM API key to match master key:

```env
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"
```

Replace with the SAME value as `LITELLM_MASTER_KEY` above.

#### 🤖 AI Model Access (REQUIRED for CPU variant)

**Skip this if using GPU variant** (models run locally, no external API needed—just set `HUGGINGFACE_API_KEY` below).

**For CPU variant**, you need external LLM access. Choose ONE provider:

**Option A: Azure OpenAI (Recommended)**

```env
AZURE_OPENAI_BASE_URL="https://your-instance.openai.azure.com"
AZURE_OPENAI_KEY="your-azure-openai-key"
```

**Where to get these:**
1. Go to Azure Portal: https://portal.azure.com
2. Create an "Azure OpenAI" resource (different from app registration!)
3. Go to "Keys and Endpoint" section
4. Copy the endpoint (base URL) and one of the keys

**Why Azure OpenAI?** It provides enterprise-grade OpenAI models (GPT-4, GPT-3.5) with better SLAs and data privacy than public OpenAI.

**Option B: Google Gemini**

```env
GEMINI_API_KEY="your-gemini-key"
```

**Where to get this:**
1. Go to https://makersuite.google.com/app/apikey
2. Create an API key
3. Copy the key

**Option C: GPU Variant - Self-Hosted Models**

```env
HUGGINGFACE_API_KEY="your-huggingface-token"
```

**Where to get this:**
1. Go to https://huggingface.co/settings/tokens
2. Create a token (read access is sufficient)
3. Copy the token

**Why?** GPU variant downloads models from Hugging Face at first startup. The token allows downloading gated models.

### Step 3.3: Review Optional Settings

These have sensible defaults but you can customize:

#### 📊 Observability (Optional)

```env
OTEL_ENABLED="false"  # Set to "true" to enable distributed tracing
```

**When to enable:** If you want detailed performance traces sent to an external observability platform (requires OTEL_CLOUD_ENDPOINT configuration).

**For local development:** Keep as `"false"`. Phoenix (http://localhost:6006) will still show traces without this.

#### 🐛 Logging (Optional)

```env
LOG_LEVEL="DEBUG"  # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
```

**For development:** Keep as `"DEBUG"` to see detailed logs.
**For production:** Use `"INFO"` or `"WARNING"`.

### Step 3.4: Verify Configuration

Check that all required placeholders are filled:

```bash
grep -E "(your-|generate-with)" .env
```

**Expected result:** No output (empty). This means all placeholders are replaced.

**If you see output:** You have unfilled placeholders. Go back and fill them.

::: tip Save This .env File
After setup, save a copy of your `.env` file (without secrets) as a template for teammates. They can copy it and add their own secrets.
:::

::: details View Full .env Template (All Options)

For reference, here's the complete `.env` structure with all available options:

::: code-group

```env [CPU Variant]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="DEBUG"                      # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="dev"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"
OAUTH_CLIENT_SECRET="your-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="generate-with-openssl-rand-hex-16"

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="generate-with-openssl-rand-hex-32"

# =============================================================================
# SUPERUSER CONFIGURATION
# =============================================================================

SUPERUSER_ENABLED="True"
SUPERUSER_NAME="Development Admin"
SUPERUSER_EMAIL="dev@localhost"
SUPERUSER_OID="generate-with-openssl-rand-hex-16"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="generate-with-openssl-rand-hex-32"

# =============================================================================
# AI MODEL ACCESS
# =============================================================================
# Configure at least one external LLM provider

# Azure OpenAI (Recommended)
AZURE_OPENAI_BASE_URL="https://your-instance.openai.azure.com"
AZURE_OPENAI_KEY="your-azure-openai-key"

# Google Gemini (Alternative)
GEMINI_API_KEY="your-gemini-key"

# Hugging Face (for model downloads, optional)
HUGGINGFACE_API_KEY=""
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="generate-with-openssl-rand-hex-16"

MONGO_USERNAME="admin"
MONGO_PASSWORD="generate-with-openssl-rand-hex-16"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="generate-with-openssl-rand-hex-16"
S3_STORAGE_ENDPOINT="http://localhost:9000"
S3_STORAGE_URL_SIGNING_SECRET="generate-with-openssl-rand-hex-32"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="generate-with-openssl-rand-hex-16"
LITELLM_MASTER_KEY="generate-with-openssl-rand-hex-32"
LITE_LLM_PROXY_BASE_URL="http://localhost:4000"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="generate-with-openssl-rand-hex-16"
PHOENIX_SECRET="generate-with-openssl-rand-hex-16"
PHOENIX_ENDPOINT="http://localhost:6006"
NATS_ENDPOINT="nats://localhost:4222"
REDIS_URL="redis://localhost:6379"
MILVUS_URL="http://localhost:19530"
MILVUS_DIMENSION="3072"
DOCLING_API_ENDPOINT="http://localhost:5001"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# OBSERVABILITY (Optional)
# =============================================================================

OTEL_ENABLED="false"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_CLOUD_ENDPOINT="localhost:4317"
OTEL_CLOUD_HEADERS=""

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search
```

```env [GPU Variant]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="DEBUG"                      # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="dev"

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-azure-client-id"
OAUTH_CLIENT_SECRET="your-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="generate-with-openssl-rand-hex-16"

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="generate-with-openssl-rand-hex-32"

# =============================================================================
# SUPERUSER CONFIGURATION
# =============================================================================

SUPERUSER_ENABLED="True"
SUPERUSER_NAME="Development Admin"
SUPERUSER_EMAIL="dev@localhost"
SUPERUSER_OID="generate-with-openssl-rand-hex-16"
SUPERUSER_ROLE="AIHubSuperuser"
SUPERUSER_TOKEN="generate-with-openssl-rand-hex-32"

# =============================================================================
# AI MODEL ACCESS
# =============================================================================
# Models are self-hosted, but HuggingFace token is required for downloads

HUGGINGFACE_API_KEY="your-huggingface-token"

# Optional: Configure external providers as fallback
AZURE_OPENAI_BASE_URL=""
AZURE_OPENAI_KEY=""
GEMINI_API_KEY=""
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="generate-with-openssl-rand-hex-16"

MONGO_USERNAME="admin"
MONGO_PASSWORD="generate-with-openssl-rand-hex-16"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="generate-with-openssl-rand-hex-16"
S3_STORAGE_ENDPOINT="http://localhost:9000"
S3_STORAGE_URL_SIGNING_SECRET="generate-with-openssl-rand-hex-32"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="generate-with-openssl-rand-hex-16"
LITELLM_MASTER_KEY="generate-with-openssl-rand-hex-32"
LITE_LLM_PROXY_BASE_URL="http://localhost:4000"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="generate-with-openssl-rand-hex-16"
PHOENIX_SECRET="generate-with-openssl-rand-hex-16"
PHOENIX_ENDPOINT="http://localhost:6006"
NATS_ENDPOINT="nats://localhost:4222"
REDIS_URL="redis://localhost:6379"
MILVUS_URL="http://localhost:19530"
MILVUS_DIMENSION="3072"
DOCLING_API_ENDPOINT="http://localhost:5001"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# OBSERVABILITY (Optional)
# =============================================================================

OTEL_ENABLED="false"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_CLOUD_ENDPOINT="localhost:4317"
OTEL_CLOUD_HEADERS=""

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search
```

:::

### Generate Random Secrets

Use these commands to generate secure random strings:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For shorter secrets like OAUTH_COOKIE_SECRET (32 characters)
openssl rand -hex 16
```

### Validate Configuration

Ensure all placeholders are replaced:

```bash
grep -n "your-\|generate-with" .env
```

This should return no results if all values are configured.

:::

## Step 4: Start Infrastructure Services

**Why this step?** The Swiss AI Hub depends on ~15 infrastructure services (databases, message queues, vector stores, etc.). Docker Compose orchestrates all of them, handling dependencies and health checks automatically.

**Time**: 5-10 minutes (CPU), 30-45 minutes first time (GPU downloads models)

### Step 4.1: Launch Services

Start all infrastructure services with one command:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml up -d
```

:::

The `-d` flag runs containers in the background (detached mode).

**What's happening:**
- Docker pulls required images (if not cached)
- Creates network bridges for service communication
- Mounts volumes for persistent data
- Starts services in dependency order
- Runs health checks until all services are ready

### Step 4.2: Monitor Startup

Watch the logs in real-time:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml logs -f
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml logs -f
```

:::

Press `Ctrl+C` to stop following logs (services keep running).

**What to look for:**
- ✅ `healthy` status messages
- ✅ Services reporting "ready to accept connections"
- ❌ Repeated restart attempts (indicates a problem)
- ❌ Port conflict errors (`address already in use`)

### Step 4.3: Verify All Services Are Healthy

After 5-10 minutes (CPU) or 30-45 minutes (GPU), check service status:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml ps
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml ps
```

:::

**Expected output:**

```
NAME                STATUS              PORTS
attu                Up (healthy)        0.0.0.0:3003->3000/tcp
docling             Up (healthy)        0.0.0.0:5001->5001/tcp
etcd                Up (healthy)        2379-2380/tcp
ferretdb            Up (healthy)        0.0.0.0:27017->27017/tcp
jupyter             Up (healthy)        0.0.0.0:8888->8888/tcp
litellm             Up (healthy)        0.0.0.0:4000->4000/tcp
milvus              Up (healthy)        0.0.0.0:19530->19530/tcp
nats                Up (healthy)        0.0.0.0:4222->4222/tcp
otel-collector      Up (healthy)        4317-4318/tcp
phoenix             Up (healthy)        0.0.0.0:6006->6006/tcp
playwright          Up (healthy)        8877/tcp
postgres            Up (healthy)        0.0.0.0:5432->5432/tcp
presidio-analyzer   Up (healthy)        3000/tcp
presidio-anonymizer Up (healthy)        3000/tcp
s3                  Up (healthy)        0.0.0.0:8889->8889/tcp
valkey              Up (healthy)        0.0.0.0:6379->6379/tcp
```

**All services should show:**
- ✅ `Up` status
- ✅ `(healthy)` indicator
- ✅ Port mappings

::: warning GPU Variant First Start
The GPU variant downloads large AI models on first startup:
- **llama.cpp models**: ~15-20 GB (Llama 3, embeddings, reranking)
- **vLLM OCR model**: ~5-10 GB

This takes 30-45 minutes on a typical internet connection. Progress shows in logs:
```
llama-cpp-text | Downloading model: meta-llama/Llama-3.2-3B-Instruct...
llama-cpp-text | Downloaded 1.2 GB / 6.4 GB (18%)...
```

Subsequent starts are fast (~5 minutes) since models are cached.
:::

### Step 4.4: Troubleshooting

**Problem: Service stuck in "starting" for > 5 minutes**

Check the service logs:
```bash
docker logs <service-name>

# Example:
docker logs milvus
```

Common causes:
- Dependency not ready yet (wait longer)
- Configuration error (check .env file)
- Port conflict (another service using the port)

**Problem: "port is already allocated"**

Another process is using the required port. Find and stop it:
```bash
# Find process using port (example: 8080)
sudo lsof -i :8080

# Stop the process
sudo kill -9 <PID>

# Or change port in docker-compose.dev.yml
```

**Problem: "unhealthy" status**

Service started but health check is failing:
```bash
# Check health check logs
docker inspect <service-name> --format='{{json .State.Health}}'

# Restart the service
docker restart <service-name>
```

**Still having issues?**
- Check Docker has enough resources (Settings → Resources): 16 GB RAM minimum
- Check disk space: `df -h` (need 50+ GB free)
- Restart Docker daemon: `sudo systemctl restart docker`

## Step 5: Verify Infrastructure Access

**Why this step?** Before running AI Hub services, verify that infrastructure is accessible. Each service exposes a web UI or API endpoint for monitoring.

**Time**: 2-3 minutes

Open each URL in your browser and verify you see the expected interface:

| Service | URL | What You Should See | Why It Matters |
|---------|-----|---------------------|----------------|
| **SeaweedFS** | http://localhost:8889 | File browser with "buckets/" folder | Object storage (files, artifacts) |
| **Attu** | http://localhost:3003 | "Attu - Milvus Admin" dashboard | Vector database UI (search embeddings) |
| **Phoenix** | http://localhost:6006 | "Phoenix" observability dashboard | ML tracing and performance monitoring |
| **NATS** | http://localhost:8222 | JSON with `"server_name": "nats"` | Message queue health (agent communication) |
| **LiteLLM** | http://localhost:4000 | Swagger UI with "/health" endpoint | LLM proxy (unified AI model access) |

**What each service does:**
- **SeaweedFS**: S3-compatible storage for uploaded files, agent artifacts, and data pipeline outputs
- **Attu**: Admin UI for Milvus vector database (stores document embeddings for RAG)
- **Phoenix**: Observability platform that shows LLM traces, token usage, and latency
- **NATS**: Message broker for event-driven communication between agents and processes
- **LiteLLM**: Proxy that provides a unified interface to OpenAI, Azure OpenAI, Gemini, and local models

::: tip Quick Test
Visit http://localhost:4000/health - you should see `{"status": "healthy"}`. This confirms LiteLLM is ready to proxy AI model requests.
:::

::: details If a Service Is Not Accessible

**"Connection refused" error:**
- Service is still starting. Wait 2 more minutes and refresh.
- Check service status: `docker ps | grep <service-name>`

**"This site can't be reached":**
- Firewall blocking the port. Disable firewall or add exception.
- Check port mapping: `docker port <service-name>`

**Blank page or error:**
- Check logs: `docker logs <service-name>`
- Service might be unhealthy. Restart: `docker restart <service-name>`

:::

## Step 6: Run AI Hub Services Locally

**Why this step?** With infrastructure ready, now run the AI Hub's core services from your local repository. This gives you hot-reloading, IDE debugging, and instant feedback on code changes.

**Time**: 10-15 minutes (Poetry install takes time first run)

::: tip Terminal Management
You'll run 3-5 services in separate terminal windows. Options:
- **VS Code**: Use split terminals (View → Terminal, click "+" to add)
- **tmux**: Run `tmux` then split panes with `Ctrl+B "` (horizontal) or `Ctrl+B %` (vertical)
- **Separate windows**: Open 3-5 terminal windows and arrange them side-by-side
:::

### Step 6.1: Start the API

**Terminal 1** - Open your first terminal and run:

```bash
cd aihub_api
poetry install
poetry run uvicorn aihub_api.main:app --reload --host 0.0.0.0 --port 8000
```

**What's happening:**
- `poetry install`: Installs Python dependencies from `poetry.lock` (takes 3-5 minutes first time)
- `uvicorn`: ASGI server for running FastAPI applications
- `--reload`: Automatically restarts server when code changes (hot-reload)
- `--host 0.0.0.0`: Listens on all network interfaces (allows Docker services to connect)
- `--port 8000`: API runs on port 8000

**Expected output:**
```
Installing dependencies from lock file...
Package operations: 120 installs, 0 updates, 0 removals
  • Installing certifi (2024.2.2)
  ...
  • Installing fastapi (0.109.2)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
```

**Verify:** Open http://localhost:8000/docs - you should see **Swagger UI** with API documentation.

::: details Troubleshooting API Startup

**"poetry: command not found":**
- Poetry not installed. Run: `curl -sSL https://install.python-poetry.org | python3 -`
- Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`

**"Python version mismatch" (requires 3.11+):**
- Check version: `python3 --version`
- Install Python 3.11+: `sudo apt install python3.11` (Ubuntu) or use pyenv

**"Cannot connect to MongoDB / Redis / etc.":**
- Infrastructure services not running. Go back to Step 4.
- Check .env file has correct connection strings

**"ModuleNotFoundError" after installing:**
- Clear Poetry cache: `poetry cache clear pypi --all`
- Reinstall: `poetry install --no-cache`

:::

### Step 6.2: Start the Web Frontend

🔄 **Terminal 2** - **Open a NEW terminal window** (keep API running in Terminal 1)

```bash
cd aihub_web/aihub_web
pnpm install
pnpm dev
```

**What's happening:**
- `pnpm install`: Installs Node.js dependencies from `pnpm-lock.yaml` (takes 2-3 minutes first time)
- `pnpm dev`: Starts Nuxt.js development server with hot-reload

**Expected output:**
```
Packages: +1234 +++++++++++++++++++++++++++++++++++++
Progress: resolved 1234, reused 1234, downloaded 0, added 1234, done

> dev
> nuxt dev

Nuxt 3.10.0 with Nitro 2.9.0
  ➜ Local:    http://localhost:3000/
  ➜ Network:  http://192.168.1.10:3000/

✔ Nuxt DevTools is enabled
```

**Verify:** Open http://localhost:3000 - you should see the **AI Hub login page** (Azure AD sign-in button or superuser token field).

::: details Troubleshooting Web Frontend

**"pnpm: command not found":**
- Install pnpm: `npm install -g pnpm`

**"Port 3000 already in use":**
- Another service using port 3000. Stop it or change port:
- Edit `nuxt.config.ts`: `devServer: { port: 3001 }`

**"Module not found" errors:**
- Delete `node_modules`: `rm -rf node_modules`
- Reinstall: `pnpm install`

**Blank page or errors after login:**
- Check API is running at http://localhost:8000/docs
- Check browser console (F12) for errors

:::

### Step 6.3: Start Agents (Optional)

**Why run agents?** Agents are background workers that handle specific tasks:
- **LLM Wrapping Agent**: Wraps external LLM calls with monitoring and error handling
- **RAG Agent**: Retrieval-Augmented Generation for knowledge base queries
- **Pipeline (Dagster)**: Data ingestion workflows (PDF parsing, chunking, embedding)

You can skip agents initially and add them later when needed.

#### LLM Wrapping Agent

🔄 **Terminal 3** - Open a NEW terminal:

```bash
cd aihub_agent
poetry install
poetry run python playground/agent/LLMWrappingAgent/run.py
```

**Expected output:**
```
INFO: Agent LLMWrappingAgent started successfully
INFO: Listening for events on: agent.llm_wrapping.*
INFO: Connected to NATS at nats://localhost:4222
```

**What it does:** Intercepts LLM calls from chat interface, adds observability (Phoenix traces), handles retries and errors.

#### RAG Agent

🔄 **Terminal 4** - Open a NEW terminal:

```bash
cd aihub_agent
poetry install
poetry run python playground/agent/RAGAgent/run.py
```

**Expected output:**
```
INFO: Agent RAGAgent started successfully
INFO: Listening for events on: agent.rag.*
INFO: Connected to NATS at nats://localhost:4222
INFO: Connected to Milvus at http://localhost:19530
```

**What it does:** Searches knowledge bases for relevant documents, retrieves context for AI responses, handles semantic search.

#### Pipeline (Data Ingestion)

🔄 **Terminal 5** - Open a NEW terminal:

```bash
cd aihub_pipeline
poetry install
poetry run dagster dev -h 0.0.0.0 -p 3007
```

**Expected output:**
```
Serving Dagster webserver on http://0.0.0.0:3007
Dagster version: 1.6.9
```

**Verify:** Open http://localhost:3007 - you should see the **Dagster UI** with asset definitions.

**What it does:** Runs data pipelines (PDF → text → chunks → embeddings → Milvus). Required for uploading documents to knowledge bases.

::: tip Start What You Need
- **Basic testing**: Just API + Web (Steps 6.1-6.2)
- **Chat functionality**: Add LLM Wrapping Agent (Step 6.3.1)
- **Knowledge bases**: Add RAG Agent + Pipeline (Steps 6.3.2-6.3.3)
:::

## Step 7: Access the Platform and Test

**Time**: 5 minutes

### Step 7.1: Access URLs

With all services running, you can access:

| Service | URL | What You Can Do |
|---------|-----|-----------------|
| **AI Hub Admin** | http://localhost:3000 | Manage knowledge bases, users, settings |
| **Open WebUI** | http://localhost:8080 | Chat interface with AI models |
| **API Docs** | http://localhost:8000/docs | Test API endpoints directly (Swagger) |
| **Phoenix** | http://localhost:6006 | View LLM traces, token usage, latency |
| **Dagster** | http://localhost:3007 | Trigger data pipelines, view runs |

### Step 7.2: Log In

#### Option A: Azure AD Login (Step 1, Option B)

1. Open http://localhost:3000
2. Click **"Sign in with Azure AD"**
3. Log in with your Microsoft account (the one you assigned in Step 1.6)
4. Accept permissions if prompted
5. You should be redirected to the AI Hub dashboard

#### Option B: Superuser Token (Step 1, Option A)

1. Find your `SUPERUSER_TOKEN` from `.env` file
2. Open: `http://localhost:3000?token=<your-superuser-token>`
3. You should see the AI Hub dashboard directly

::: details Login Troubleshooting

**"Access denied" after Azure AD login:**
- Check Step 1.6: Did you assign your user in Enterprise Applications?
- Verify tenant ID in `.env` matches Azure Portal tenant
- Check redirect URIs in Azure AD Authentication settings

**"AADSTS50011: Redirect URI mismatch":**
- Ensure redirect URI is exactly: `http://localhost:3000/oauth2/callback`
- No trailing slash, no https

**Superuser token not working:**
- Check `SUPERUSER_ENABLED="True"` in `.env` (capital T)
- Verify token is correct (no spaces, no quotes in URL)
- Check API logs (Terminal 1) for authentication errors

:::

### Step 7.3: Verify Everything Works

Quick smoke test to ensure platform is functional:

1. **Test API** (http://localhost:8000/docs):
   - Click on `/health` endpoint
   - Click "Try it out" → "Execute"
   - Should return `{"status": "healthy"}`

2. **Test Chat** (http://localhost:8080):
   - Log in with same credentials
   - Start a new chat
   - Type a message (e.g., "Hello, how are you?")
   - If LLM Wrapping Agent is running, you should get a response

3. **Test Phoenix Tracing** (http://localhost:6006):
   - Go to "Traces" tab
   - You should see trace for the chat message you just sent
   - Click trace to see LLM call details, tokens, latency

4. **Test Admin UI** (http://localhost:3000):
   - Navigate through settings, knowledge bases
   - If Pipeline is running, try creating a knowledge base

::: tip Success!
If you can log in and see the dashboard, your development environment is ready! 🎉

Next steps:
- Make code changes and see them hot-reload automatically
- Set breakpoints in your IDE to debug
- Check Phoenix for observability and tracing
- Read the [Developer Guide](link) for contribution guidelines
:::

::: details What If Something Doesn't Work?

**Logs are your friend.** Check terminal outputs for errors:
- **API errors**: Terminal 1 (aihub_api)
- **Web errors**: Terminal 2 (aihub_web) + Browser console (F12)
- **Agent errors**: Terminals 3-4 (agents)
- **Infrastructure errors**: `docker logs <service-name>`

**Common issues:**
- **502 Bad Gateway**: API not running or crashed. Check Terminal 1.
- **Can't connect to MongoDB/Redis**: Check `.env` connection strings and Step 4.
- **Chat not responding**: LLM Wrapping Agent not running or LLM credentials invalid.
- **Knowledge base errors**: Pipeline or RAG Agent not running.

**Still stuck?** Check our [full troubleshooting guide](link) or ask in [Discord](link).

:::

## Exposed Ports Reference

::: details Click to view all exposed ports

The development setup exposes these ports for local access:

| Port | Service | Description |
|------|---------|-------------|
| 3000 | Web Frontend | Your locally running SvelteKit app |
| 5432 | PostgreSQL | Primary database |
| 6006 | Phoenix | ML observability UI |
| 6007 | Phoenix gRPC | Trace ingestion |
| 6379 | Valkey | Redis-compatible cache |
| 8000 | API | Your locally running API server |
| 8080 | Open WebUI | Chat interface |
| 8222 | NATS Monitoring | Message queue status |
| 8889 | SeaweedFS Filer | S3 storage browser |
| 9000 | SeaweedFS S3 | S3 API endpoint |
| 19530 | Milvus | Vector database |
| 27017 | FerretDB | MongoDB-compatible API |
| 3003 | Attu | Milvus UI |
| 4000 | LiteLLM | LLM proxy |
| 4222 | NATS | Message queue |

**GPU Variant Additional Ports:**

| Port | Service | Description |
|------|---------|-------------|
| 8182 | llama.cpp | Text generation |
| 8183 | llama.cpp | Embeddings |
| 8184 | llama.cpp | Reranking |
| 8186 | vLLM | Document OCR |

:::

## Common Development Operations

### Stopping Services

**Stop AI Hub services:**
- Press `Ctrl+C` in each terminal running API/web/agents

**Stop infrastructure:**

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml down
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml down
```

:::

### Resetting Data

::: danger Data Loss Warning
This operation deletes all data permanently, including databases, vector stores, and file storage. There is no undo.
:::

To completely reset all data and start fresh:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml down -v
rm -rf .docker-volumes
docker compose -f docker-compose.dev.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml down -v
rm -rf .docker-volumes
docker compose -f docker-compose.dev.gpu.yml up -d
```

:::

### Viewing Logs for Specific Services

```bash
# View logs for a specific service
docker logs -f milvus

# View logs for multiple services
docker logs -f litellm postgres
```

### Daily Workflow (After Initial Setup)

After you've completed setup once, starting your dev environment is much faster:

**Quick Start (5-10 minutes):**

```bash
# 1. Start infrastructure (wait 2-3 min for healthy status)
docker compose -f docker-compose.dev.yml up -d

# 2. In Terminal 1 - Start API
cd aihub_api && poetry run uvicorn aihub_api.main:app --reload --host 0.0.0.0 --port 8000

# 3. In Terminal 2 - Start Web
cd aihub_web/aihub_web && pnpm dev

# 4. Optional - Start agents in additional terminals
```

**Updating Dependencies:**

If `poetry.lock` or `package.json` changed (after git pull):

```bash
# Update Python dependencies
cd aihub_api && poetry install

# Update Node dependencies
cd aihub_web/aihub_web && pnpm install
```

**Pulling Latest Changes:**

```bash
git pull
# Check if .env.dev changed - you may need to update your .env
diff .env .env.dev
```

## Alternative: Running in Docker (Build Mode)

The standard development setup runs infrastructure in Docker while you run AI Hub services (API, web, agents) locally for rapid iteration. However, you might want to test the complete platform running entirely in Docker with locally built images—for example, to validate Docker configurations or test changes before creating a pull request.

### When to Use Build Mode

Use `docker-compose.build.yml` when you want to:

- Test your changes in a production-like Docker environment
- Validate Dockerfiles and service configurations
- Debug issues that only appear when running in containers
- Test the complete stack without running services locally

### Prerequisites

Same as the standard development setup (Step 1-2 above), plus ensure all code changes are saved since Docker will build from your current working directory.

### Step 1: Build and Launch

Build Docker images from your local source code and start all services:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.build.yml up -d --build
```

```bash [GPU Variant]
docker compose -f docker-compose.build.gpu.yml up -d --build
```

:::

The `--build` flag forces a rebuild of all images. Initial build takes 10-15 minutes; subsequent builds are faster due to layer caching.

### Step 2: Monitor Startup

Watch the services initialize:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.build.yml logs -f
```

```bash [GPU Variant]
docker compose -f docker-compose.build.gpu.yml logs -f
```

:::

### Step 3: Access Services

All services are available at the same URLs as the standard development setup:

- **Open WebUI (Chat)**: http://localhost:8080
- **Admin UI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Phoenix (Observability)**: http://localhost:6006
- **Dagster (Pipeline UI)**: http://localhost:3007

### Rebuilding After Code Changes

When you make code changes, rebuild the affected services:

::: code-group

```bash [Rebuild Specific Service (CPU)]
docker compose -f docker-compose.build.yml up -d --build api
```

```bash [Rebuild Specific Service (GPU)]
docker compose -f docker-compose.build.gpu.yml up -d --build api
```

```bash [Rebuild All Services (CPU)]
docker compose -f docker-compose.build.yml up -d --build
```

```bash [Rebuild All Services (GPU)]
docker compose -f docker-compose.build.gpu.yml up -d --build
```

:::

### Stopping Build Mode

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.build.yml down
```

```bash [GPU Variant]
docker compose -f docker-compose.build.gpu.yml down
```

:::

### Build Mode vs. Standard Development

::: details Click to compare Standard Development vs Build Mode

| Aspect | Standard Development | Build Mode |
|--------|---------------------|------------|
| **Services in Docker** | Infrastructure only | Everything |
| **Hot-reload** | ✅ Yes (API, web, agents) | ❌ No (must rebuild) |
| **Startup time** | ~5 minutes | ~15 minutes (first build) |
| **Iteration speed** | ⚡ Fast | 🐢 Slower |
| **Debugging** | ✅ Easy (local IDE) | ⚠️ Harder (in container) |
| **Production parity** | ⚠️ Lower | ✅ Higher |
| **Use case** | Active development | Pre-PR testing, Docker validation |

:::

::: tip Recommendation
Use **standard development mode** for day-to-day coding. Switch to **build mode** when you need to validate Docker configurations or test in a production-like environment before creating a pull request.
:::


