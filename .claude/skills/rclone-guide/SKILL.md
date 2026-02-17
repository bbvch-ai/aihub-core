---
name: rclone-guide
description: >-
  Reference for rclone integration in the pipeline system. Covers rclone configuration, supported backends,
  RcloneResource, RcloneClient, RcloneIOManager, observable rclone assets, and setting up new cloud storage
  connectors. Use when user says 'set up OneDrive connector', 'rclone configuration', 'add cloud storage
  backend', 'rclone filter patterns', 'connect Google Drive', 'rclone authentication', 'RcloneSourceConfig',
  'troubleshoot rclone', or 'how does rclone work'. Covers 70+ storage backends.
arguments:
  - name: topic
    description: Topic or question (e.g., "OneDrive setup", "filter patterns", "authentication", "RcloneSourceConfig", "backends")
allowed-tools: Read, Grep, Glob
---

# Rclone Integration — Cloud Storage Reference

Look up rclone integration information. Topic or question via `$ARGUMENTS`.

---

## Overview

**rclone** is a command-line tool for managing files on 70+ cloud storage backends. The platform uses rclone as a
**universal source connector** for Stage 1 pipelines (Source → DataLake).

**Why rclone**: Single implementation for ALL cloud providers — no provider-specific SDKs, no custom authentication
code, no per-backend maintenance. One connector handles OneDrive, SharePoint, Google Drive, Dropbox, Box, S3, Azure
Blob, SFTP, and 60+ more.

### Architecture

```
Cloud Storage (OneDrive, GDrive, etc.)
    ↓  rclone RC API (HTTP)
RcloneClient (aiohttp/httpx)
    ↓
RcloneResource (Dagster ConfigurableResource)
    ↓
RcloneIOManager (Dagster ConfigurableIOManager)
    ↓
Observable Rclone Asset → DataLakeFile → S3
```

### Docker Service

rclone runs as a standalone Docker service with its RC (Remote Control) API exposed:

```yaml
rclone:
  image: rclone/rclone
  command: rcd --rc-addr=:5572 --rc-no-auth --rc-serve
  ports:
    - "5572:5572"
```

In production, authentication is enabled:

```yaml
command: rcd --rc-addr=:5572 --rc-user=${RCLONE_RC_USER} --rc-pass=${RCLONE_RC_PASS} --rc-serve
```

---

## RcloneSettings (Connection Config)

```python
# aihub_lib/aihub_lib/infrastructure/rclone/RcloneSettings.py

class RcloneSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("RCLONE_")

    URL: str = "http://rclone:5572"     # Rclone RC API URL
    RC_USER: str | None = None          # RC API username (non-dev environments)
    RC_PASS: SecretStr | None = None    # RC API password (non-dev environments)
```

| Env Variable     | Default              | Purpose                  |
| ---------------- | -------------------- | ------------------------ |
| `RCLONE_URL`     | `http://rclone:5572` | RC API endpoint          |
| `RCLONE_RC_USER` | None                 | HTTP Basic Auth username |
| `RCLONE_RC_PASS` | None                 | HTTP Basic Auth password |

---

## RcloneSourceConfig (Remote Definition)

Defines a remote storage backend. Used to programmatically configure rclone remotes.

```python
# aihub_lib/aihub_lib/infrastructure/rclone/RcloneSourceConfig.py

class RcloneBackendType(str, Enum):
    ONEDRIVE = "onedrive"
    DRIVE = "drive"        # Google Drive
    S3 = "s3"
    LOCAL = "local"
    AZUREBLOB = "azureblob"
    SFTP = "sftp"

class RcloneSourceConfig(BaseModel):
    name: str              # Remote name (alphanumeric + _ -)
    backend_type: RcloneBackendType
    options: dict[str, Any] = {}  # Backend-specific options

    def to_rclone_params(self) -> dict[str, Any]:
        """Convert to rclone config/create API payload."""
        return {
            "name": self.name,
            "type": self.backend_type.value,
            "parameters": {
                k: v.get_secret_value() if isinstance(v, SecretStr) else v
                for k, v in self.options.items()
            },
        }
```

