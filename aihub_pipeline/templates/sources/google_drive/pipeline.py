"""
Google Drive Pipeline - Simple Version

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Google OAuth credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import google_drive_source

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup Google Drive remote (reads GDRIVE_* env vars)
gdrive = google_drive_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="gdrive",
    source_remote=f"{gdrive.name}:",
    rclone_config=gdrive,
)
