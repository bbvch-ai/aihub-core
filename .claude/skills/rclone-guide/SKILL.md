---
name: rclone-guide
description: Reference for rclone integration in the pipeline system. Covers RcloneSourceFactory (env-var config), RcloneSourceConfig (programmatic config), RcloneClient (RC API), RcloneResource (Dagster), RcloneIOManager, observable rclone assets, and setting up new cloud storage connectors. Use when user says 'set up OneDrive connector', 'rclone configuration', 'add cloud storage backend', 'rclone filter patterns', 'connect Google Drive', 'rclone authentication', 'RcloneSourceConfig', 'RcloneSourceFactory', 'troubleshoot rclone', or 'how does rclone work'. Do NOT use for scaffolding new pipelines (use scaffold-pipeline), debugging pipeline failures (use debug-pipeline), or general pipeline architecture (use dagster-pipelines).
arguments:
  - name: topic
    description: Topic or question (e.g., "OneDrive setup", "filter patterns", "authentication", "RcloneSourceConfig", "RcloneSourceFactory", "backends")
allowed-tools: Read, Grep, Glob
---

# Rclone Integration — Cloud Storage Reference

Look up rclone integration information. Topic or question via `$ARGUMENTS`.

______________________________________________________________________

## Overview

**rclone** is a command-line tool for managing files on 70+ cloud storage backends. The platform uses rclone as a
**universal source connector** for Stage 1 pipelines (Source → DataLake).

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

rclone runs as a standalone Docker service with its RC (Remote Control) API exposed. In development, no auth
(`--rc-no-auth`); in production, auth is enabled via `--rc-user` and `--rc-pass`. The `--rc-serve` flag is required for
file downloads.

______________________________________________________________________

## RcloneSourceFactory (Preferred Configuration)

The standard way to configure rclone sources. Loads config from `RCLONE_{SOURCE}_*` environment variables.

```python
# packages/core/swiss_ai_hub/core/infrastructure/rclone/RcloneSourceFactory.py

class RcloneSourceSettings(EnvironmentSettings):
    """Loads RCLONE_{SOURCE}_NAME, RCLONE_{SOURCE}_TYPE, and all other
    RCLONE_{SOURCE}_* as backend-specific options."""

    @classmethod
    def load(cls, source: str) -> RcloneSourceConfig:
        """Load config for a source (e.g., 'AZUREBLOB' loads RCLONE_AZUREBLOB_* env vars)."""
```

### Helper Functions

Pre-configured loaders for common backends:

| Helper                  | Loads env prefix      | Backend            |
| ----------------------- | --------------------- | ------------------ |
| `sharepoint_source()`   | `RCLONE_SHAREPOINT_*` | SharePoint Online  |
| `onedrive_source()`     | `RCLONE_ONEDRIVE_*`   | OneDrive           |
| `google_drive_source()` | `RCLONE_GDRIVE_*`     | Google Drive       |
| `s3_source()`           | `RCLONE_S3_*`         | AWS S3 / MinIO     |
| `azure_blob_source()`   | `RCLONE_AZUREBLOB_*`  | Azure Blob Storage |
| `sftp_source()`         | `RCLONE_SFTP_*`       | SFTP               |
| `local_fs_source()`     | `RCLONE_LOCAL_FS_*`   | Local filesystem   |

### Required Env Vars

For any source, two vars are always required:

```bash
RCLONE_{SOURCE}_NAME=my-remote       # Remote name (alphanumeric + _ -)
RCLONE_{SOURCE}_TYPE=onedrive        # Backend type (onedrive, drive, s3, azureblob, sftp, local)
```

All other `RCLONE_{SOURCE}_*` vars become backend-specific options:

```bash
# Example: OneDrive
RCLONE_ONEDRIVE_NAME=onedrive
RCLONE_ONEDRIVE_TYPE=onedrive
RCLONE_ONEDRIVE_CLIENT_ID=your-app-id
RCLONE_ONEDRIVE_CLIENT_SECRET=your-secret
RCLONE_ONEDRIVE_TOKEN={"access_token":"...","refresh_token":"..."}
RCLONE_ONEDRIVE_DRIVE_TYPE=business
```

### Usage in Pipeline

```python
from swiss_ai_hub.core.infrastructure.rclone.RcloneSourceFactory import onedrive_source
from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

source = onedrive_source()

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="company-docs",
    datalake_directory_name="onedrive-sales",
    rclone_config=source,
    source_remote=f"{source.name}:Documents/Sales",
)
```

See `packages/pipeline/templates/sources/` for complete per-backend examples with `.env.template` files.

______________________________________________________________________

## RcloneSettings (Connection Config)

Global rclone service connection settings.

```python
# packages/core/swiss_ai_hub/core/infrastructure/rclone/RcloneSettings.py

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

______________________________________________________________________

## RcloneSourceConfig (Programmatic Configuration)

For cases where env-var configuration isn't suitable (dynamic config, tests, playground):

```python
# packages/core/swiss_ai_hub/core/infrastructure/rclone/RcloneSourceConfig.py

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
```

### Example: Manual OneDrive Config

```python
RcloneSourceConfig(
    name="onedrive",
    backend_type=RcloneBackendType.ONEDRIVE,
    options={
        "client_id": "your-app-client-id",
        "client_secret": SecretStr("your-app-client-secret"),
        "token": '{"access_token":"...","refresh_token":"..."}',
        "drive_type": "business",
    },
)
```

### Example: Manual S3 Config

```python
RcloneSourceConfig(
    name="external-s3",
    backend_type=RcloneBackendType.S3,
    options={
        "provider": "AWS",  # or "Minio", "Ceph"
        "access_key_id": "AKIA...",
        "secret_access_key": SecretStr("..."),
        "region": "eu-central-1",
    },
)
```

Serialization for Dagster resources: `config.model_dump(mode="json", exclude_none=True)`.

______________________________________________________________________

## RcloneClient (Low-Level API)

HTTP client wrapping the rclone RC API. Uses `httpx` (sync) for config operations and `aiohttp` (async) for file
operations.

```python
# packages/pipeline/swiss_ai_hub/pipeline/resources/rclone/RcloneClient.py

class RcloneClient:
    def __init__(self, base_url: str | None = None, default_remote: str | None = None, timeout: int = 30):
        settings = RcloneSettings()
        self.base_url = (base_url or settings.URL).rstrip("/")
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

files = await client.list_files(
    include=["*.pdf", "*.docx"],
    exclude=["**/archive/**", "**/temp/**"],
)

for f in files:
    print(f"{f.path} ({f.size} bytes, modified: {f.modified})")
```

Rclone applies filters in order: excludes first → includes → implicit exclude-all (if includes specified).

### Downloading Files

```python
file = await client.download_bytes("path/to/document.pdf")
# Returns RcloneFile with .name, .content (bytes), .mime_type, .modified
```

Download requires `--rc-serve` flag on the rclone service. Timeout: 600s read, 30s connect.

______________________________________________________________________

## RcloneResource (Dagster Resource)

Wraps `RcloneClient` as a Dagster `ConfigurableResource`. Provides sync methods that safely wrap async operations.

```python
# packages/pipeline/swiss_ai_hub/pipeline/resources/rclone/RcloneResource.py

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

If `rclone_config_dict` is provided, the resource auto-creates the remote on first use via `RcloneClient.ensure_remote`.

______________________________________________________________________

## RcloneIOManager

Read-only IO manager for loading files from rclone remotes.

```python
# packages/pipeline/swiss_ai_hub/pipeline/io/RcloneIOManager.py

class RcloneIOManager(ConfigurableIOManager):
    rclone_client: ResourceDependency[RcloneResource]
```