### Backend Configuration Examples

**OneDrive**:

```python
RcloneSourceConfig(
    name="onedrive",
    backend_type=RcloneBackendType.ONEDRIVE,
    options={
        "client_id": "your-app-client-id",
        "client_secret": SecretStr("your-app-client-secret"),
        "token": '{"access_token":"...","refresh_token":"...","expiry":"..."}',
        "drive_type": "personal",  # or "business"
    },
)
```

**Google Drive**:

```python
RcloneSourceConfig(
    name="gdrive",
    backend_type=RcloneBackendType.DRIVE,
    options={
        "client_id": "your-client-id.apps.googleusercontent.com",
        "client_secret": SecretStr("your-client-secret"),
        "token": '{"access_token":"...","refresh_token":"..."}',
        "scope": "drive.readonly",
    },
)
```

**S3-Compatible**:

```python
RcloneSourceConfig(
    name="external-s3",
    backend_type=RcloneBackendType.S3,
    options={
        "provider": "AWS",  # or "Minio", "Ceph", etc.
        "access_key_id": "AKIA...",
        "secret_access_key": SecretStr("..."),
        "region": "eu-central-1",
        "endpoint": "",  # Custom endpoint for non-AWS S3
    },
)
```

**Azure Blob Storage**:

```python
RcloneSourceConfig(
    name="azblob",
    backend_type=RcloneBackendType.AZUREBLOB,
    options={
        "account": "mystorageaccount",
        "key": SecretStr("base64-encoded-account-key"),
        # Or use SAS token:
        # "sas_url": "https://account.blob.core.windows.net/container?sv=...&sig=...",
    },
)
```

**SFTP**:

```python
RcloneSourceConfig(
    name="sftp-server",
    backend_type=RcloneBackendType.SFTP,
    options={
        "host": "sftp.example.com",
        "user": "username",
        "pass": SecretStr("password"),
        "port": "22",
    },
)
```

---

## RcloneClient (Low-Level API)

HTTP client wrapping the rclone RC API. Uses `httpx` for sync config operations and `aiohttp` for async file operations.

```python
# aihub_pipeline/aihub_pipeline/resources/rclone/RcloneClient.py

class RcloneClient:
    def __init__(self, base_url: str | None = None, default_remote: str | None = None, timeout: int = 30):
        settings = RcloneSettings()
        self.base_url = (base_url or settings.URL).rstrip("/")
        self.default_remote = default_remote
        # Auto-configures HTTP Basic Auth if RCLONE_RC_USER/RC_PASS are set
```

### Key Methods

| Method                                 | Sync/Async | Purpose                                       |
| -------------------------------------- | ---------- | --------------------------------------------- |
| `upsert_remote(config)`                | Sync       | Create or update a remote via `config/create` |
| `remote_exists(name)`                  | Sync       | Check if remote exists via `config/get`       |
| `ensure_remote(config)`                | Sync       | Create remote only if it doesn't exist        |
| `list_files(include, exclude, remote)` | **Async**  | List files with metadata (no content)         |
| `download_bytes(file_path, remote)`    | **Async**  | Download file content                         |

### Listing Files with Filters

```python
client = RcloneClient(base_url="http://rclone:5572", default_remote="onedrive:Documents")

# List all PDFs, excluding archive folder
files = await client.list_files(
    include=["*.pdf", "*.docx"],
    exclude=["**/archive/**", "**/temp/**"],
)

for f in files:
    print(f"{f.path} ({f.size} bytes, modified: {f.modified})")
    if f.hashes:
        print(f"  MD5: {f.hashes.get('md5')}")
```

### Filter Rule Priority

Rclone applies filters in order:

1. **Excludes first** (noise removal): `- **/archive/**`
2. **Includes** (scope definition): `+ *.pdf`, `+ *.docx`
3. **Implicit exclude** (if includes specified): `- **` (exclude everything else)

### Downloading Files

