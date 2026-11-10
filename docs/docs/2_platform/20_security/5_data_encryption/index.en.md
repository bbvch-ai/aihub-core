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

## Secret Configuration Fields

Independently of the volume encryption, the platform encrypts the secret fields of agent profiles and knowledge source
configurations itself. A field is secret when its form declares it as a password input or a key file; no field name is
hard-coded. For agents these are the mailbox password and the Entra ID client secret of the Email Agent, the API key of
an MCP Tool Agent connection, and the Jira token of the Release Notes Assistant.

- **Encrypted at rest**: The API encrypts a secret before it stores it, with the key in `AIHUB_CONFIG_ENCRYPTION_KEY`.
  The database, its backups and the configuration an agent fetches over NATS hold only the ciphertext.
- **Decrypted only where it is used**: An agent decrypts its secrets only when it validates the profile for a run. The
  run state it keeps in Valkey holds the ciphertext.
- **Masked in responses**: The API never returns a secret or its ciphertext. A stored secret is shown as a mask, and
  saving the form with the mask unchanged keeps the stored secret. A mask is bound to its field and profile and is
  refused anywhere else.
- **Export, import and clone**: An exported profile holds masks, never secrets. Importing such a file or cloning a
  profile clears the masked fields, and the Admin UI names them so you can enter them again before saving.

### The Key

`AIHUB_CONFIG_ENCRYPTION_KEY` is a Fernet key, the url-safe base64 encoding of 32 random bytes. Generate one with
`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. The same key must reach the
API, the knowledge pipelines and every agent whose profiles hold a secret: `imap_agent`, `email_classification_agent`
and `release_notes_agent` in the shipped compose files, and any custom SDK agent that declares a password field.

- **Required once a secret is stored**: The API refuses to start while a stored profile holds a secret and the key is
  missing or malformed. Profiles that leave every secret blank need no key.
- **No rotation**: Changing the key makes every stored secret unreadable. Enter the secrets again after a change.
- **Backups are tied to the key**: A database backup restores usable secrets only together with the key in use when it
  was taken. Keep the key safe, and separate from the backups.

### Upgrading to Encrypted Agent Secrets

Agent profiles saved before agent secrets were encrypted still hold them in plaintext. The API encrypts them when it
starts, once the agent has announced its blueprint, so a profile may only be encrypted on a later restart. Upgrade the
agent containers first, or in the same deployment, and the API last: an agent that cannot decrypt would use the
ciphertext as its credential. Custom SDK agents with password fields must be upgraded, and given the key, before the
API. Replace all API replicas together: a replica from before the upgrade returns stored ciphertext where the new ones
return a mask. After the upgrade:

- Rotate the IMAP, MCP and Jira credentials. Exports and backups made before the upgrade may still hold them in
  plaintext.
- Step traces in Langfuse may hold the decrypted values a run used, before the upgrade and after it. Redacting them is a
  separate change.
- Reload any profile form left open during the upgrade. Saving it may be refused with a request to resubmit the form.

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
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **Referrer-Policy**: Limits referrer information leakage

The Admin UI and the Sysadmin UI additionally send their own **Content-Security-Policy** and HSTS header from nginx.
Scripts load only from the app itself, plugins and `<base>` rewrites are blocked, and frames, form targets and outgoing
connections are limited to the app, Keycloak and OpenWebUI. The Admin UI loads images only from the app and the S3
storage, so a markdown image cannot send chat content to another server. The container fills in these origins from
`OAUTH_AUTHORITY_URL`, `WEBUI_URL`, `WS_ENDPOINT` and `S3_STORAGE_PUBLIC_ENDPOINT` at start. Without
`S3_STORAGE_PUBLIC_ENDPOINT`, images and uploads are allowed from any HTTPS origin.

## External Service Connections

All connections from the platform to external services utilize encrypted transport:

- **Swiss LLM Cloud**: HTTPS connections to the configured Swiss LLM Cloud endpoints
- **OAuth/OIDC Providers**: TLS-secured authentication flows
- **LLM Providers**: Encrypted API connections through the LiteLLM proxy layer

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
