"""
OneDrive Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Azure AD credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from swiss_ai_hub.core.infrastructure import onedrive_source

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup OneDrive remote (reads ONEDRIVE_* env vars)
onedrive = onedrive_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="onedrive",
    source_remote=f"{onedrive.name}:",
    rclone_config=onedrive,
)
