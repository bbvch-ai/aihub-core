# AI-Hub Deployment Configurations

This directory contains the generated Docker Compose configurations for deploying the AI-Hub platform in various environments. The platform supports multiple deployment scenarios, each optimized for specific use cases ranging from local development to production deployment.

## Overview

AI-Hub provides **5 deployment configurations**, each available in both **CPU** and **GPU** variants:

| Configuration | Use Case | 1st Party Services | Traefik | Port Exposure |
|---------------|----------|-------------------|---------|---------------|
| **dev** | Active development | Not included | None | Direct to localhost |
| **local** | Local testing with SSL | Latest tagged | Local SSL | Through Traefik |
| **build** | Source code development | Built from source | Local SSL | Through Traefik |
| **latest** | Production deployment | Latest tagged | Let's Encrypt | Through Traefik |
| **nightly** | Pre-production testing | Nightly tagged | Let's Encrypt | Through Traefik |

## Configuration Details

### 1. **dev** - Development Environment

**Purpose**: For active development where you run 1st party services (API, Web, Dagster, Agents) directly from your IDE or command line.

**Characteristics**:
- ❌ **No 1st party services** in Docker Compose
- ❌ **No Traefik** reverse proxy
- ✅ All infrastructure services (databases, message queues, etc.)
- ✅ All ports exposed directly to localhost
- ✅ Fastest startup and shutdown
- ✅ Minimal resource usage

**When to use**:
- Developing backend services (aihub_api, aihub_agents, aihub_pipeline)
- Debugging and testing with IDE debugger
- Rapid iteration without rebuilding containers

**Start command**:
```bash
# CPU variant
docker compose -f docker-compose.dev.yml up -d

# GPU variant
docker compose -f docker-compose.gpu.dev.yml up -d
```

---

### 2. **local** - Local Testing Environment

**Purpose**: Test the complete platform locally with SSL certificates before deploying to production.

**Characteristics**:
- ✅ **Latest tagged** 1st party services from container registry
- ✅ **Traefik** with local SSL certificates (mkcert)
- ✅ Access via `*.127.0.0.1.nip.io` domains
- ✅ Production-like environment on your machine
- ✅ All services behind SSL/TLS

**When to use**:
- Testing the complete platform integration
- Validating deployment configurations
- QA and user acceptance testing locally
- Demonstrating features to stakeholders

**Prerequisites**:
```bash
# Generate local SSL certificates (one-time setup)
make local-cert
```

**Start command**:
```bash
# CPU variant
docker compose -f docker-compose.local.yml up -d

# GPU variant
docker compose -f docker-compose.gpu.local.yml up -d
```

**Access points**:
- Main Web Interface: https://127.0.0.1.nip.io
- OpenWebUI: https://openwebui.127.0.0.1.nip.io
- Dagster: https://dagster.127.0.0.1.nip.io
- LiteLLM: https://litellm.127.0.0.1.nip.io

---

### 3. **build** - Source Build Environment

**Purpose**: Build and test 1st party services from source code, identical to local but with source builds.

**Characteristics**:
- ✅ **Build from source** (using `localbuild` tag)
- ✅ **Traefik** with local SSL certificates (mkcert)
- ✅ Same access patterns as `local`
- ⚠️ Longer startup time due to building
- ✅ Tests your local code changes end-to-end

**When to use**:
- Testing code changes in a containerized environment
- Validating Dockerfiles and build processes
- End-to-end testing of uncommitted changes
- Debugging container-specific issues

**Prerequisites**:
```bash
# Generate local SSL certificates (one-time setup)
make local-cert
```

**Start command**:
```bash
# CPU variant
docker compose -f docker-compose.build.yml up -d --build

# GPU variant
docker compose -f docker-compose.gpu.build.yml up -d --build
```

---

### 4. **latest** - Production Deployment

**Purpose**: Production deployment using the latest stable release.

**Characteristics**:
- ✅ **Latest tagged** 1st party services (stable releases)
- ✅ **Traefik** with Let's Encrypt SSL certificates
- ✅ Automatic SSL certificate management
- ✅ Production-ready configuration
- ✅ Optimized for stability and reliability

**When to use**:
- Production deployments
- Stable customer installations
- Public-facing instances

**Prerequisites**:
- Public domain name configured
- DNS pointing to your server
- Ports 80 and 443 accessible from internet

**Start command**:
```bash
# CPU variant
docker compose -f docker-compose.latest.yml up -d

# GPU variant
docker compose -f docker-compose.gpu.latest.yml up -d
```

