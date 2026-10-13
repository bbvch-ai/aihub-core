---
title: Container Security
---

# Container Security

The Swiss AI Hub uses containerization (Docker) for all services with basic security hardening implemented.

## Implementation status

| Security Control          | Status         |
| ------------------------- | -------------- |
| Non-Root User Execution   | Implemented    |
| Multi-Stage Builds        | Implemented    |
| Minimal Base Images       | Implemented    |
| Seccomp Profiles          | Not configured |
| AppArmor/SELinux          | Not configured |
| Capability Dropping       | Not configured |
| Read-Only Root Filesystem | Not configured |
| Network Segmentation      | Implemented    |

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

## Code-execution sandbox

User code runs in `open-terminal`, the one container that executes arbitrary code. It is isolated in three ways.

- **Network.** It sits alone in the `code-sandbox` network, shared only with the services that call it (`open-webui`,
  `universal-agent` and `api`). A breakout can reach those callers, but has no direct network path to the rest of the
  application tier or to the data tier, and outside development the network has no outbound internet access (see
  [Network Isolation](../../2_architecture/4_network_isolation/)).
- **Per-user homes.** Each user works in their own home directory. The platform ships a patched sandbox image
  (`open-terminal-office`) whose file API resolves links and only reaches the requesting user's own home. Without the
  patch, a link inside one home could read or overwrite another user's files, or reach the server's environment. The
  image build fails if the patch no longer matches upstream, so a base-image bump cannot drop it silently.
- **Mirror and downloads.** The backup mirror mounts the homes read-only, skips symbolic links, and uses an S3 identity
  limited to its own bucket. Files served back to the browser through **My Files** show inline only as PDF, raster image
  or plain text. Everything else, HTML and SVG included, is sent as a download with `Content-Security-Policy: sandbox`,
  because agents write these files.

Shell commands still run as the user and see the sandbox system under normal permissions. Isolation between users rests
on the file API confinement and the container boundary, not on a separate container per user.

## Related documentation

- [Deployment Options](../../3_deployment_guide/1_deployment_options/) - Container orchestration
- [Input Validation](../2_input_validation/) - Preventing malicious input
- [Data Encryption](../5_data_encryption/) - Data protection
