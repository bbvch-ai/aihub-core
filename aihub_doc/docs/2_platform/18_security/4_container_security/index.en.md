---
title: Container Security
index: 4
---

# Container Security

The Swiss AI-Hub uses containerization (Docker) for all services with basic security hardening implemented.

## Implementation Status

| Security Control | Status |
|-----------------|--------|
| Non-Root User Execution | ✅ Implemented |
| Multi-Stage Builds | ✅ Implemented |
| Minimal Base Images | ✅ Implemented |
| Seccomp Profiles | ⚠️ Not configured |
| AppArmor/SELinux | ⚠️ Not configured |
| Capability Dropping | ⚠️ Not configured |
| Read-Only Root Filesystem | ⚠️ Not configured |
| Network Segmentation | ⚠️ Basic (single network) |

## Implemented Controls

### Non-Root User Execution

**Implementation**: All `Dockerfile` files (example: `aihub_api/Dockerfile:62-97`)

Every container runs as a non-privileged user (UID 1000, GID 1000). All application processes run without root privileges, limiting damage from container escape vulnerabilities and preventing privilege escalation.

### Multi-Stage Builds

**Implementation**: All `Dockerfile` files (example: `aihub_api/Dockerfile:1-105`)

Containers use multi-stage builds separating build and runtime environments. The builder stage compiles dependencies with build tools, while the runtime stage copies only necessary artifacts, excluding build tools from the final image. This reduces attack surface and image size.

### Minimal Base Images

**Implementation**: All `Dockerfile` files use `python:3.13-slim`

Base images use the slim variant (~150MB) instead of full Debian (~1GB). This provides fewer packages, smaller attack surface, and reduced CVE exposure while maintaining compatibility with Python packages.

### Regular Base Image Updates

Container images are rebuilt from source for each release, ensuring base images stay current with security patches. Images follow immutable infrastructure principles (never patched in place).

## Production Hardening Recommendations

For production deployments, consider implementing:

**Seccomp Profiles**: Restrict system calls to only what's necessary (blocks ~250+ unnecessary syscalls)

**AppArmor/SELinux**: Mandatory access control limiting file system access and process interactions

**Capability Dropping**: Remove all Linux capabilities, add back only required ones (e.g., `NET_BIND_SERVICE` for ports <1024)

**Read-Only Root Filesystem**: Mount application code as read-only with tmpfs for temporary directories

**Network Segmentation**: Separate Docker networks for frontend (API, web) and backend (database, vector store) services

**Automated Vulnerability Scanning**: Integrate tools like Trivy, Snyk, or Grype in CI/CD pipeline

## Best Practices

**Immutable Infrastructure**: Never patch running containers. Always rebuild and redeploy.

**Minimal Software**: Only install software required for runtime. Avoid build tools, SSH servers, or unnecessary utilities in runtime images.

**Regular Updates**: Update base images monthly or when security advisories released. Apply critical patches within 24-48 hours.

**Principle of Least Privilege**: Grant minimum permissions required for operation across user privileges, file system access, network access, and kernel capabilities.

## Verification

Check container security posture:
- `docker exec <container> whoami` - Should be 'user', not root
- `docker exec <container> id` - Should show uid=1000
- `docker history <image>` - Review layer sizes and commands
- `trivy image <image>` - Scan for vulnerabilities

## Related Documentation

- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Container orchestration
- [Input Validation](../3_input_validation/) - Preventing malicious input
- [Malware Prevention](../2_malware_prevention/) - File content scanning
- [Data Encryption](../x_data_encryption/) - Data protection

## References

- **Example Dockerfile**: `aihub_api/Dockerfile`
- **All Dockerfiles**: `aihub_agent/*/Dockerfile`, `aihub_pipeline/Dockerfile`, `aihub_web/aihub_web/Dockerfile`, `aihub_bot/Dockerfile`
- **Docker Compose**: `docker-compose.yml`, `docker-compose.local.yml`
