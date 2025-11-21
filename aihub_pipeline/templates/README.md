# Pipeline Templates

Ready-to-use pipeline templates for common data sources.

## Available Templates

Each template includes:
- `.env.template` - Environment variables to copy to your `.env`
- `pipeline.py` - Complete pipeline definition (~10 lines)
- `README.md` - Setup guide with credentials instructions

## Quick Start

1. **Choose a template** (e.g., `sharepoint/`)

2. **Copy environment variables**
   ```bash
   cat templates/sources/sharepoint/.env.template >> .env
   ```

3. **Fill in credentials** (see template's README.md)

4. **Run pipeline**
   ```bash
   make playground
   ```

5. **Open Dagster UI**
   http://localhost:3000

## How Templates Work

All templates use the same simple pattern:

```python
from aihub_lib.infrastructure.rclone.RcloneSourceFactory import sharepoint_source

# Reads SHAREPOINT_* env vars
sharepoint = sharepoint_source()

# Creates remote in rclone
sharepoint.ensure_remote_exists()

# Creates Dagster pipeline
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="sharepoint",
    source_remote=f"{sharepoint.name}:",
)
```

That's it! The generic `RcloneSourceFactory` works for all 70+ rclone backends.

## Adding Custom Sources

For sources not listed above, use the generic pattern:

```python
from aihub_lib.infrastructure.rclone.RcloneSourceFactory import GenericRcloneSourceSettings

# Reads MYSOURCE_* env vars
source = GenericRcloneSourceSettings.for_source("MYSOURCE").to_rclone_source()
source.ensure_remote_exists()

defs = default_rclone_to_datalake_definitions(
    datalake_container_name="my-docs",
    source_remote=f"{source.name}:",
)
```

Environment variables:
```bash
MYSOURCE_NAME=mysource
MYSOURCE_TYPE=<rclone-backend-type>  # See https://rclone.org/docs/
MYSOURCE_CLIENT_ID=...
MYSOURCE_CLIENT_SECRET=...
# ... provider-specific options
```

## See Also

- [Rclone Documentation](https://rclone.org/docs/) - All supported backends
