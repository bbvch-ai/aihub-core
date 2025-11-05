---
title: One-command deployment
---

# One-command deployment

Deploy the platform with Docker Compose. Takes three steps: download configuration, set environment variables, start services.

## Step 1: Download configuration

Get the Docker Compose file:

```bash
# Create deployment directory
mkdir swiss-ai-hub-deployment
cd swiss-ai-hub-deployment

# Download configuration
curl -O https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/docker-compose.latest.yml
```

Or download `docker-compose.latest.yml` from the [aihub-core repository](https://github.com/bbvch-ai/aihub-core).

Verify:

```bash
ls -la docker-compose.latest.yml
```

## Step 2: Configure environment

Create `.env` file:

```bash
touch .env
```

Add configuration (replace placeholder values):

```env
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="WARNING"                    # Options: CRITICAL, ERROR, WARNING, INFO, DEBUG
ENV="prod"                            # Options: dev, test, prod
AIHUB_API_VERSION="dev"

# =============================================================================
# Domain and DNS configuration
# =============================================================================

# Main domain (without protocol)
DOMAIN="127.0.0.1.nip.io"                # Local: 127.0.0.1.nip.io, Production: aihub.example.com

# SSL/TLS certificate
ACME_EMAIL="admin@example.com"

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

# Role management
AIHUB_CREATE_DEFAULT_ROLES="True"

# =============================================================================
# Service access control
# =============================================================================

# Dagster and data lake access (defaults to AIHubDeveloper)
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubDeveloper"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubDeveloper"

# =============================================================================
# Traefik admin
# =============================================================================

# Dashboard access (generate with: htpasswd -nbB admin your-password)
TRAEFIK_ADMIN_PASSWORD_HASH="REPLACE_WITH_HTPASSWD_HASH"

# =============================================================================
# AI MODEL ACCESS (Configure at least one)
# =============================================================================

# Azure OpenAI (Recommended)
AZURE_OPENAI_KEY="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_IMAGE="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_KEY_AUDIO="REPLACE_WITH_AZURE_OPENAI_KEY"
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"

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

# FerretDB (MongoDB-compatible)
MONGO_USERNAME="admin"
MONGO_PASSWORD="REPLACE_WITH_RANDOM_STRING_9"
MONGO_CONNECTION_STRING="mongodb://admin:REPLACE_WITH_SAME_MONGO_PASSWORD@ferretdb:27017/"

# Valkey (Redis-compatible)
REDIS_URL="redis://localhost:6379"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# SeaweedFS S3 Storage
SEAWEEDFS_ROOT_USER="admin"
SEAWEEDFS_ROOT_PASSWORD="REPLACE_WITH_RANDOM_STRING_10"
S3_STORAGE_ENDPOINT="http://seaweedfs:8333"
S3_STORAGE_ACCESS_KEY="admin"                         # Must match SEAWEEDFS_ROOT_USER
S3_STORAGE_SECRET_KEY="REPLACE_WITH_RANDOM_STRING_11"
# S3_STORAGE_URL_SIGNING_SECRET must be same as S3_STORAGE_SECRET_KEY for now
S3_STORAGE_URL_SIGNING_SECRET="REPLACE_WITH_SAME_AS_S3_STORAGE_SECRET_KEY"

# =============================================================================
# SERVICE ENDPOINTS (Internal - Don't Change)
# =============================================================================

DOCLING_API_ENDPOINT="http://docling:5001"
DOCLING_API_TIMEOUT="600"
PHOENIX_SECRET="REPLACE_WITH_RANDOM_STRING_12"
PHOENIX_ENDPOINT="http://phoenix:6006"
NATS_ENDPOINT="nats://localhost:4222"
DAGSTER_HOME="~/.dagster_home"
JUPYTER_TOKEN="REPLACE_WITH_RANDOM_STRING_13"
MILVUS_URL="http://localhost"
MILVUS_DIMENSION="3072"

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

# Jina AI Search (Optional)
# JINA_API_KEY="your_jina_api_key"
```

Replace these values:

1. Authentication (from prerequisites):
   - `REPLACE_WITH_YOUR_CLIENT_ID` → Azure client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Azure client secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Azure tenant ID (appears twice)

2. AI model access (at least one):
   - `REPLACE_WITH_AZURE_OPENAI_KEY` → Azure OpenAI API key
   - `REPLACE_WITH_GEMINI_KEY` → Google Gemini API key

3. Random strings:
   - Replace all `REPLACE_WITH_RANDOM_STRING_X` with unique values
   - Use different values for each placeholder
   - Minimum 32 characters

Domain configuration:
- Local testing: Keep `DOMAIN=127.0.0.1.nip.io` (automatic DNS to localhost)
- Production: Use your domain like `DOMAIN=aihub.example.com`

For production, create DNS records for six subdomains:
- `aihub.example.com` - main interface
- `openwebui.aihub.example.com` - chat UI
- `dagster.aihub.example.com` - pipeline orchestration
- `datalake.aihub.example.com` - data lake console
- `datalake-api.aihub.example.com` - S3 API
- `traefik.aihub.example.com` - reverse proxy dashboard

All point to your server's public IP.

Generate random strings:

```bash
openssl rand -hex 32
```

Run multiple times for different values.

Validate configuration:

```bash
# Check for missing values
grep -n "REPLACE_WITH" .env
```

Should return no results.

## Step 3: Deploy

Start services:

```bash
docker compose -f docker-compose.latest.yml up -d
```

This downloads images, creates networks and volumes, and starts services.

Monitor progress:

```bash
# Watch logs
docker compose -f docker-compose.latest.yml logs -f

# Check status
docker compose -f docker-compose.latest.yml ps
```

Core services:
- Web interface (aihub-web)
- API (aihub-api)
- Authentication services
- Databases (FerretDB, PostgreSQL, Valkey)
- Vector database (Milvus)
- LLM proxy (LiteLLM)
- Document processing (Docling)
- Observability (Phoenix)
- Message queue (NATS)
- Storage (SeaweedFS)

Initial startup takes 5-10 minutes:

Timeline:
- 0-2 minutes: SSL certificate provisioning (Let's Encrypt ACME challenge)
- 2-7 minutes: Docling model downloads (~2GB, cached for future use)
- 7-10 minutes: All services healthy

Watch progress:

```bash
# Monitor deployment
docker compose -f docker-compose.latest.yml ps --format "table {{.Name}}\t{{.Status}}"

# Follow specific services
docker compose -f docker-compose.latest.yml logs -f docling traefik
```

Traefik automatically provisions SSL certificates from Let's Encrypt on first run. Docling downloads AI models (layout, tableformer, OCR) once and caches them. Subsequent starts take 30 seconds because certificates and models are cached.

## Step 4: Verify deployment

Assign your test user the `AIHubAdmin` and `AIHubDeveloper` roles in Azure Enterprise Application first. The `AIHubAdmin` role provides access to the main interface and OpenWebUI. The `AIHubDeveloper` role is required for accessing Dagster and the data lake console.

Service URLs:

Local deployment (`127.0.0.1.nip.io`):
- Main interface: `https://127.0.0.1.nip.io`
- Chat UI: `https://openwebui.127.0.0.1.nip.io`
- Pipeline orchestration: `https://dagster.127.0.0.1.nip.io`
- Data lake console: `https://datalake.127.0.0.1.nip.io`
- Traefik dashboard: `https://traefik.127.0.0.1.nip.io` (admin credentials)

Production deployment:
- Main interface: `https://aihub.example.com`
- Chat UI: `https://openwebui.aihub.example.com`
- Pipeline orchestration: `https://dagster.aihub.example.com`
- Data lake console: `https://datalake.aihub.example.com`
- Traefik dashboard: `https://traefik.aihub.example.com` (admin credentials)

Login flow:
- Browser redirects to Microsoft/Azure authentication
- Enter credentials (user with AIHubAdmin role)
- After login, redirects to AI-Hub interface
- Main dashboard with language selector (de/en/fr/it)

### Health checks

Check API:

```bash
curl https://127.0.0.1.nip.io/api/v1/health
```

Check Phoenix:

```bash
curl https://127.0.0.1.nip.io/phoenix/
```

## Common issues

### Authentication fails

Check redirect URIs match exactly in Azure AD. See [authentication setup](../1_prerequisites/) for configuration. Verify OAuth credentials are correct. Confirm user is assigned to app role in Enterprise Application.

### Services won't start

```bash
# Check logs
docker compose -f docker-compose.latest.yml logs <service-name>

# Verify environment
docker compose -f docker-compose.latest.yml config | grep DOMAIN

# Check resources
df -h  # Disk space
free -h  # Memory
```

### SSL certificate issues

```bash
# View Traefik logs
docker compose -f docker-compose.latest.yml logs traefik | grep -i acme

# Verify DNS
dig +short ${DOMAIN}
```

Ports 80 and 443 need internet access. DNS records must exist before Let's Encrypt issues certificates.

### DNS resolution issues (production only)

For production deployments on a VM in a subnet, ensure DNS records are both globally and locally resolvable.

**Symptoms**: Authentication timeouts, OAuth failures after DNS is configured correctly.

**Cause**: VM cannot resolve its own domain. Common when nameservers in `/etc/resolv.conf` are not in your subnet.

**Test**:

```bash
# From the VM itself
dig +short aihub.example.com
curl -I https://aihub.example.com
```

**Fix**: Update `/etc/resolv.conf` to use a nameserver that can resolve your domain (e.g., 8.8.8.8). See [network requirements](../../3_deployment_guide/7_network_requirements/) for detailed guidance.

## Next steps

- [First conversation](../4_your_first_conversation/) - test the platform
- [Production configuration](../../3_deployment_guide/2_production_configuration/) - full environment setup
- [Authentication setup](../../11_access_management/1_authentication_setup/) - detailed OAuth configuration
