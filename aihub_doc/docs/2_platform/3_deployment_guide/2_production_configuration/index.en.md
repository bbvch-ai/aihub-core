---
title: Production configuration
---

# Production configuration

Configure environment variables, DNS, SSL certificates, and service settings for production deployment.

## Environment variables structure

Production deployments use a structured `.env` file organized into sections. Here's the complete structure:

### Basic platform configuration

```bash
# Environment and logging
LOG_LEVEL=info
ENV=prod

# API versioning
AIHUB_API_VERSION=dev
```

### Domain and DNS configuration

The platform routes services through subdomains. Your DNS needs records for six domains:

```bash
# Main domain (without protocol)
DOMAIN=aihub.example.com
```

Create A records or CNAMEs for these subdomains:
- `aihub.example.com` - main web interface
- `openwebui.aihub.example.com` - chat UI
- `dagster.aihub.example.com` - pipeline orchestration
- `datalake.aihub.example.com` - data lake console
- `datalake-api.aihub.example.com` - S3 API
- `traefik.aihub.example.com` - reverse proxy dashboard

All subdomains point to your server's public IP.

### SSL/TLS certificates

Traefik handles certificate provisioning through Let's Encrypt:

```bash
# Let's Encrypt configuration
ACME_EMAIL=admin@example.com
```

Ports 80 and 443 need internet access for ACME HTTP challenges. Let's Encrypt won't issue certificates without valid DNS records. Initial provisioning takes 1-2 minutes. Renewal happens automatically every 60 days.

### Authentication

Configure Azure AD OAuth2 for user authentication:

```bash
# Azure AD OAuth2
AUTH_IDENTITY_PROVIDER=azure
OAUTH_CLIENT_ID=<your-azure-ad-client-id>
OAUTH_CLIENT_SECRET=<your-azure-ad-client-secret>
OAUTH_TENANT_ID=<your-azure-ad-tenant-id>
OAUTH_AUTHORITY_URL=https://login.microsoftonline.com/<your-azure-ad-tenant-id>/v2.0

# Azure credentials (legacy variables that match OAuth values)
AZURE_CLIENT_ID=${OAUTH_CLIENT_ID}
AZURE_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
AZURE_TENANT_ID=${OAUTH_TENANT_ID}
```

See [authentication setup](../../11_access_management/1_authentication_setup/) for OAuth redirect URI configuration.

### Platform access

```bash
# Superuser configuration
SUPERUSER_ENABLED=true
SUPERUSER_NAME=Admin
SUPERUSER_EMAIL=admin@example.com
SUPERUSER_OID=<azure-ad-object-id-of-admin>
SUPERUSER_ROLE=admin
SUPERUSER_TOKEN=<generate-strong-random-token>

# Role management
AIHUB_CREATE_DEFAULT_ROLES=true

# Open WebUI integration
AUTH_ENABLE_API_ACCESS=true
AUTH_OPEN_WEBUI_SIGNING_SECRET=<generate-strong-random-secret>
```

Generate tokens with `openssl rand -hex 32` or `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.

### Service access control

Control which Azure AD groups can access Dagster and the data lake:

```bash
# Dagster pipeline orchestration dashboard
DAGSTER_OAUTH_ALLOWED_GROUPS="AIHubDeveloper"

# SeaweedFS data lake console
SEAWEEDFS_OAUTH_ALLOWED_GROUPS="AIHubDeveloper"
```

Both default to `AIHubDeveloper` if not specified. You can specify multiple groups separated by commas (e.g., `"AIHubDeveloper,AIHubAdmin"`). Users must have the corresponding app role assigned in Azure Enterprise Applications to access these services.

### Traefik admin

```bash
# Dashboard access
TRAEFIK_ADMIN_PASSWORD_HASH=<htpasswd-bcrypt-hash>
```

Generate the hash with `htpasswd -nbB admin your-password-here`. Copy the entire output including the "admin:" prefix.

### AI model access

Configure access to language models:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com

# LiteLLM proxy
LITELLM_MASTER_KEY=<generate-strong-random-key>
```

### Database configuration

```bash
# PostgreSQL
POSTGRES_USER=aihub
POSTGRES_PASSWORD=<generate-strong-password>

# MongoDB/FerretDB
MONGO_USERNAME=aihub
MONGO_PASSWORD=<generate-strong-password>
```

### Storage configuration

```bash
# SeaweedFS (S3-compatible storage)
MINIO_ROOT_USER=<generate-username>
MINIO_ROOT_PASSWORD=<generate-strong-password>
MINIO_URL_SIGNING_SECRET=<generate-strong-random-secret>

# Alternative variable names used by some services
S3_STORAGE_ACCESS_KEY=${MINIO_ROOT_USER}
S3_STORAGE_SECRET_KEY=${MINIO_ROOT_PASSWORD}
S3_STORAGE_URL_SIGNING_SECRET=${MINIO_URL_SIGNING_SECRET}
```

### Vector database

```bash
# Milvus
MILVUS_DIMENSION=3072  # Must match embedding model dimension
```

The dimension must match your embedding model:
- `text-embedding-3-large`: 3072
- `text-embedding-3-small`: 1536
- `text-embedding-ada-002`: 1536

Changing this after data ingestion requires reindexing all documents.

### Service endpoints

Internal service endpoints use Docker network DNS:

