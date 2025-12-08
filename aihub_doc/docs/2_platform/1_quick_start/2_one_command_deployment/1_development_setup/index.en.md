---
title: "Development Setup"
description: "Set up a development environment for extending the Swiss AI Hub platform"
---

# Development Setup

This guide helps you set up a development environment for actively building and extending the Swiss AI Hub platform. The Docker Compose configuration starts all infrastructure services while you run the API, web frontend, and agents locally from source — enabling rapid iteration with hot-reloading and debugging.

## How Deployment Works

The Swiss AI Hub follows a simple deployment philosophy: **one command to launch everything**. The platform ships with pre-configured Docker Compose files that orchestrate all necessary services — databases, message queues, vector stores, authentication, observability, and supporting infrastructure.

For development, the compose file starts only the third-party infrastructure services. You then run the AI Hub's core services (API, web frontend, agents) locally from the repository, giving you full control over the development experience with hot-reloading, debugging, and rapid iteration.

Your main task is selecting the right configuration for your hardware and setting up environment variables. The Docker Compose files handle service dependencies, health checks, networking, and startup order automatically.

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

## What You Run Locally

After starting the infrastructure, you run these services from your local repository:

- **aihub-api** — The core API server
- **aihub-web** — The SvelteKit frontend
- **Agents** — Background workers for RAG, LLM wrapping, etc.

## Prerequisites

### Required Software

- **Docker** and **Docker Compose** (v2.20+)
- **Git** for cloning the repository
- **Node.js** (v20+) and **pnpm** for the web frontend
- **Python** (3.11+) and **uv** for the API and agents

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

### External Services

- **Azure AD / Entra ID** application registration for authentication
- **LLM Provider** (CPU variant only): Azure OpenAI, Google Gemini, or similar

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/bbvch-ai/aihub-core.git
cd aihub-core
```

---

## Step 2: Configure Environment Variables

Create a `.env` file in the repository root with your configuration settings.

### Generate the .env File

```bash
cp .env.example .env
```

### Essential Configuration

Edit the `.env` file and configure these values:

```env
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
```

::: code-group

```env [CPU Variant]
# Configure at least one external LLM provider

# Azure OpenAI (Recommended)
AZURE_OPENAI_BASE_URL="https://your-instance.openai.azure.com"
AZURE_OPENAI_KEY="your-azure-openai-key"

# Google Gemini (Alternative)
GEMINI_API_KEY="your-gemini-key"

# Hugging Face (for model downloads, optional)
HUGGINGFACE_API_KEY=""
```

```env [GPU Variant]
# Models are self-hosted, but HuggingFace token is required for downloads

HUGGINGFACE_API_KEY="your-huggingface-token"

# Optional: Configure external providers as fallback
AZURE_OPENAI_BASE_URL=""
AZURE_OPENAI_KEY=""
GEMINI_API_KEY=""
```

:::

```env
# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="generate-with-openssl-rand-hex-16"

MONGO_USERNAME="admin"
MONGO_PASSWORD="generate-with-openssl-rand-hex-16"
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@localhost:27017/"

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
MILVUS_DIMENSION="3072"
DOCLING_API_ENDPOINT="http://localhost:5001"
DOCLING_API_TIMEOUT="600"

# =============================================================================
# OBSERVABILITY (Optional)
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_CLOUD_ENDPOINT="localhost:4317"
OTEL_CLOUD_HEADERS=""

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search
```

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

---

## Step 3: Start Infrastructure Services

Launch all infrastructure services with Docker Compose:

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml up -d
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml up -d
```

:::

### Monitor Startup Progress

Watch the services initialize:

::: code-group

```bash [CPU Variant]
# Follow logs
docker compose -f docker-compose.dev.yml logs -f

# Check service status
docker compose -f docker-compose.dev.yml ps
```

```bash [GPU Variant]
# Follow logs
docker compose -f docker-compose.dev.gpu.yml logs -f

# Check service status
docker compose -f docker-compose.dev.gpu.yml ps
```

:::

Initial startup takes 3-5 minutes. Wait until all services show "healthy" status before proceeding.

::: warning GPU Variant First Start
The GPU variant downloads AI models on first startup, which can take 15-30 minutes depending on your internet connection. Subsequent starts are much faster.
:::

---

## Step 4: Verify Infrastructure

Once services are running, verify access to the key infrastructure UIs:

| Service | URL | Purpose |
|---------|-----|---------|
| **SeaweedFS Filer** | http://localhost:8889 | Browse S3 storage |
| **Attu** | http://localhost:3003 | Milvus vector database UI |
| **Phoenix** | http://localhost:6006 | ML tracing and observability |
| **NATS Monitoring** | http://localhost:8222 | Message queue status |
| **LiteLLM** | http://localhost:4000 | LLM proxy admin |

---

## Step 5: Run AI Hub Services Locally

With infrastructure running, start the AI Hub services from your local repository.

### Start the API

```bash
cd packages/api
uv sync
uv run uvicorn aihub_api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000.

### Start the Web Frontend

In a new terminal:

```bash
cd packages/web
pnpm install
pnpm dev
```

The frontend will be available at http://localhost:3000.

### Start Agents (Optional)

For full platform functionality, start the background agents:

```bash
# LLM Wrapping Agent
cd packages/agents/llm_wrapping_agent
uv sync
uv run python -m llm_wrapping_agent

# RAG Agent
cd packages/agents/rag_agent
uv sync
uv run python -m rag_agent

# Default RAG Pipeline
cd packages/agents/default_rag_pipeline
uv sync
uv run python -m default_rag_pipeline
```

---

## Step 6: Access the Platform

With all services running:

- **AI Hub Web Interface**: http://localhost:3000
- **Open WebUI (Chat)**: http://localhost:8080
- **API Documentation**: http://localhost:8000/docs

Log in using your Azure AD credentials. Ensure your user has the appropriate roles assigned in the Azure Enterprise Application.

---

## Exposed Ports Reference

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

::: code-group

```txt [CPU Variant]
No additional ports.
```

```txt [GPU Variant]
| 8182 | llama.cpp | Text generation |
| 8183 | llama.cpp | Embeddings |
| 8184 | llama.cpp | Reranking |
| 8186 | vLLM | Document OCR |
```

:::

---

## Common Operations

### Stopping Services

::: code-group

```bash [CPU Variant]
docker compose -f docker-compose.dev.yml down
```

```bash [GPU Variant]
docker compose -f docker-compose.dev.gpu.yml down
```

:::

### Resetting Data

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

---

## Troubleshooting

### Services Won't Start

1. Ensure Docker has sufficient resources allocated (16GB+ RAM)
2. Check if ports are already in use: `lsof -i :5432` (example for PostgreSQL)
3. Review logs for specific errors: `docker logs <container-name>`

### GPU Not Detected

1. Verify NVIDIA drivers are installed: `nvidia-smi`
2. Ensure NVIDIA Container Toolkit is installed
3. Test Docker GPU access: `docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi`

### Connection Refused Errors

1. Wait for services to fully initialize (check health status)
2. Verify the service is running: `docker ps | grep <service-name>`
3. Check if the port is correctly exposed: `docker port <container-name>`

### LiteLLM Model Errors (CPU Variant)

1. Verify your LLM provider credentials in `.env`
2. Check LiteLLM logs: `docker logs litellm`
3. Test the provider directly before using through LiteLLM

---

## Next Steps

With your development environment running, you can:

- Explore the API documentation at http://localhost:8000/docs
- Create knowledge bases and test RAG functionality
- Modify the API, web frontend, or agents with hot-reloading
- Add new LLM providers in the LiteLLM configuration
- Implement new agents and pipelines