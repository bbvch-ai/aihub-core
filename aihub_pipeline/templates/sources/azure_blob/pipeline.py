"""
Azure Blob Storage Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Azure storage credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import GenericRcloneSourceSettings

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup Azure Blob remote (reads AZUREBLOB_* env vars)
azureblob_settings = GenericRcloneSourceSettings.for_source("AZUREBLOB")
azureblob = azureblob_settings.to_rclone_source()
azureblob.ensure_remote_exists()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    source_remote=f"{azureblob.name}:container-name/path",  # Update with your container
)
