---
title: "Production Deployment"
description: "Deploy the Swiss AI Hub to production with real domain, automatic SSL, and enterprise-grade security"
---

# Production Deployment

This guide walks you through deploying the Swiss AI Hub to a production server with a real domain name, automatic Let's Encrypt SSL certificates, and enterprise-grade configuration. Designed for IT administrators and production deployments where the platform will serve real users.

## What is Production Deployment?

Production deployment runs the complete Swiss AI Hub stack on a dedicated server with:

- **Real Domain**: Custom domain (e.g., `aihub.company.com`)
- **Automatic SSL**: Let's Encrypt certificates via Traefik (auto-renewal)
- **Pre-Built Images**: Stable `latest` or bleeding-edge `nightly` images from the registry
- **Production Security**: No development backdoors, hardened configurations
- **Scalable Architecture**: Ready for organizational workloads

### Differences from Local Playground

| Aspect | Local Playground | Production Deployment |
|--------|------------------|----------------------|
| **Domain** | `127.0.0.1.nip.io` | Real domain (e.g., `aihub.company.com`) |
| **SSL Certificates** | Self-signed (mkcert) | Let's Encrypt (trusted, auto-renewal) |
| **Server** | Local machine | Dedicated server/VM |
| **Superuser Auth** | Enabled (for testing) | Disabled (Azure AD only) |
| **Data Backups** | Not required | Critical |
| **Monitoring** | Optional | Recommended |
| **Use Case** | Testing, demos | Production workloads |

## Prerequisites

### Server Requirements

::: code-group

```txt [CPU Variant]
- 32 GB RAM minimum (64 GB recommended)
- 100 GB free disk space minimum (500 GB+ for production data)
- Ubuntu 22.04 or 24.04 LTS (recommended)
- Public IPv4 address
- Open ports: 80 (HTTP), 443 (HTTPS)
```

```txt [GPU Variant]
- 64 GB RAM minimum (128 GB recommended)
- 500 GB free disk space minimum (1 TB+ for models and data)
- Ubuntu 22.04 or 24.04 LTS (recommended)
- NVIDIA GPU with 24+ GB VRAM (A100, H100, RTX 6000 Ada, etc.)
- NVIDIA drivers installed (version 525+)
- NVIDIA Container Toolkit installed
- Public IPv4 address
- Open ports: 80 (HTTP), 443 (HTTPS)
```

:::

### Domain and DNS

- **Domain Name**: Owned and controllable (e.g., `aihub.company.com`)
- **DNS Access**: Ability to create A records and CNAME records
- **Wildcard Support**: Required for subdomains (`*.aihub.company.com`)

### External Services

- **Azure AD / Entra ID** application registration
  - Required for production authentication
  - Superuser fallback NOT recommended for production
  - See [Azure AD Setup Guide](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)

- **LLM Provider API** (CPU variant only)
  - Azure OpenAI (recommended for enterprises)
  - Google Gemini (alternative)
  - API keys and endpoint URLs

::: info GPU Variant
The GPU variant includes self-hosted AI models, reducing external dependencies. External LLM API access is optional for fallback.
:::

### Email for Let's Encrypt

- Valid email address for Let's Encrypt certificate notifications
- Receives expiry warnings (certificates auto-renew, but notifications are useful for monitoring)

### Time Estimate

- **With prerequisites ready**: ~30 minutes
- **First-time setup**: ~60 minutes (includes DNS propagation, server setup, Azure AD configuration)

::: tip Production Deployment Checklist
Before starting, ensure you have: ✅ A server with Ubuntu 22.04/24.04, ✅ A registered domain name, ✅ DNS access for A/CNAME records, ✅ Azure AD app registration, ✅ Email for Let's Encrypt notifications.
:::

## Step 1: Server Preparation

### Install Docker and Docker Compose

::: code-group

```bash [Ubuntu 22.04 / 24.04]
# Remove old Docker installations
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

:::

### Install NVIDIA Drivers and Container Toolkit (GPU Variant Only)

::: code-group

```bash [GPU Variant - Ubuntu 22.04 / 24.04]
# Install NVIDIA drivers
sudo apt-get update
sudo apt-get install -y nvidia-driver-535

