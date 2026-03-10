"""
SharePoint Pipeline

1. Copy env vars from .env.template to your .env
2. Fill in your Azure AD credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from swiss_ai_hub.core.infrastructure.rclone.RcloneSourceFactory import sharepoint_source

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup SharePoint remote (reads SHAREPOINT_* env vars)
sharepoint = sharepoint_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="sharepoint",
    rclone_config=sharepoint,
    source_remote=f"{sharepoint.name}:",
)
