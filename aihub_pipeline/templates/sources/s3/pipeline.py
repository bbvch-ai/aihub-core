"""
AWS S3 Pipeline

1. Copy env vars from .env.template to your .env.dev
2. Fill in your AWS credentials
3. Run: make playground
4. Open http://localhost:3000
"""

from aihub_lib.infrastructure.rclone.RcloneSourceFactory import s3_source

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Setup S3 remote (reads S3_* env vars)
s3 = s3_source()

# Create pipeline (syncs to data lake)
defs = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    datalake_directory_name="s3",
    rclone_config=s3,
    source_remote=f"{s3.name}:bucket-name/path",  # Update with your bucket
)