# Reboot to load the driver
sudo reboot

# After reboot, verify NVIDIA driver
nvidia-smi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

:::

### Configure Firewall

```bash
# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Verify rules
sudo ufw status
```

## Step 2: DNS Configuration

Configure DNS records for your domain to point to your server's public IP address.

### Required DNS Records

Replace `YOUR_SERVER_IP` with your server's public IPv4 address and `aihub.company.com` with your actual domain.

```dns
; A record for the main domain
aihub.company.com.        IN A     YOUR_SERVER_IP

; CNAME wildcard for all subdomains
*.aihub.company.com.      IN CNAME aihub.company.com.
```

### Required Subdomains

::: details Click to view all required subdomains

The platform uses these subdomains (automatically handled by wildcard):

- `openwebui.aihub.company.com` - Chat interface (primary entry point)
- `admin.aihub.company.com` - Admin interface
- `api.aihub.company.com` - REST API
- `s3.aihub.company.com` - S3 object storage
- `phoenix.aihub.company.com` - AI observability
- `dagster.aihub.company.com` - Pipeline orchestration
- `attu.aihub.company.com` - Vector database UI
- `litellm.aihub.company.com` - LLM proxy

:::

### Verify DNS Propagation

Wait for DNS propagation (usually 5-60 minutes):

```bash
# Check A record
nslookup aihub.company.com

# Check wildcard CNAME
nslookup openwebui.aihub.company.com
```

Both should return your server's IP address.

::: warning DNS Propagation
Do not proceed until DNS is fully propagated. Let's Encrypt will fail if it cannot reach your server via the configured domain.
:::

## Step 3: Clone the Repository

SSH into your server and clone the AI Hub repository:

```bash
# Create deployment directory (recommended: /opt)
sudo mkdir -p /opt/aihub
sudo chown $USER:$USER /opt/aihub

# Clone repository
cd /opt
git clone https://github.com/bbvch-ai/aihub-core.git aihub
cd aihub
```

::: tip Version Control
For production, consider checking out a specific stable tag instead of using `main`:
```bash
git checkout tags/v0.254.16  # Example: use latest stable tag
```
:::

## Step 4: Configure Environment Variables

Create a `.env` file with production-grade configuration.

### Generate the .env File

Start by copying the production template:

```bash
cp .env.prod .env
```

### Essential Configuration

Edit the `.env` file with your production values:

::: code-group

```env [CPU Variant]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="INFO"           # Use INFO for production (not DEBUG)
ENV="prod"
DOMAIN="aihub.company.com"  # Your actual domain

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-production-azure-client-id"
OAUTH_CLIENT_SECRET="your-production-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="$(openssl rand -hex 16)"

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="$(openssl rand -hex 32)"

# =============================================================================
# SUPERUSER CONFIGURATION - DISABLED IN PRODUCTION
# =============================================================================

SUPERUSER_ENABLED="False"  # CRITICAL: Disable in production

# =============================================================================
# AI MODEL ACCESS
# =============================================================================

# Azure OpenAI (recommended for production)
AZURE_OPENAI_BASE_URL="https://your-instance.openai.azure.com"
AZURE_OPENAI_KEY="your-production-azure-openai-key"

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="$(openssl rand -hex 32)"  # Strong password

MONGO_USERNAME="admin"
MONGO_PASSWORD="$(openssl rand -hex 32)"  # Strong password
# Note: Update connection string with same password (internal Docker network)
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@mongodb:27017/"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="$(openssl rand -hex 32)"
S3_STORAGE_URL_SIGNING_SECRET="$(openssl rand -hex 32)"

# Internal endpoint (Docker network)
S3_STORAGE_ENDPOINT="http://seaweedfs-s3:9000"

# Public endpoint (browser access) - matches DOMAIN
S3_STORAGE_PUBLIC_ENDPOINT="https://s3.aihub.company.com"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="$(openssl rand -hex 32)"
LITELLM_MASTER_KEY="$(openssl rand -hex 32)"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="$(openssl rand -hex 32)"
PHOENIX_SECRET="$(openssl rand -hex 32)"
NATS_TOKEN="$(openssl rand -hex 32)"
MILVUS_DIMENSION="3072"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# TRAEFIK & SSL CONFIGURATION
# =============================================================================

# Let's Encrypt email (for certificate expiry notifications)
ACME_EMAIL="admin@company.com"

# Admin dashboard access (use htpasswd to generate)
ADMIN_PASSWORD_HASH="$(htpasswd -nb admin your-admin-password)"

# =============================================================================
# AZURE AD GROUP RESTRICTIONS (OPTIONAL)
# =============================================================================

# Restrict access to specific Azure AD groups
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
ATTU_OAUTH_ALLOWED_GROUPS="AIHubAdmin"

# =============================================================================
# OBSERVABILITY
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# Optional: Send traces to cloud observability (SignOz, Datadog, etc.)
OTEL_CLOUD_ENDPOINT=""
OTEL_CLOUD_HEADERS=""

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search functionality
```

