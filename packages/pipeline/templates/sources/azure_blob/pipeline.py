"""
Azure Blob Storage Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Azure storage credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from swiss_ai_hub.core.infrastructure import azure_blob_source

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup Azure Blob remote (reads AZUREBLOB_* env vars)
azureblob = azure_blob_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="azureblob",
    source_remote=f"{azureblob.name}:playground",  # Update with your container / path
    rclone_config=azureblob,
)
