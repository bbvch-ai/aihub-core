# Rclone Integration

Generic rclone-based file sync for AI-Hub pipelines. Works with 70+ cloud storage providers without provider-specific code.

## Supported Backends

**Cloud Storage:**
- OneDrive Personal & Business
- SharePoint (including shared folders)
- Google Drive
- Dropbox
- Box
- Azure Blob Storage
- AWS S3 & S3-compatible (MinIO, SeaweedFS, etc.)
- Google Cloud Storage
- Backblaze B2
- Wasabi
- And 60+ more...

**Traditional Protocols:**
- SFTP
- FTP
- WebDAV
- HTTP

**Local:**
- Local filesystem
- Network shares

## Installation

### 1. Install rclone binary

**Linux/macOS:**
```bash
curl https://rclone.org/install.sh | sudo bash
```

**Docker (add to Dockerfile):**
```dockerfile
RUN curl https://rclone.org/install.sh | bash
```

**Verify installation:**
```bash
rclone version
```

### 2. Configure Remote

**Interactive setup:**
```bash
rclone config create onedrive_remote onedrive
```

**Headless setup (environment variables):**
```bash
export RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
export RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=your_client_id
export RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_client_secret
export RCLONE_CONFIG_ONEDRIVE_TOKEN='{"access_token":"..."}'
```

**Config file location:**
- Default: `~/.config/rclone/rclone.conf`
- Custom: Specify via `rclone_config_path` parameter

## Usage

### Basic Pipeline

```python
from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="my-docs",
    source_remote="onedrive_remote:Documents",
    include_patterns=["*.pdf", "*.docx"],
    exclude_patterns=["**/archive/**"],
)
```

### Advanced Configuration

```python
from aihub_pipeline.resources.rclone.RcloneResource import RcloneResource
from aihub_pipeline.io.RcloneIOManager import RcloneIOManager

rclone_client = RcloneResource(
    source_remote="onedrive:Documents/ProjectX",
    target_remote="s3:my-bucket/sync",
    include_patterns=["*.pdf", "*.docx", "*.xlsx"],
    exclude_patterns=[
        "**/archiv/**",
        "**/temp/**",
        "**/.git/**",
    ],
    rclone_config_path="/custom/path/to/rclone.conf",
    sync_deletions=False,  # Use application-level cleanup
    max_delete=100,
    dry_run=False,
)

# List files (metadata only)
files = rclone_client.fetch_minimal_files()

# Download specific file
file = rclone_client.download_file("path/to/file.pdf")

# Sync to target
result = rclone_client.sync_files()
```

## Filter Patterns

Rclone uses glob patterns for filtering:

**Include patterns:**
```python
include_patterns=[
    "*.pdf",           # All PDFs
    "*.doc",           # All .doc files
    "*.docx",          # All .docx files
    "/Important/**",   # All files in Important folder
]
```

**Exclude patterns:**
```python
exclude_patterns=[
    "**/archiv/**",    # Any folder named archiv (case-sensitive)
    "**/Archiv/**",    # Any folder named Archiv
    "**/.git/**",      # Git directories
    "**/temp/**",      # Temp directories
    "*.tmp",           # Temporary files
]
```

**Pattern syntax:**
- `*` - matches any characters except `/`
- `**` - matches any characters including `/`
- `?` - matches one character
- Patterns are case-sensitive by default

## Authentication

### OneDrive

**Option 1: Interactive (development):**
```bash
rclone config create onedrive_remote onedrive
# Follow OAuth2 flow in browser
```

**Option 2: Service Account (production):**
```bash
export RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
export RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=your_app_id
export RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_app_secret
export RCLONE_CONFIG_ONEDRIVE_TOKEN='{"access_token":"...","refresh_token":"..."}'
```

### SharePoint

```bash
rclone config create sharepoint_remote onedrive \
    --onedrive-drive-type "documentLibrary"
```

### Google Drive

```bash
rclone config create gdrive_remote drive
# Follow OAuth2 flow
```

### S3-Compatible

```bash
rclone config create s3_remote s3 \
    --s3-provider AWS \
    --s3-access-key-id your_access_key \
    --s3-secret-access-key your_secret_key \
    --s3-region us-east-1
```

## Examples

### OneDrive → S3
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="onedrive-sync",
    source_remote="onedrive_remote:Documents",
    include_patterns=["*.pdf", "*.docx"],
)
```

### Google Drive → S3
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="gdrive-sync",
    source_remote="gdrive:Shared Documents",
    include_patterns=["*.pdf"],
)
```

### SharePoint → S3
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="sharepoint-sync",
    source_remote="sharepoint:sites/MySite/Shared Documents",
    exclude_patterns=["**/archive/**"],
)
```

### Azure Blob → S3
```python
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="azure-sync",
    source_remote="azure:container-name/prefix",
    include_patterns=["*.json", "*.csv"],
)
```

## Deletion Handling

By default, deletions are handled at the application level:

1. **Rclone syncs** files to S3 (append-only, no deletions)
2. **Observable asset** scans source and reports all existing files
3. **Cleanup asset** compares source vs S3 and removes orphans

**Why this approach?**
- Consistent across all source types (rclone, SharePoint, LocalFS)
- Observable in Dagster UI (lineage, logs, failures)
- Safer (separate scheduled job, can abort/retry)
- Supports cascade deletions (S3 → Mongo → Milvus)

**To enable rclone-level deletions:**
```python
rclone_client = RcloneResource(
    source_remote="...",
    target_remote="...",
    sync_deletions=True,  # Use rclone sync instead of copy
    max_delete=100,       # Safety limit
)
```

## Troubleshooting

### "rclone: command not found"
Install rclone binary: `curl https://rclone.org/install.sh | sudo bash`

### Authentication errors
Re-run: `rclone config reconnect remote_name`

### No files found
Check patterns with dry-run:
```bash
rclone lsf onedrive_remote:Documents \
    --include "*.pdf" \
    --exclude "**/archive/**" \
    --dry-run -vv
```

### Slow listing
Enable `--fast-list` (already enabled in RcloneResource)

### Rate limiting
Rclone automatically handles rate limits via exponential backoff

## Performance

**Optimizations enabled by default:**
- `--fast-list`: Faster directory listing
- `--transfers=4`: 4 parallel transfers
- `--checkers=8`: 8 parallel checkers
- Automatic retry on failure
- Exponential backoff on rate limits

**For large datasets (100K+ files):**
- Use `include_patterns` to reduce scope
- Consider splitting into multiple pipelines
- Monitor Dagster UI for performance metrics

## Comparison to Direct Integration

| Aspect | Rclone | Direct SDK (SharePoint, etc.) |
|--------|--------|-------------------------------|
| **Setup** | Single config, works everywhere | Per-provider SDK, auth, code |
| **Providers** | 70+ backends | One per implementation |
| **Maintenance** | Minimal (rclone handles APIs) | High (API changes, auth updates) |
| **Performance** | Very good (optimized transfers) | Comparable |
| **Control** | CLI-based (subprocess) | Native Python (fine-grained) |
| **Metadata** | Basic (size, mtime, type) | Rich (provider-specific) |

**When to use rclone:**
- New source types (OneDrive, GDrive, Azure Blob)
- Quick prototyping
- Standardization across providers

**When to use direct SDK:**
- Need provider-specific metadata (SharePoint ETags)
- Complex authentication requirements
- Advanced API features

## See Also

- [Rclone Documentation](https://rclone.org/docs/)
- [Rclone Filtering](https://rclone.org/filtering/)
- [Example Pipeline](/home/user/aihub-core/aihub_pipeline/playground/quick_start/rclone_onedrive_pipeline.py)
