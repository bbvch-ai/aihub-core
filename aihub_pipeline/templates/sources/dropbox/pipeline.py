"""
Dropbox Pipeline - Simple Version

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Dropbox app credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import dropbox_source

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup Dropbox remote (reads DROPBOX_* env vars)
dropbox = dropbox_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    source_remote=f"{dropbox.name}:",
    rclone_config=dropbox,
)