```python
# Download via rclone's native HTTP serve (requires --rc-serve flag)
file = await client.download_bytes("path/to/document.pdf")

print(f"Name: {file.name}")
print(f"Size: {len(file.content)} bytes")
print(f"MIME: {file.mime_type}")
print(f"Modified: {file.modified}")
```

Download URL format: `http://host:port/[remote]/path/to/file`

- URL-encoded for special characters (spaces, etc.)
- Timeout: 600s for read, 30s for connect

---

## RcloneResource (Dagster Resource)

Wraps `RcloneClient` as a Dagster `ConfigurableResource`. Provides sync methods that safely wrap async operations.

```python
# aihub_pipeline/aihub_pipeline/resources/rclone/RcloneResource.py

class RcloneResource(ConfigurableResource):
    source_remote: str          # e.g., "onedrive:Documents"
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None
    rclone_config_dict: dict[str, Any] | None = None  # Serialized RcloneSourceConfig
```

### Key Methods

| Method                           | Returns                   | Purpose                         |
| -------------------------------- | ------------------------- | ------------------------------- |
| `fetch_minimal_files()`          | `list[MinimalRcloneFile]` | Metadata only (for observation) |
| `download_file(file_path)`       | `RcloneFile`              | Full content (for processing)   |
| `fetch_minimal_files_async()`    | `list[MinimalRcloneFile]` | Async version                   |
| `download_file_async(file_path)` | `RcloneFile`              | Async version                   |

### Auto Remote Configuration

If `rclone_config_dict` is provided, the resource automatically ensures the remote exists before any operation:

```python
rclone_client = RcloneResource(
    source_remote="onedrive:Documents",
    include_patterns=["*.pdf", "*.docx"],
    rclone_config_dict=config.model_dump(mode="json", exclude_none=True),
)

# First call: auto-creates remote if needed, then lists files
files = rclone_client.fetch_minimal_files()
```

### Manual vs Auto Configuration

**Auto** (via `rclone_config_dict`): Remote configured programmatically on first use. Best for automated deployments.

**Manual** (via `rclone config` CLI): Remote pre-configured in `~/.config/rclone/rclone.conf`. Leave
`rclone_config_dict` as `None`. Best for development and manual setups.

---

## RcloneIOManager

Read-only IO manager for loading files from rclone remotes.

```python
# aihub_pipeline/aihub_pipeline/io/RcloneIOManager.py

class RcloneIOManager(ConfigurableIOManager):
    rclone_client: ResourceDependency[RcloneResource]

    def handle_output(self, context, obj):
        raise NotImplementedError("Writing to rclone remotes not supported (read-only)")

    def load_input(self, context):
        if context.has_partition_key:
            # Partitioned: download full file content
            return self.rclone_client.download_file(context.partition_key)
        else:
            # Non-partitioned: metadata only (for cleanup comparison)
            all_keys = partitions_def.get_partition_keys(...)
            all_files = self.rclone_client.fetch_minimal_files()
            return [f for f in all_files if f.path in set(all_keys)]
```

**Two loading patterns**:

- **Partitioned** → `RcloneFile` with content (for document processing)
- **Non-partitioned** → `list[MinimalRcloneFile]` metadata only (for cleanup comparison — saves memory)

---

## Observable Rclone Asset

Monitors a rclone remote for file changes using hash-based change detection.

```python
# aihub_pipeline/aihub_pipeline/assets/factories/rclone_to_data_lake/observable_rclone_factory.py

def observable_rclone_factory(key, partitions, max_partitions):
    @observable_source_asset(
        key=key,
        partitions_def=partitions,
        io_manager_key="rclone_io_manager",
    )
    def observable_rclone(context, rclone_client: RcloneResource) -> DataVersionsByPartition:
        rclone_files = rclone_client.fetch_minimal_files()
        return data_version_by_partition_for_rclone_files(
            context=context, asset_key=key, partition=partitions,
            rclone_files=rclone_files, max_partitions=max_partitions,
        )
    return observable_rclone
```

### Change Detection Strategy

