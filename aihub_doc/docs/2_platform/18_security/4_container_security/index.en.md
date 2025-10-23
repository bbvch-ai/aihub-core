---
title: Container Security
index: 4
---

# Container Security

The Swiss AI-Hub uses containerization (Docker) for all services. This document covers currently implemented container security controls and recommended production hardening measures.

## Implementation Status

| Security Control | Status | Implementation |
|-----------------|--------|----------------|
| Non-Root User Execution | ✅ Implemented | All `Dockerfile` files |
| Multi-Stage Builds | ✅ Implemented | All `Dockerfile` files |
| Minimal Base Images | ✅ Implemented | `python:3.13-slim` |
| Seccomp Profiles | ⚠️ Recommended | Not configured |
| AppArmor/SELinux | ⚠️ Recommended | Not configured |
| Capability Dropping | ⚠️ Recommended | Not configured |
| Read-Only Root Filesystem | ⚠️ Recommended | Not configured |
| Network Segmentation | ⚠️ Recommended | Basic (single network) |

## Currently Implemented Controls

### Non-Root User Execution

**Implementation**: All `Dockerfile` files (example: `aihub_api/Dockerfile:62-97`)

Every container runs as a non-privileged user:

**Configuration**:
- User created with UID 1000, GID 1000 (non-privileged)
- Container switches to this user before startup (`USER $USERNAME`)
- All application processes run without root privileges

**Security Benefit**:
- ✅ Limits damage from container escape vulnerabilities
- ✅ Prevents privilege escalation within container
- ✅ Reduces attack surface for kernel exploits
- ✅ Aligns with principle of least privilege

**Verification**:
```bash
# Check which user a container runs as
docker exec <container-name> whoami
# Should output: user

# Check UID
docker exec <container-name> id
# Should output: uid=1000(user) gid=1000(user)
```

### Multi-Stage Builds

**Implementation**: All `Dockerfile` files (example: `aihub_api/Dockerfile:1-105`)

Containers use multi-stage builds to separate build and runtime environments:

**Build Stage** (lines 1-45):
- Installs build tools (gcc, make, git, etc.)
- Compiles Python dependencies
- Builds application artifacts
- Larger image size acceptable here

**Runtime Stage** (lines 46-105):
- Starts from clean base image
- Copies only necessary artifacts from build stage
- Excludes build tools and intermediate files
- Significantly smaller final image

**Security Benefits**:
- ✅ Removes build tools that could be exploited
- ✅ Reduces attack surface (fewer binaries, libraries)
- ✅ Smaller image size (faster deployments, less storage)
- ✅ Separates build and runtime dependencies

**Example Pattern**:
```dockerfile
# Build stage
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y build-essential git
COPY . /app
WORKDIR /app
RUN poetry install

# Runtime stage
FROM python:3.13-slim AS runtime
COPY --from=builder /app/.venv /app/.venv
# No build tools present in final image
```

### Minimal Base Images

**Implementation**: All `Dockerfile` files use `python:3.13-slim`

Base images use the "slim" variant:

**Slim vs Full Comparison**:
- **python:3.13**: ~1GB (full Debian install)
- **python:3.13-slim**: ~150MB (minimal Debian)
- **python:3.13-alpine**: ~50MB (different libc, compatibility issues)

**Why Slim Over Alpine**:
- Compatible with most Python packages (uses glibc)
- Widely tested and supported
- Better compatibility with binary wheels
- Sufficient size reduction for most use cases

**Security Benefits**:
- ✅ Fewer packages = fewer vulnerabilities
- ✅ Smaller attack surface
- ✅ Faster security updates
- ✅ Reduced CVE exposure

### Regular Base Image Updates

Container images are rebuilt from source for each release, ensuring base images stay current with security patches. Images are never patched in place (immutable infrastructure principle).

**Update Process**:
1. New release triggers container rebuild
2. Pulls latest `python:3.13-slim` base image
3. Rebuilds application layers
4. Tests new image
5. Deploys to production

## Recommended Production Enhancements

The following controls are **not currently implemented** but recommended for production deployments.

### Seccomp Profiles

**Status**: ⚠️ **Not Configured**

**What It Is**: System call filtering that restricts which kernel syscalls a container can make.

**Why It's Needed**:
- Containers by default can make ~300+ syscalls
- Most applications need <50 syscalls
- Restricting syscalls blocks exploit techniques

**How to Implement**:
Add to `docker-compose.yml`:
```yaml
services:
  aihub-api:
    security_opt:
      - seccomp:/path/to/seccomp-profile.json
```

**Recommendation**: Start with Docker's default profile, then create custom profiles per service based on actual syscall usage.

### AppArmor/SELinux Profiles

**Status**: ⚠️ **Not Configured**

**What It Is**: Mandatory Access Control (MAC) that restricts file system access, network operations, and process interactions.

**Why It's Needed**:
- Limits what files containers can read/write
- Restricts network access patterns
- Prevents lateral movement if compromised

**How to Implement**:
Add to `docker-compose.yml`:
```yaml
services:
  aihub-api:
    security_opt:
      - apparmor=aihub-api-profile  # or selinux label
```

