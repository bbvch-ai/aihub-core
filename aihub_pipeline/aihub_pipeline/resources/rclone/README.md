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

### 1. Rclone RC API Service

Rclone runs as a separate Docker service with Remote Control API enabled:

**Already configured in docker-compose.yml:**
```yaml
rclone:
  container_name: aihub-rclone
  image: rclone/rclone:latest
  command:
    - "rcd"
    - "--rc-addr=0.0.0.0:5572"
    - "--rc-no-auth"
  volumes:
    - ./rclone.conf:/config/rclone/rclone.conf:ro
```

**Start the service:**
```bash
docker compose -f docker-compose.dev.yml up -d rclone
```

**Verify installation:**
```bash
curl -X POST http://localhost:5572/core/version
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
    rc_url="http://aihub-rclone:5572",  # RC API endpoint
    source_remote="onedrive:Documents/ProjectX",
    include_patterns=["*.pdf", "*.docx", "*.xlsx"],
    exclude_patterns=[
        "**/archiv/**",
        "**/temp/**",
        "**/.git/**",
    ],
    max_retries=5,
    initial_retry_delay=1.0,
)

# List files (metadata only) - async HTTP call to RC API
files = rclone_client.fetch_minimal_files()

# Download specific file - async HTTP call to RC API
file = rclone_client.download_file("path/to/file.pdf")
```

**RC API Architecture:**
- RcloneResource uses async HTTP client (aiohttp)
- Follows same pattern as SharePointResource
- Connection pooling and retry logic built-in
- No subprocess overhead

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

Deletions are handled at the application level (not at rclone level):

1. **RC API lists** all files from source (operations/list)
2. **Observable asset** scans source and reports all existing files to Dagster
3. **Cleanup asset** compares source vs S3 and removes orphans

**Why this approach?**
- Consistent across all source types (rclone, SharePoint, LocalFS)
- Observable in Dagster UI (lineage, logs, failures)
- Safer (separate scheduled job, can abort/retry)
- Supports cascade deletions (S3 → Mongo → Milvus)

**Implementation:**
- RcloneResource only reads from source (via RC API)
- Application logic handles S3 cleanup based on observable source state
- Same pattern as SharePoint and LocalFS integrations

## Troubleshooting

### RC API Connection Refused
Check if rclone service is running:
```bash
docker compose -f docker-compose.dev.yml ps rclone
docker compose -f docker-compose.dev.yml logs rclone
```

### Authentication errors
Re-configure remote in rclone.conf, then restart service:
```bash
# On host
rclone config reconnect remote_name

# Restart service to reload config
docker compose -f docker-compose.dev.yml restart rclone
```

### No files found
Test RC API directly:
```bash
# List files via RC API
curl -X POST http://localhost:5572/operations/list \
    -H "Content-Type: application/json" \
    -d '{"fs":"onedrive:Documents","opt":{"recurse":true}}'
```

### HTTP 500 errors from RC API
Check rclone service logs:
```bash
docker compose -f docker-compose.dev.yml logs rclone
```

### Rate limiting
RcloneResource automatically handles rate limits with exponential backoff (max_retries parameter)

## Performance

**Optimizations enabled by default:**
- Async HTTP client (aiohttp) with connection pooling
- Automatic retry on failure (max_retries parameter)
- Exponential backoff on rate limits (429, 5xx errors)
- TCP connector with connection limits
- Timeouts configured per operation type

**For large datasets (100K+ files):**
- Use `include_patterns` to reduce scope
- RC API handles pagination automatically
- Consider splitting into multiple pipelines
- Monitor Dagster UI for performance metrics

**RC API advantages:**
- No subprocess overhead
- Persistent HTTP connections
- Efficient batch operations
- Same pattern as SharePointResource

## Comparison to Direct Integration

| Aspect | Rclone (RC API) | Direct SDK (SharePoint, etc.) |
|--------|-----------------|-------------------------------|
| **Setup** | Single config, works everywhere | Per-provider SDK, auth, code |
| **Providers** | 70+ backends | One per implementation |
| **Maintenance** | Minimal (rclone handles APIs) | High (API changes, auth updates) |
| **Performance** | Very good (async HTTP, pooling) | Comparable (async HTTP, pooling) |
| **Architecture** | RC API service → HTTP client | Graph API → HTTP client |
| **Code Pattern** | Same as SharePointResource | Native Python |
| **Metadata** | Basic (size, mtime, type) | Rich (provider-specific) |

**When to use rclone:**
- New source types (OneDrive, GDrive, Azure Blob, Dropbox)
- Quick prototyping
- Standardization across providers
- When basic metadata is sufficient

**When to use direct SDK:**
- Need provider-specific metadata (SharePoint ETags, permissions)
- Complex authentication requirements
- Advanced API features (versioning, sharing, etc.)

## See Also

- [Rclone Documentation](https://rclone.org/docs/)
- [Rclone Filtering](https://rclone.org/filtering/)
- [Example Pipeline](/home/user/aihub-core/aihub_pipeline/playground/quick_start/rclone_onedrive_pipeline.py)