---

### 5. **nightly** - Pre-Production Testing

**Purpose**: Test the latest nightly builds before promoting to production.

**Characteristics**:
- ✅ **Nightly tagged** 1st party services (bleeding edge)
- ✅ **Traefik** with Let's Encrypt SSL certificates
- ⚠️ May contain experimental features
- ⚠️ Less stable than `latest`
- ✅ Early access to new capabilities

**When to use**:
- Staging environments
- Testing upcoming features
- Pre-production validation
- Beta testing with customers

**Prerequisites**:
- Public domain name configured
- DNS pointing to your server
- Ports 80 and 443 accessible from internet

**Start command**:
```bash
# CPU variant
docker compose -f docker-compose.nightly.yml up -d

# GPU variant
docker compose -f docker-compose.gpu.nightly.yml up -d
```

---

## GPU Variants

All configurations support GPU acceleration through CUDA-enabled containers. GPU variants include:

- **llama.cpp**: CUDA-enabled LLM inference
- **Speaches**: GPU-accelerated speech processing
- Additional ML services with GPU support

**System requirements**:
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit installed
- Docker configured with GPU access

---

## Configuration Generation

All Docker Compose files are **generated** from Jinja2 templates to ensure consistency and reduce duplication.

**Source files**:
- `compose-config.yml` - Single source of truth for all configurations
- `templates/docker-compose.yml.j2` - Main template
- `templates/configs/` - Service-specific configuration templates

**Generation**:
```bash
# Generate all configurations
cd deployment
python generate_compose.py
```

**Generated files location**:
- Root directory: `docker-compose.{stage}.yml` and `docker-compose.gpu.{stage}.yml`
- This directory: `targets/docker-compose.{stage}.yml` (archive/reference)

---

## Key Differences Summary

### 1st Party Services (AI-Hub Components)

| Service | dev | local | build | latest | nightly |
|---------|-----|-------|-------|--------|---------|
| aihub_api | Manual | ✅ latest | 🔨 source | ✅ latest | 🌙 nightly |
| aihub_web | Manual | ✅ latest | 🔨 source | ✅ latest | 🌙 nightly |
| aihub_dagster | Manual | ✅ latest | 🔨 source | ✅ latest | 🌙 nightly |
| aihub_agents | Manual | ✅ latest | 🔨 source | ✅ latest | 🌙 nightly |

### Traefik Configuration

| Configuration | Traefik | SSL Certificates | Domain |
|---------------|---------|------------------|--------|
| dev | ❌ None | N/A | localhost |
| local | ✅ Local | mkcert (self-signed) | *.127.0.0.1.nip.io |
| build | ✅ Local | mkcert (self-signed) | *.127.0.0.1.nip.io |
| latest | ✅ Remote | Let's Encrypt | Your domain |
| nightly | ✅ Remote | Let's Encrypt | Your domain |

### Infrastructure Services

All configurations include the same infrastructure services:
- **Databases**: PostgreSQL (FerretDB), Valkey
- **Vector Store**: Milvus
- **Object Storage**: SeaweedFS
- **Observability**: Phoenix, OpenTelemetry
- **Message Queue**: NATS
- **AI Gateway**: LiteLLM, OpenWebUI

---

## Best Practices

1. **Development**: Use `dev` for active development
2. **Local testing**: Use `local` or `build` for end-to-end testing
3. **Staging**: Use `nightly` to test upcoming releases
4. **Production**: Use `latest` for stable deployments
5. **GPU acceleration**: Add `gpu.` prefix when GPU resources are available

---

## Troubleshooting

### Services not starting

```bash
# Check service health
docker compose -f docker-compose.{stage}.yml ps

# View logs
docker compose -f docker-compose.{stage}.yml logs -f {service_name}
```

### Port conflicts (dev configuration)

The `dev` configuration exposes many ports directly. Ensure no other services are using these ports.

### SSL certificate issues (local/build)

```bash
# Regenerate local certificates
make local-cert

# Verify mkcert installation
mkcert -version
```

### Let's Encrypt issues (latest/nightly)

- Verify DNS is correctly configured
- Ensure ports 80 and 443 are accessible
- Check Traefik logs: `docker logs traefik`

---

## Related Documentation

- [Main README](../README.md) - Complete developer guide
- [Infrastructure Documentation](../aihub_doc/docs/) - Detailed architecture documentation
- [Local Development Setup](../README.md#gear-codebase--dependency-setup) - Setting up your development environment