**Recommendation**: Use Docker's default AppArmor profile initially, then customize based on application needs.

### Capability Dropping

**Status**: ⚠️ **Not Configured**

**What It Is**: Linux capabilities are root privileges divided into distinct units. Containers inherit many capabilities by default.

**Why It's Needed**:
- Containers don't need most root capabilities
- Even non-root users inherit some capabilities
- Dropping unnecessary capabilities limits damage from exploits

**How to Implement**:
Add to `docker-compose.yml`:
```yaml
services:
  aihub-api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to ports <1024
```

**Recommendation**: Drop all capabilities by default, add back only what's explicitly needed.

### Read-Only Root Filesystem

**Status**: ⚠️ **Not Configured**

**What It Is**: Mount container filesystem as read-only, use tmpfs for directories requiring write access.

**Why It's Needed**:
- Prevents malware from persisting on disk
- Blocks runtime code injection
- Enforces immutability principle

**How to Implement**:
Add to `docker-compose.yml`:
```yaml
services:
  aihub-api:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

**Consideration**: Requires careful identification of directories needing write access.

### Network Segmentation

**Status**: ⚠️ **Basic** (single Docker network)

**What It Is**: Separate Docker networks for frontend (API, web) and backend (database, vector store) services.

**Why It's Needed**:
- Limits lateral movement if service is compromised
- Enforces network-level access control
- Follows principle of least privilege

**How to Implement**:
```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

services:
  aihub-api:
    networks:
      - frontend
      - backend

  postgres:
    networks:
      - backend  # Not accessible from frontend network
```

**Recommendation**: Create separate networks for different trust zones.

## Automated Security Scanning

### Container Image Scanning

**Status**: ⚠️ **Not Implemented**

**Recommended Tools**:
- **Trivy**: Free, comprehensive, easy to integrate
- **Snyk**: Commercial, good developer experience
- **Grype**: Free, fast, focused on CVE detection

**CI/CD Integration** (example with Trivy):
```yaml
# .github/workflows/security-scan.yml
- name: Run Trivy Scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/bbvch-ai/aihub-core/api:latest'
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail build on vulnerabilities
```

**Recommendation**: Scan images on every build, block deployment if critical vulnerabilities found.

## Best Practices

### Immutable Infrastructure

**Principle**: Never patch running containers. Always rebuild and redeploy.

**Why**:
- Ensures reproducibility
- Prevents configuration drift
- Makes rollback simple
- Facilitates testing

**Implementation**:
- Build new images for updates
- Deploy via blue-green or rolling deployment
- Never SSH into containers to fix issues

### Minimal Software Installation

**Principle**: Only install software required for runtime.

**Avoid**:
- ❌ Build tools in runtime images (gcc, make, git)
- ❌ Shell utilities beyond basic needs
- ❌ Package managers in runtime images
- ❌ SSH servers in containers

**Acceptable**:
- ✅ Application runtime (Python interpreter)
- ✅ Required libraries for application
- ✅ Essential utilities (curl for health checks)

### Regular Updates

**Principle**: Keep base images and dependencies current.

**Cadence**:
- **Base images**: Update monthly or when security advisories released
- **Dependencies**: Update weekly or bi-weekly (with testing)
- **Critical patches**: Apply within 24-48 hours

### Principle of Least Privilege

**Principle**: Grant minimum permissions required for operation.

**Apply To**:
- User privileges (non-root execution)
- File system access (read-only where possible)
- Network access (segmented networks)
- Kernel capabilities (drop all, add needed only)
- System calls (Seccomp filtering)

## Verification and Testing

### Security Posture Checks

**Verify Non-Root Execution**:
```bash
docker exec <container> whoami  # Should be 'user'
docker exec <container> id      # Should show uid=1000
```

**Verify Image Layers**:
```bash
docker history <image-name>  # Review layer sizes and commands
```

**Scan for Vulnerabilities**:
```bash
trivy image <image-name>  # Lists CVEs in image
```

### Testing Hardened Configurations

When implementing hardening (Seccomp, capabilities, read-only FS):

1. **Test in Development**: Apply hardening to dev environment first
2. **Monitor Logs**: Check for syscall denials, permission errors
3. **Functional Testing**: Ensure application still works correctly
4. **Performance Testing**: Verify no performance degradation
5. **Gradual Rollout**: Deploy to staging, then production

## Related Documentation

- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Container orchestration and deployment strategies
- [Input Validation](../3_input_validation/) - Preventing malicious input from reaching containers
- [Malware Prevention](../2_malware_prevention/) - Scanning files processed by containers
- [Data Encryption](../x_data_encryption/) - Protecting data handled by containers

## References

- **Example Dockerfile**: `aihub_api/Dockerfile`
- **All Dockerfiles**: `aihub_agent/*/Dockerfile`, `aihub_pipeline/Dockerfile`, `aihub_web/aihub_web/Dockerfile`, `aihub_bot/Dockerfile`
- **Docker Compose**: `docker-compose.yml`, `docker-compose.local.yml`
- **Docker Security Best Practices**: [Docker Official Documentation](https://docs.docker.com/engine/security/)
