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
