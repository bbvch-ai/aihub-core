---
title: Data Encryption
---

# Data Encryption at Rest

> **️⚠️Implementation Status**: This encryption approach is not yet implemented. This section describes the planned
> security concept.

## LUKS Volume Encryption

All platform data is stored within Docker volumes, which are encrypted using Linux Unified Key Setup (LUKS). This
approach provides full-disk encryption for all persistent data stored by the platform, including:

- Application databases
- Vector store indices
- Document storage and ingestion artifacts
- Configuration data and secrets
- Logs and observability data

### Security Properties

LUKS encryption provides:

- **AES-256 encryption** in XTS mode for the entire volume
- **Key management** independent of the data, allowing key rotation without re-encrypting the entire volume
- **Protection against physical access**: Data remains encrypted when the system is powered off or volumes are detached
- **Transparent operation**: Applications interact with encrypted volumes without modification; encryption/decryption
  occurs at the block device layer

### Threat Mitigation

This encryption-at-rest strategy protects against:

- Unauthorized physical access to storage media
- Volume snapshot exfiltration
- Disk theft or improper disposal
- Backup media compromise

The encryption does **not** protect against threats while the system is running and volumes are mounted, such as
memory-based attacks or compromised application credentials. These threats are addressed through complementary controls
in access management, network segmentation, and runtime security monitoring.

# Data Encryption in Transit

All data transmitted between the platform and external clients, as well as connections to external services, is
encrypted using industry-standard Transport Layer Security (TLS) protocols.

## Edge Encryption

The platform employs **Traefik** as the reverse proxy and ingress controller, providing TLS termination at the network
edge. All external connections are secured through:

- **TLS 1.2 and TLS 1.3** support for client connections
- **Automatic HTTP to HTTPS redirection** ensuring all traffic uses encrypted channels
- **Let's Encrypt integration** for automated certificate provisioning and renewal in production environments
- **Custom certificate support** for environments with existing PKI infrastructure

### Production Certificate Management

In production deployments, TLS certificates are managed through:

- **ACME protocol** with Let's Encrypt for automatic certificate issuance and renewal
- **Certificate validation** via HTTP-01 challenge mechanism
- **Automated rotation** before expiration, preventing service interruptions

### Security Headers

Traefik applies security-hardened HTTP headers to all responses:

- **Strict-Transport-Security (HSTS)**: Enforces HTTPS for one year, including all subdomains
- **Content-Security-Policy**: Restricts frame embedding to same-origin
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **Referrer-Policy**: Limits referrer information leakage

## External Service Connections

All connections from the platform to external services utilize encrypted transport:

- **Azure OpenAI Services**: HTTPS connections to `*.openai.azure.com` and `*.cognitiveservices.azure.com`
- **OAuth/OIDC Providers**: TLS-secured authentication flows
- **LLM Providers**: Encrypted API connections through the LiteLLM proxy layer
- **Azure AI Services**: HTTPS for Document Intelligence, Speech Services, and Cognitive Search

### Certificate Validation

The platform validates server certificates for all external connections, protecting against man-in-the-middle attacks.
Standard library TLS implementations ensure:

- **Certificate chain verification** against trusted root CAs
- **Hostname validation** matching certificate Subject Alternative Names
- **Revocation checking** where supported by the service

## Internal Communication

Communication between Docker containers within the same deployment uses the internal Docker network. While this traffic
is isolated from external networks by Docker's network segmentation, it is **not encrypted at the application layer**.
The security model relies on:

- **Network isolation**: Container-to-container traffic never traverses external networks
- **Firewall boundaries**: The Docker host's network stack provides isolation from external access
- **Physical/virtual security**: The VM or host environment provides the security perimeter

For deployments requiring encrypted inter-service communication (e.g., multi-host deployments), additional measures such
as service mesh or IPsec can be implemented.

## WebSocket Connections

Real-time event streaming via WebSocket connections is secured using:

- **WSS (WebSocket Secure)**: TLS-encrypted WebSocket protocol for client connections
- **Origin validation**: Verifies the origin header to prevent cross-site WebSocket hijacking
- **Session-based authentication**: Requires valid authentication before upgrading to WebSocket