**Two loading patterns**:

- **Partitioned** → `RcloneFile` with full content (for document processing)
- **Non-partitioned** → `list[MinimalRcloneFile]` metadata only (for cleanup comparison — saves memory)

`handle_output()` raises `NotImplementedError` — rclone is read-only.

______________________________________________________________________

## Observable Rclone Asset

Monitors a rclone remote for file changes using hash-based change detection.

```python
# packages/pipeline/swiss_ai_hub/pipeline/assets/factories/rclone_to_data_lake/observable_rclone_factory.py

def observable_rclone_factory(key, partitions, max_partitions):
    @observable_source_asset(key=key, partitions_def=partitions, io_manager_key="rclone_io_manager")
    def observable_rclone(context, rclone_client: RcloneResource) -> DataVersionsByPartition:
        rclone_files = rclone_client.fetch_minimal_files()
        return data_version_by_partition_for_rclone_files(
            context=context, asset_key=key, partition=partitions,
            rclone_files=rclone_files, max_partitions=max_partitions,
        )
    return observable_rclone
```

### Change Detection

| Method                      | Priority | When Used                                            |
| --------------------------- | -------- | ---------------------------------------------------- |
| **Content hash** (MD5/SHA1) | Primary  | Backend supports hashes (OneDrive, S3, etc.)         |
| **mtime + size**            | Fallback | Backend doesn't support hashes (local FS, some SFTP) |

Change detection op: `packages/pipeline/swiss_ai_hub/pipeline/ops/rclone/data_version_by_partition_for_rclone_files.py`.

______________________________________________________________________

## RcloneFile Types

```python
# packages/pipeline/swiss_ai_hub/pipeline/types/RcloneFile.py

class MinimalRcloneFile(MinimalSourceFile):
    remote: str = ""              # e.g., "onedrive:"
    is_dir: bool = False
    mime_type: str | None = None
    id: str | None = None         # Remote-specific file ID
    hashes: dict[str, str] | None = None  # {"md5": "...", "sha1": "..."}
    created: int = 0              # UNIX timestamp

class RcloneFile(SourceFile, MinimalRcloneFile):
    remote_path: str              # Full path within remote

    @property
    def source_url(self) -> str:
        return f"{self.remote}{self.remote_path}"
```

______________________________________________________________________

## Troubleshooting

For detailed pipeline debugging, use the `/debug-pipeline` skill with Dagster MCP tools.

Common rclone-specific errors:

| Error                                                      | Cause                          | Fix                                                                         |
| ---------------------------------------------------------- | ------------------------------ | --------------------------------------------------------------------------- |
| `ClientConnectorError: Cannot connect to host rclone:5572` | Service not running            | `docker compose ps rclone`                                                  |
| `403 Forbidden`                                            | RC auth mismatch               | Check `RCLONE_RC_USER`/`RCLONE_RC_PASS` match `--rc-user`/`--rc-pass` flags |
| `didn't find section in config file`                       | Remote not configured          | Provide `rclone_config_dict` or use `RcloneSourceFactory` helpers           |
| `token has expired`                                        | OAuth2 token lifetime exceeded | Reconfigure remote with fresh tokens (90-day refresh typical)               |
| `asyncio.TimeoutError`                                     | Large file download            | Increase `timeout` in `RcloneClient.__init__` (default: 600s)               |

______________________________________________________________________

## Conventions

- Use `RcloneSourceFactory` helpers for production config (env-var-based)
- Use `RcloneSourceConfig` directly only for tests, playground, and dynamic config
- `SecretStr` for all credentials in `RcloneSourceConfig.options`
- Include/exclude patterns use rclone glob syntax (not regex)
- IO manager is read-only (`handle_output` raises `NotImplementedError`)
- Remote names: alphanumeric with `_` and `-` only (Pydantic-validated)
- Serialize config via `config.model_dump(mode="json", exclude_none=True)`
