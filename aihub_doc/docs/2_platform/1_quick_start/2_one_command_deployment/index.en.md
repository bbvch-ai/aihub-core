---
title: One-Command Deployment
---

# One-Command Deployment: Launch Your AI Platform

The Swiss AI Hub platform deploys with a single Docker Compose command. This streamlined process gets your complete AI
infrastructure running in minutes, not hours.

## Quick Install

Run a single command to download, extract, and set up the platform:

```bash
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash
```

The installer auto-detects GPU hardware, downloads the correct release bundle, and generates all secrets. Afterwards,
edit `.env` and run `docker compose up -d`.

| Flag                | Default          | Description               |
| ------------------- | ---------------- | ------------------------- |
| `--version VERSION` | latest           | Pin to a specific release |
| `--gpu`             | auto-detect      | Force GPU bundle          |
| `--cpu`             | auto-detect      | Force CPU-only bundle     |
| `--dir PATH`        | `./swiss-ai-hub` | Installation directory    |
| `--help`            |                  | Show usage                |

**Examples:**

```bash
# Install with GPU bundle to a custom directory
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --gpu --dir /opt/aihub

# Pin a specific version
curl -fsSL https://raw.githubusercontent.com/bbvch-ai/aihub-core/main/install.sh | bash -s -- --version v0.269.2
```

**Upgrading:** Run the installer again with the same `--dir`. It detects the existing installation, backs up your
`.env`, replaces bundle files, restores `.env`, and reports any new environment variables added in the release.

______________________________________________________________________

## Deployment Overview

::: tip Two Deployment Options
The Swiss AI Hub supports two deployment modes. Follow the same steps for both, using the appropriate commands for your
deployment type:

- **Production Deployment**: Deploy to a server with a real domain name (e.g., `aihub.yourcompany.com`)

  - Uses the CPU or GPU release bundle from GitHub Releases
  - Uses Let's Encrypt for automatic SSL certificates
  - Requires DNS configuration pointing to your server

- **Local Deployment**: Run on your local machine for development/testing

  - Uses `docker-compose.local.yml` from the repository
  - Uses self-signed SSL certificates (mkcert)
  - Uses `127.0.0.1.nip.io` domain (automatically resolves to localhost)

Each step below shows commands for both deployment types. Simply follow the commands that match your chosen deployment
mode.
:::

______________________________________________________________________

## Step 1: Get Deployment Files

**For Production:**

