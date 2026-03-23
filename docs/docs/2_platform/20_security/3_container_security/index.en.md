---
title: Container Security
---

# Container Security

The Swiss AI Hub uses containerization (Docker) for all services with basic security hardening implemented.

## Implementation status

| Security Control          | Status                 |
| ------------------------- | ---------------------- |
| Non-Root User Execution   | Implemented            |
| Multi-Stage Builds        | Implemented            |
| Minimal Base Images       | Implemented            |
| Seccomp Profiles          | Not configured         |
| AppArmor/SELinux          | Not configured         |
| Capability Dropping       | Not configured         |
| Read-Only Root Filesystem | Not configured         |
| Network Segmentation      | Basic (single network) |

## Implemented controls

### Non-root user execution

Every container runs as a non-privileged user (UID 1000, GID 1000). All application processes run without root
privileges, limiting damage from container escape vulnerabilities and preventing privilege escalation.

### Multi-stage builds

Containers use multi-stage builds separating build and runtime environments. The builder stage compiles dependencies
with build tools, while the runtime stage copies only necessary artifacts, excluding build tools from the final image.
This reduces attack surface and image size.

### Minimal base images

Base images use the slim variant (~150MB) instead of full Debian (~1GB). This provides fewer packages, smaller attack
surface, and reduced CVE exposure while maintaining compatibility with Python packages.

### Regular base image updates

Container images are rebuilt from source for each release, ensuring base images stay current with security patches.
Images follow immutable infrastructure principles and are never patched in place.

## Related documentation

- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Container orchestration
- [Input Validation](../2_input_validation/) - Preventing malicious input
- [Data Encryption](../5_data_encryption/) - Data protection
