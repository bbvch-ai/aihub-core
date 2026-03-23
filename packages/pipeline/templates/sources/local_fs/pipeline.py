"""
Local Filesystem Pipeline

1. Set RCLONE_DATA_PATH in your .env to point to your documents folder
2. Run: make playground
3. Open http://localhost:3000

Note: No rclone remote setup needed - just use the mounted path directly!
"""

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Create pipeline (syncs to data lake)
# The /data path is mounted from RCLONE_DATA_PATH (see docker-compose)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="local_fs",
    source_remote="/data",  # Direct path to mounted volume
)
