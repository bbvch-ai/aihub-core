"""
SFTP Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your SFTP credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from swiss_ai_hub.core.infrastructure import sftp_source

from swiss_ai_hub.pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup SFTP remote (reads SFTP_* env vars)
sftp = sftp_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="sftp",
    rclone_config=sftp,
    source_remote=f"{sftp.name}:/path/to/folder",  # Update with your path
)