| Method                      | Priority | When Used                                            |
| --------------------------- | -------- | ---------------------------------------------------- |
| **Content hash** (MD5/SHA1) | Primary  | Backend supports hashes (OneDrive, S3, etc.)         |
| **mtime + size**            | Fallback | Backend doesn't support hashes (local FS, some SFTP) |

Hash-based detection = **zero false positives**. Detects ANY content change, ignores metadata-only changes.

---

## RcloneFile Types

### MinimalRcloneFile (Metadata Only)

```python
class MinimalRcloneFile(MinimalSourceFile):
    remote: str = ""              # e.g., "onedrive:"
    is_dir: bool = False
    mime_type: str | None = None
    id: str | None = None         # Remote-specific file ID
    hashes: dict[str, str] | None = None  # {"md5": "...", "sha1": "..."}
    created: int = 0              # UNIX timestamp
```

### RcloneFile (With Content)

```python
class RcloneFile(SourceFile, MinimalRcloneFile):
    remote_path: str              # Full path within remote

    @property
    def source_url(self) -> str:
        return f"{self.remote}{self.remote_path}"
```

---

## Complete Pipeline Setup

### Quick Start (Rclone → S3 → Vector Store)

```python
from aihub_pipeline.util.definitions_util import (
    default_rclone_to_datalake_definitions,
    default_definitions,
)
from aihub_lib.infrastructure.rclone import RcloneSourceConfig, RcloneBackendType

# Stage 1: OneDrive → S3
rclone_config = RcloneSourceConfig(
    name="onedrive",
    backend_type=RcloneBackendType.ONEDRIVE,
    options={
        "client_id": "your-app-id",
        "client_secret": "your-app-secret",
        "token": '{"access_token":"...","refresh_token":"..."}',
    },
)

stage1 = default_rclone_to_datalake_definitions(
    datalake_container_name="company-docs",
    source_remote="onedrive:Documents/Sales",
    rclone_config=rclone_config,
    include_patterns=["*.pdf", "*.docx", "*.pptx"],
    exclude_patterns=["**/archive/**", "**/draft/**"],
)

# Stage 2: S3 → Vector Store
stage2 = default_definitions(
    datalake_container_name="company-docs",
    embedding_model_name="embedding/large",
)
```

### Resource Wiring

When using `default_rclone_to_datalake_definitions()`, resources are auto-configured:

```python
resources={
    "rclone_client": RcloneResource(
        source_remote="onedrive:Documents",
        include_patterns=["*.pdf"],
        rclone_config_dict=config.model_dump(mode="json", exclude_none=True),
    ),
    "rclone_io_manager": RcloneIOManager(rclone_client=rclone_client),
    **s3_data_lake_resources(container_name="company-docs"),
}
```

---

## Filter Patterns

Rclone uses **glob patterns** (not regex):

| Pattern         | Matches                      |
| --------------- | ---------------------------- |
| `*.pdf`         | All PDF files (any depth)    |
| `*.{pdf,docx}`  | PDFs and DOCX files          |
| `Documents/**`  | Everything under Documents/  |
| `**/archive/**` | Archive folders at any depth |
| `**/temp/**`    | Temp folders at any depth    |
| `*.tmp`         | All .tmp files               |
| `??.txt`        | Two-character .txt files     |

### Filter Examples

```python
# Only sync documents
include_patterns=["*.pdf", "*.docx", "*.pptx", "*.xlsx", "*.md", "*.txt"]

# Exclude noise
exclude_patterns=[
    "**/archive/**",     # Archive folders
    "**/temp/**",        # Temp folders
    "**/draft/**",       # Draft folders
    "**/.git/**",        # Git folders
    "*.tmp",             # Temp files
    "~$*",               # Office lock files
    "Thumbs.db",         # Windows thumbnails
    ".DS_Store",         # macOS metadata
]
```

---

## Supported Backends (Subset)