```env [GPU Variant]
# =============================================================================
# BASIC PLATFORM CONFIGURATION
# =============================================================================

LOG_LEVEL="INFO"           # Use INFO for production (not DEBUG)
ENV="prod"
DOMAIN="aihub.company.com"  # Your actual domain

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

# OAuth2 Configuration (from Azure AD App Registration)
OAUTH_CLIENT_ID="your-production-azure-client-id"
OAUTH_CLIENT_SECRET="your-production-azure-client-secret"
OAUTH_AUTHORITY_URL="https://login.microsoftonline.com/your-tenant-id"
OAUTH_PROVIDER_NAME="azure"
OAUTH_TENANT_ID="your-tenant-id"
OAUTH_COOKIE_SECRET="$(openssl rand -hex 16)"

# Open WebUI Signing Secret
AUTH_OPEN_WEBUI_SIGNING_SECRET="$(openssl rand -hex 32)"

# =============================================================================
# SUPERUSER CONFIGURATION - DISABLED IN PRODUCTION
# =============================================================================

SUPERUSER_ENABLED="False"  # CRITICAL: Disable in production

# =============================================================================
# AI MODEL ACCESS
# =============================================================================

# HuggingFace (required for GPU model downloads)
HUGGINGFACE_API_KEY="your-huggingface-token"

# Optional: External providers as fallback
AZURE_OPENAI_BASE_URL=""
AZURE_OPENAI_KEY=""

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

POSTGRES_USER="admin"
POSTGRES_PASSWORD="$(openssl rand -hex 32)"  # Strong password

MONGO_USERNAME="admin"
MONGO_PASSWORD="$(openssl rand -hex 32)"  # Strong password
# Note: Update connection string with same password (internal Docker network)
MONGO_CONNECTION_STRING="mongodb://admin:same-mongo-password@mongodb:27017/"

# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

S3_STORAGE_ACCESS_KEY="admin"
S3_STORAGE_SECRET_KEY="$(openssl rand -hex 32)"
S3_STORAGE_URL_SIGNING_SECRET="$(openssl rand -hex 32)"

# Internal endpoint (Docker network)
S3_STORAGE_ENDPOINT="http://seaweedfs-s3:9000"

# Public endpoint (browser access) - matches DOMAIN
S3_STORAGE_PUBLIC_ENDPOINT="https://s3.aihub.company.com"

# =============================================================================
# LITELLM CONFIGURATION
# =============================================================================

LITELLM_UI_USERNAME="admin"
LITELLM_UI_PASSWORD="$(openssl rand -hex 32)"
LITELLM_MASTER_KEY="$(openssl rand -hex 32)"
LITE_LLM_PROXY_API_KEY="same-as-litellm-master-key"

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

JUPYTER_TOKEN="$(openssl rand -hex 32)"
PHOENIX_SECRET="$(openssl rand -hex 32)"
NATS_TOKEN="$(openssl rand -hex 32)"
MILVUS_DIMENSION="3072"
DOCLING_API_TIMEOUT="600"
DOCLING_PIPELINE_TYPE="vlm"

# =============================================================================
# TRAEFIK & SSL CONFIGURATION
# =============================================================================

# Let's Encrypt email (for certificate expiry notifications)
ACME_EMAIL="admin@company.com"

# Admin dashboard access (use htpasswd to generate)
ADMIN_PASSWORD_HASH="$(htpasswd -nb admin your-admin-password)"

# =============================================================================
# AZURE AD GROUP RESTRICTIONS (OPTIONAL)
# =============================================================================

# Restrict access to specific Azure AD groups
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
ATTU_OAUTH_ALLOWED_GROUPS="AIHubAdmin"

# =============================================================================
# OBSERVABILITY
# =============================================================================

OTEL_ENABLED="true"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

# Optional: Send traces to cloud observability (SignOz, Datadog, etc.)
OTEL_CLOUD_ENDPOINT=""
OTEL_CLOUD_HEADERS=""

# =============================================================================
# OPTIONAL INTEGRATIONS
# =============================================================================

JINA_API_KEY=""  # For web search functionality
```