Download the latest release bundle from [GitHub Releases](https://github.com/bbvch-ai/aihub-core/releases). Each release
provides two self-contained bundles:

- `swissaihub-<version>.tar.gz` — CPU-only deployment
- `swissaihub-<version>-gpu.tar.gz` — GPU-enabled deployment (includes vLLM, GPU-accelerated inference)

```bash
# Set the version you want to deploy
VERSION="v0.266.0"  # Replace with the desired version

# Download and extract the release bundle (CPU example)
mkdir swiss-ai-hub && cd swiss-ai-hub
curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}.tar.gz" \
  | tar -xz

# For GPU-enabled deployment, use this instead:
# curl -L "https://github.com/bbvch-ai/aihub-core/releases/download/${VERSION}/swissaihub-${VERSION}-gpu.tar.gz" \
#   | tar -xz
```

The release bundle contains everything needed to deploy: `docker-compose.yml`, all service configuration files, an
`.env.template`, and the `setup-env.sh` script.

**For Local Deployment:**

```bash
# Clone the repository
git clone https://github.com/bbvch-ai/aihub-core.git
cd aihub-core

# Generate SSL certificates with mkcert
mkcert -install  # Install local CA (only needed once)
make local-cert
```

::: tip What is nip.io?
The `*.127.0.0.1.nip.io` domain automatically resolves to your localhost (127.0.0.1), providing wildcard DNS resolution
without needing to modify your hosts file. This allows subdomain-based routing in local development.
:::

______________________________________________________________________

## Step 2: Configure Environment Variables

### Generate Environment Configuration

**For Production (release bundle):**

The release bundle includes a `setup-env.sh` script that generates a `.env` file from the included `.env.template`. It
automatically creates unique secrets for all database passwords, tokens, and signing keys:

```bash
# Generate .env with auto-generated secrets
./setup-env.sh
```

::: details What does setup-env.sh do?
The script reads `.env.template` and replaces all `REPLACE_WITH_*` placeholders with cryptographically secure random
values. Each placeholder gets its own unique secret. The script requires only `openssl` and `bash` — no Python or other
dependencies needed.

```bash
# Options:
./setup-env.sh                              # Default: .env.template → .env
./setup-env.sh -t custom.template -o out.env  # Custom paths
./setup-env.sh --force                      # Overwrite existing .env
```
:::

**For Local Deployment:**

```bash
cp .env.dev .env
```

### Configure Remaining Values

After generating your `.env` file, review it and fill in the values that require manual configuration:

**Critical Values to Replace:**

1. **Domain** — Set `DOMAIN` to your production domain (e.g., `aihub.yourcompany.com`) or `127.0.0.1.nip.io` for local
   testing

2. **Authentication Values** (from Prerequisites):

   - `REPLACE_WITH_YOUR_CLIENT_ID` → Your Azure App Registration Client ID
   - `REPLACE_WITH_YOUR_CLIENT_SECRET` → Your Azure App Registration Client Secret
   - `REPLACE_WITH_YOUR_TENANT_ID` → Your Azure Tenant ID

3. **AI Model Access** (Swiss LLM Cloud — required for non-GPU deployments):

   - `REPLACE_WITH_SWISS_LLM_CLOUD_URL` → Your Swiss LLM Cloud text generation endpoint
   - `REPLACE_WITH_SWISS_LLM_CLOUD_KEY` → Your Swiss LLM Cloud API key
   - Configure the remaining endpoint pairs for embedding, reranking, whisper, and OCR

4. **Expert Escalation** (optional — for expert-in-the-loop features):

   - `REPLACE_WITH_TEAMS_CHANNEL_ID` → Your Teams channel ID (format: `19:xxx@thread.tacv2`)
   - `REPLACE_WITH_TEAMS_TENANT_ID` → Your Azure AD tenant ID
   - `REPLACE_WITH_TEAMS_BOT_ID` → Your Azure Bot Service application ID

::: info Simplified Configuration
Internal service endpoints (like database URLs, message queues, etc.) are hardcoded in the Docker Compose files. You
only need to configure credentials and external service connections. All database passwords, tokens, and signing keys
are auto-generated by `setup-env.sh`.
:::

### Environment Validation

Before deployment, verify your configuration:

```bash
# Check for placeholder values that still need replacement
grep -n "REPLACE_WITH" .env
```

This should return no results if all placeholders are replaced.

______________________________________________________________________

## Step 3: Deploy the Platform

### Launch All Services

Deploy the complete platform with one command:

**For Production (release bundle):**

```bash
docker compose up -d
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
docker compose logs -f

# Check service health status
docker compose ps
```

**Expected Services:** The platform includes these core services:

- **Web Interface** (aihub-web)
- **API** (aihub-api)
- **Authentication** (auth services)
- **Databases** (FerretDB, PostgreSQL, Valkey)
- **Vector Database** (Milvus)
- **LLM Proxy** (LiteLLM)
- **Document Processing** (MinerU)
- **Observability** (Langfuse)
- **Message Queue** (NATS)
- **Storage** (SeaweedFS)

### Wait for Service Initialization

Initial startup takes 3-5 minutes while services initialize. All services should show "healthy" status:

```bash
# Wait for healthy status
docker compose ps --format "table {{.Name}}\t{{.Status}}"
```

______________________________________________________________________

## Step 4: Verify Successful Deployment

### Access the Platform

1. **Make sure your User that you test with has the roles "AIHubAdmin" and "AIHubSysAdmin" assigned in the Azure
   Enterprise Application**

2. **Web Interface:**

   - Production: `https://your-domain.com`

3. **Expected Login Flow:**

   - Redirects to Azure authentication
   - After login, returns to AI-Hub interface
   - Should see the main dashboard
