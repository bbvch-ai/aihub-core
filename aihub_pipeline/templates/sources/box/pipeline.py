"""
Box Pipeline - Simple Version

1. Copy env vars from .env.template to your .env.dev
2. Fill in your Box app credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import box_source

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup Box remote (reads BOX_* env vars)
box = box_source()
box.ensure_remote_exists()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    source_remote=f"{box.name}:",
)