:::

### Generate Random Secrets

Generate strong secrets for production:

```bash
# For most secrets (64 characters)
openssl rand -hex 32

# For shorter secrets like OAUTH_COOKIE_SECRET (32 characters)
openssl rand -hex 16

# For admin password hash (htpasswd required)
htpasswd -nb admin your-admin-password
```

Replace all `$(openssl rand -hex XX)` placeholders with generated values.

### Validate Configuration

Ensure all placeholders are replaced and sensitive values are secure:

```bash
# Check for unreplaced placeholders
grep -n "your-\|REPLACE_WITH_\|\$(openssl\|\$(htpasswd" .env

# Verify no accidental exposure (should be -rw------- or 600)
ls -la .env

# Secure the .env file
chmod 600 .env
```

### Store Credentials Securely

::: danger Credential Security
- **Do NOT commit `.env` to version control** (add to `.gitignore`)
- Store credentials in a password manager (1Password, Bitwarden, Azure Key Vault)
- Document secret rotation procedures
- Enable audit logging for credential access
:::

## Step 5: Configure Azure AD Redirect URIs

Update your Azure AD app registration with production redirect URIs.

### Add Redirect URIs

In the [Azure Portal](https://portal.azure.com/):

1. Navigate to **Azure Active Directory**  **App registrations**
2. Select your AI Hub application
3. Go to **Authentication**  **Platform configurations**  **Web**
4. Add these redirect URIs (replace `aihub.company.com` with your domain):

```
https://openwebui.aihub.company.com/oauth/oidc/callback
https://admin.aihub.company.com/oauth2/callback
https://dagster.aihub.company.com/oauth2/callback
https://attu.aihub.company.com/oauth2/callback
https://s3.aihub.company.com/oauth2/callback
https://litellm.aihub.company.com/oauth2/callback
```

5. Click **Save**

### Assign User Roles

1. Go to **Enterprise applications** in Azure AD
2. Find your AI Hub application
3. Click **Users and groups**
4. Add users/groups and assign roles:
   - `AIHubUser` - Standard users
   - `AIHubAdmin` - Administrators
   - `AIHubSuperuser` - Platform superusers (use sparingly)

## Step 6: Launch the Platform

Start all AI Hub services with Docker Compose:

::: code-group

```bash [CPU Variant - Latest (Stable)]
docker compose -f docker-compose.latest.yml up -d
```

```bash [CPU Variant - Nightly (Bleeding Edge)]
docker compose -f docker-compose.nightly.yml up -d
```

```bash [GPU Variant - Latest (Stable)]
docker compose -f docker-compose.latest.gpu.yml up -d
```

```bash [GPU Variant - Nightly (Bleeding Edge)]
docker compose -f docker-compose.nightly.gpu.yml up -d
```

:::

::: tip Choosing Between Latest and Nightly
- **`latest`**: Stable releases, thoroughly tested, recommended for production
- **`nightly`**: Latest features, cutting-edge, may have bugs, suitable for staging/development
:::

### Monitor Startup Progress

Watch services initialize and Let's Encrypt certificate generation:

::: code-group

```bash [CPU Variant - Latest]
docker compose -f docker-compose.latest.yml logs -f
```

```bash [CPU Variant - Nightly]
docker compose -f docker-compose.nightly.yml logs -f
```

```bash [GPU Variant - Latest]
docker compose -f docker-compose.latest.gpu.yml logs -f
```

```bash [GPU Variant - Nightly]
docker compose -f docker-compose.nightly.gpu.yml logs -f
```

:::

**Initial Startup Time:**
- **CPU Variant**: 5-10 minutes (includes Let's Encrypt challenge)
- **GPU Variant**: 20-40 minutes (includes model downloads on first start)

Look for log message: `Certificate obtained successfully` from Traefik.

Press `Ctrl+C` to stop following logs. Services continue running in the background.

### Check Service Status

Verify all services are healthy:

::: code-group

```bash [Latest (CPU/GPU)]
docker compose -f docker-compose.latest.yml ps
```

```bash [Nightly (CPU/GPU)]
docker compose -f docker-compose.nightly.yml ps
```

:::

All services should show `healthy` or `running` status.

## Step 7: Verify Deployment

### Check SSL Certificates

Visit your platform in a browser:

```
https://openwebui.aihub.company.com
```

**Expected:**
-  Green padlock in browser (valid SSL certificate)
-  Certificate issued by "Let's Encrypt"
-  No certificate warnings

If you see certificate errors, check:
- DNS is correctly configured and propagated
- Ports 80 and 443 are open in firewall
- `DOMAIN` in `.env` matches your actual domain
- Traefik logs: `docker compose -f docker-compose.latest.yml logs traefik`

### Verify All Services

| Service | URL | Expected Result |
|---------|-----|----------------|
| **Open WebUI** | https://openwebui.aihub.company.com | Login page appears |
| **Admin UI** | https://admin.aihub.company.com | Admin dashboard loads |
| **API Docs** | https://api.aihub.company.com/docs | Swagger UI loads |
| **Phoenix** | https://phoenix.aihub.company.com | Phoenix traces UI loads |
| **Dagster** | https://dagster.aihub.company.com | Dagster pipeline UI loads |

### Test API Health

```bash
curl https://api.aihub.company.com/health
```

Should return: `{"status":"healthy"}`

### Test Azure AD Authentication

1. Navigate to `https://openwebui.aihub.company.com`
2. Click **"Sign in with Azure AD"**
3. Authenticate with your Azure credentials
4. Verify you're redirected back and logged in

::: warning Authentication Errors
If authentication fails:
- Verify redirect URIs in Azure AD match exactly
- Check `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_TENANT_ID` in `.env`
- Review OpenWebUI logs: `docker compose logs openwebui`
:::

## Step 8: Production Hardening

### Verify Superuser is Disabled

```bash
grep SUPERUSER_ENABLED .env
```

Should show: `SUPERUSER_ENABLED="False"`

::: danger Security Risk
Never enable superuser authentication in production. It bypasses Azure AD and creates a security backdoor.
:::

### Configure Azure AD Group Restrictions

Limit access to administrative interfaces:

```bash
# In .env file
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
ATTU_OAUTH_ALLOWED_GROUPS="AIHubAdmin"
```

Restart services after changes:

```bash
docker compose -f docker-compose.latest.yml restart
```

### Set Up Automated Backups

::: details Click to view backup script and setup instructions

Create a backup script for data volumes:

```bash
#!/bin/bash
# /opt/aihub/backup.sh

BACKUP_DIR="/backup/aihub"
DATE=$(date +%Y%m%d_%H%M%S)

# Stop services (optional - for consistent backups)
cd /opt/aihub
# docker compose -f docker-compose.latest.yml down

# Backup data volumes
mkdir -p $BACKUP_DIR
tar czf $BACKUP_DIR/aihub-volumes-$DATE.tar.gz .docker-volumes/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "aihub-volumes-*.tar.gz" -mtime +7 -delete

# Restart services (if stopped)
# docker compose -f docker-compose.latest.yml up -d

echo "Backup completed: $BACKUP_DIR/aihub-volumes-$DATE.tar.gz"
```

Make executable and schedule with cron:

```bash
chmod +x /opt/aihub/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /opt/aihub/backup.sh >> /var/log/aihub-backup.log 2>&1
```

:::

### Configure Log Retention

Docker Compose files include log rotation settings. Verify:

```bash
# Check log driver configuration in docker-compose file
grep -A 3 "logging:" docker-compose.latest.yml
```

Should show:
```yaml
logging:
  driver: json-file
  options:
    max-size: 10m
    max-file: 2
```

### Set Up Monitoring

Consider integrating with monitoring solutions:

- **Prometheus + Grafana**: Resource monitoring (CPU, RAM, disk)
- **Uptime Robot**: Availability monitoring
- **Phoenix Cloud**: AI observability (configure `OTEL_CLOUD_ENDPOINT`)
- **Azure Monitor**: Integration with Azure services

### Document Admin Credentials

Create a secure document with:
- `.env` file location
- All secrets and tokens (store in password manager)
- Azure AD application details
- Backup restoration procedures
- Emergency contact information

## Common Operations

### Update Platform

Pull latest images and restart:

::: code-group

```bash [Latest (CPU/GPU)]
cd /opt/aihub
docker compose -f docker-compose.latest.yml pull
docker compose -f docker-compose.latest.yml up -d
```

```bash [Nightly (CPU/GPU)]
cd /opt/aihub
docker compose -f docker-compose.nightly.yml pull
docker compose -f docker-compose.nightly.yml up -d
```

:::

### View Logs

::: code-group

```bash [All Services]
docker compose -f docker-compose.latest.yml logs -f
```

```bash [Specific Service]
docker compose -f docker-compose.latest.yml logs -f api
```

```bash [Last 100 Lines]
docker compose -f docker-compose.latest.yml logs --tail=100
```

:::

### Restart a Service

```bash
docker compose -f docker-compose.latest.yml restart api
```

### Restore from Backup

```bash
# Stop services
cd /opt/aihub
docker compose -f docker-compose.latest.yml down

# Remove existing volumes
rm -rf .docker-volumes/

# Extract backup
tar xzf /backup/aihub/aihub-volumes-YYYYMMDD_HHMMSS.tar.gz

# Restart services
docker compose -f docker-compose.latest.yml up -d
```

### Emergency Stop

```bash
cd /opt/aihub
docker compose -f docker-compose.latest.yml down
```

### Complete Reset (DESTRUCTIVE)

::: danger Data Loss
This deletes ALL data, including user accounts, knowledge bases, and configurations.
:::

```bash
docker compose -f docker-compose.latest.yml down -v
rm -rf .docker-volumes
docker compose -f docker-compose.latest.yml up -d
```

## Next Steps

Your production AI Hub is now running!

### User Onboarding

1. **Assign Roles**: Add users to Azure AD groups (`AIHubUser`, `AIHubAdmin`)
2. **Create Knowledge Bases**: Upload organizational documents
3. **Configure Models**: Set up additional LLM providers in Admin UI
4. **Train Users**: Provide documentation and training sessions

### Monitoring and Maintenance

1. **Daily**: Check logs for errors (`docker compose logs`)
2. **Weekly**: Verify backups are running and restorable
3. **Monthly**: Review resource usage (CPU, RAM, disk)
4. **Quarterly**: Update platform (`docker compose pull && up -d`)

### Learn More

- **User Documentation**: [Coming soon]
- **Architecture Overview**: [docs/2_platform/2_architecture](../../2_architecture/index.en.md)
- **API Reference**: https://api.aihub.company.com/docs
- **Support**: [GitHub Issues](https://github.com/bbvch-ai/aihub-core/issues)