| Backend          | Type        | Notes                                     |
| ---------------- | ----------- | ----------------------------------------- |
| **OneDrive**     | `onedrive`  | Personal & Business. OAuth2, hash support |
| **SharePoint**   | `onedrive`  | Via OneDrive backend with drive_id        |
| **Google Drive** | `drive`     | OAuth2, hash support                      |
| **Dropbox**      | `dropbox`   | OAuth2, hash support                      |
| **Box**          | `box`       | OAuth2, hash support                      |
| **AWS S3**       | `s3`        | Access key or IAM, hash support           |
| **Azure Blob**   | `azureblob` | Account key, SAS token, or Azure AD       |
| **SFTP**         | `sftp`      | Password or key auth                      |
| **Local FS**     | `local`     | Direct filesystem access                  |
| **FTP**          | `ftp`       | Plain FTP                                 |
| **WebDAV**       | `webdav`    | Nextcloud, ownCloud, etc.                 |
| **Mega**         | `mega`      | OAuth2                                    |
| **pCloud**       | `pcloud`    | OAuth2                                    |

Full list: https://rclone.org/overview/

---

## Troubleshooting

### Connection Refused

```
aiohttp.client_exceptions.ClientConnectorError: Cannot connect to host rclone:5572
```

- Rclone Docker service not running
- Check: `docker compose ps rclone`

### Authentication Failed

```
403 Forbidden
```

- `RCLONE_RC_USER` / `RCLONE_RC_PASS` mismatch
- Production: ensure `--rc-user` / `--rc-pass` flags match env vars

### Remote Not Found

```
Failed to create file system for "onedrive:Documents": didn't find section in config file
```

- Remote not configured. Either:
  - Provide `rclone_config_dict` in `RcloneResource`
  - Or run `rclone config` manually in the container

### Token Expired

```
Failed to create file system: token has expired
```

- OAuth2 tokens have limited lifetime
- Refresh tokens expire after 90 days (varies by provider)
- Reconfigure the remote with fresh tokens

### Timeout on Large Files

```
asyncio.TimeoutError
```

- Download timeout is 600s by default
- For very large files, increase `timeout` in `RcloneClient.__init__`

---

## Key File Reference

| File                                                                                              | Purpose                                    |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| `aihub_lib/aihub_lib/infrastructure/rclone/RcloneSettings.py`                                     | Connection settings                        |
| `aihub_lib/aihub_lib/infrastructure/rclone/RcloneSourceConfig.py`                                 | Remote config model                        |
| `aihub_pipeline/aihub_pipeline/resources/rclone/RcloneClient.py`                                  | Low-level RC API client                    |
| `aihub_pipeline/aihub_pipeline/resources/rclone/RcloneResource.py`                                | Dagster resource wrapper                   |
| `aihub_pipeline/aihub_pipeline/io/RcloneIOManager.py`                                             | IO manager (read-only)                     |
| `aihub_pipeline/aihub_pipeline/assets/factories/rclone_to_data_lake/observable_rclone_factory.py` | Observable asset                           |
| `aihub_pipeline/aihub_pipeline/ops/rclone/data_version_by_partition_for_rclone_files.py`          | Change detection op                        |
| `aihub_pipeline/aihub_pipeline/types/RcloneFile.py`                                               | File type definitions                      |
| `aihub_pipeline/aihub_pipeline/util/definitions_util.py`                                          | `default_rclone_to_datalake_definitions()` |

---

## Conventions Checklist

- [ ] Use `RcloneSourceConfig` for programmatic remote configuration (not raw dicts)
- [ ] `RcloneBackendType` enum for type safety on backend selection
- [ ] `SecretStr` for all credentials in `RcloneSourceConfig.options`
- [ ] `include_patterns` and `exclude_patterns` use rclone glob syntax (not regex)
- [ ] IO manager is read-only (`handle_output` raises `NotImplementedError`)
- [ ] Observable asset uses hash-based change detection with mtime+size fallback
- [ ] `rclone_config_dict` serialized via `config.model_dump(mode="json", exclude_none=True)`
- [ ] Remote names are alphanumeric with `_` and `-` only (validated by Pydantic)
- [ ] RC API authentication configured for non-dev environments