```bash
# Phoenix (observability)
PHOENIX_ENDPOINT=http://phoenix:6006

# Milvus (vector database)
MILVUS_URL=http://milvus-standalone:19530

# NATS (message broker)
NATS_ENDPOINT=nats://nats:4222

# Redis/Valkey (cache)
REDIS_URL=redis://valkey:6379

# LiteLLM proxy
LITE_LLM_PROXY_BASE_URL=http://litellm:4000
LITE_LLM_PROXY_API_KEY=${LITELLM_MASTER_KEY}

# MongoDB/FerretDB
MONGO_CONNECTION_STRING=mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@ferretdb:27017

# Storage (internal S3)
S3_STORAGE_ENDPOINT=http://seaweedfs-s3:9000

# Docling (document processing)
DOCLING_API_ENDPOINT=http://docling:5001
DOCLING_API_TIMEOUT=600
```

### Optional integrations

```bash
# Jina AI (web search and embeddings)
JINA_API_KEY=<your-jina-api-key>

# Jupyter Lab
JUPYTER_TOKEN=<generate-strong-token>
```

### Volume storage

```bash
# Docker volume root directory
VOLUME_ROOT=/srv/app
```

This directory contains all persistent data: PostgreSQL databases, MongoDB data, vector indices, object storage, and configuration files. Include it in your backup strategy.

## Configuration validation

Check for missing values before deployment:

```bash
# Find required variables
grep -E "^(DOMAIN|OAUTH_CLIENT_ID|SUPERUSER_TOKEN)=" .env

# Check for placeholder values
if grep -q "example.com\|your-.*\|<.*>" .env; then
  echo "Warning: Placeholder values detected in .env"
fi

# Test DNS resolution
for subdomain in "" "openwebui." "dagster." "datalake." "datalake-api."; do
  echo "Testing ${subdomain}${DOMAIN}..."
  dig +short "${subdomain}${DOMAIN}"
done
```

## Starting the production stack

Pull images and start services:

```bash
# Pull latest images
docker compose -f docker-compose.latest.yml pull

# Start all services
docker compose -f docker-compose.latest.yml up -d

# Monitor service health
docker compose -f docker-compose.latest.yml ps

# View logs
docker compose -f docker-compose.latest.yml logs -f
```

First deployment takes about 5 minutes: 1-2 minutes for Let's Encrypt certificates, 5-7 minutes for Docling model downloads (2GB), 30-60 seconds for database initialization. Subsequent starts take 30 seconds because certificates and models are cached.

## Health check verification

Verify services are running:

```bash
# Check service health
docker compose -f docker-compose.latest.yml ps | grep -E "(healthy|running)"

# Test web interface
curl -I https://${DOMAIN}/

# Test API
curl https://${DOMAIN}/api/v1/health

# Check Phoenix dashboard
curl -I https://${DOMAIN}/phoenix/
```

## Troubleshooting

### Services not starting

```bash
# Check container logs
docker compose -f docker-compose.latest.yml logs <service-name>

# Verify environment variables
docker compose -f docker-compose.latest.yml config | grep DOMAIN

# Check resources
df -h  # Disk space
free -h  # Memory
```

### SSL certificate issues

```bash
# View Traefik logs
docker compose -f docker-compose.latest.yml logs traefik | grep -i acme

# Check certificate storage
ls -lh /srv/app/traefik/acme.json

# Verify DNS
dig +short ${DOMAIN}
```

### Authentication failures

Check that Azure AD redirect URIs match exactly in the [authentication setup](../../11_access_management/1_authentication_setup/) guide. Verify `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET` are correct. Confirm `OAUTH_AUTHORITY_URL` uses the right tenant ID. Make sure users are assigned to the Azure AD application.

### DNS resolution issues

**Symptoms**: Authentication timeouts, OAuth callback failures, "Connection timed out" errors during login.

**Cause**: VM cannot resolve its own domain name. This typically happens when nameservers in `/etc/resolv.conf` are not in your subnet and block DNS requests.

**Diagnosis**:

```bash
# Test from the VM
dig +short ${DOMAIN}
curl -I https://${DOMAIN}

# Check nameserver configuration
cat /etc/resolv.conf
```

If `dig` returns your IP but `curl` times out, or if `dig` fails entirely, you have a DNS resolution issue.

**Solution**:

Test different nameservers to find one that works:

```bash
# Test with public nameservers
dig @8.8.8.8 ${DOMAIN}
dig @1.1.1.1 ${DOMAIN}
```

Update `/etc/resolv.conf` to use a working nameserver:

```bash
sudo nano /etc/resolv.conf
# Change to working nameserver (e.g., 8.8.8.8)
```

For persistent changes on Ubuntu/Debian with systemd-resolved:

```bash
sudo nano /etc/systemd/resolved.conf
# Set: DNS=8.8.8.8 8.8.4.4
sudo systemctl restart systemd-resolved
```

See [network requirements](../7_network_requirements/) for detailed DNS configuration guidance.

## Security hardening

After initial deployment:

1. Restrict Traefik dashboard access to admin IPs in firewall rules
2. Rotate `SUPERUSER_TOKEN`, database passwords, and API keys regularly
3. Configure log aggregation and retention ([auditing](../../12_auditing/))
4. Set up service failure alerts ([monitoring](../5_monitoring_and_alerting/))
5. Store encrypted backups of `.env` file securely

## Next steps

- [Authentication setup](../../11_access_management/1_authentication_setup/) - configure Azure AD OAuth redirect URIs
- [Network requirements](../7_network_requirements/) - firewall rules and connectivity
- [Monitoring and alerting](../5_monitoring_and_alerting/) - production observability
- [Backup and recovery](../4_backup_and_recovery/) - data protection
