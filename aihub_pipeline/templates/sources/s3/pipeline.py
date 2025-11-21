"""
AWS S3 Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your AWS credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import GenericRcloneSourceSettings

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup S3 remote (reads S3_* env vars)
s3_settings = GenericRcloneSourceSettings.for_source("S3")
s3 = s3_settings.to_rclone_source()
s3.ensure_remote_exists()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    source_remote=f"{s3.name}:bucket-name/path",  # Update with your bucket
)
