"""
Example Rclone OneDrive to S3 Pipeline

This example demonstrates how to use rclone to sync files from OneDrive to S3.
The same pattern works for any rclone-supported backend (SharePoint, Google Drive,
Azure Blob, Dropbox, Box, etc.).

Prerequisites:
    1. Install rclone: https://rclone.org/install/
    2. Configure OneDrive remote:
       ```bash
       rclone config create onedrive_remote onedrive
       ```
       Follow the interactive prompts for OAuth2 authentication.

    3. Or use environment variables for headless setup:
       ```bash
       export RCLONE_CONFIG_ONEDRIVE_TYPE=onedrive
       export RCLONE_CONFIG_ONEDRIVE_CLIENT_ID=your_client_id
       export RCLONE_CONFIG_ONEDRIVE_CLIENT_SECRET=your_client_secret
       export RCLONE_CONFIG_ONEDRIVE_TOKEN={"access_token":"..."}
       ```

Usage:
    # Start Dagster UI
    poetry run dagster dev -m playground.quick_start.rclone_onedrive_pipeline

    # Access UI at http://localhost:3000
    # Materialize "rclone" asset to scan OneDrive
    # Materialize "data_lake_files" asset to download files to S3
"""

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# OneDrive to S3 example
defs = default_rclone_to_datalake_definitions(
    # S3 bucket name for storage
    datalake_container_name="onedrive-sync",
    # Rclone remote (configure with: rclone config create onedrive_remote onedrive)
    source_remote="onedrive_remote:Documents",
    # Optional: subdirectory within S3 bucket
    datalake_directory_name="company-docs",
    # Include only specific file types
    include_patterns=[
        "*.pdf",
        "*.docx",
        "*.doc",
        "*.xlsx",
        "*.pptx",
        "*.txt",
        "*.md",
    ],
    # Exclude archive folders and temp files
    exclude_patterns=[
        "**/archiv/**",
        "**/Archiv/**",
        "**/archive/**",
        "**/Archive/**",
        "**/temp/**",
        "**/Temp/**",
        "**/.git/**",
        "**/node_modules/**",
        "**/__pycache__/**",
    ],
    # Schedule: Observe OneDrive daily at 2:00 AM
    observe_job_hour=2,
    observe_job_minute=0,
    # Schedule: Cleanup deleted files daily at 3:00 AM
    remove_job_hour=3,
    remove_job_minute=0,
)

# Alternative examples (uncomment to use):

# # Google Drive to S3
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="gdrive-sync",
#     source_remote="gdrive:Shared Documents",
#     include_patterns=["*.pdf", "*.docx"],
#     exclude_patterns=["**/archive/**"],
# )

# # SharePoint to S3 (via rclone)
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="sharepoint-sync",
#     source_remote="sharepoint:sites/YourSite/Shared Documents",
#     include_patterns=["*.pdf"],
# )

# # Azure Blob to S3
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="azure-sync",
#     source_remote="azure:container-name",
#     include_patterns=["*.json", "*.csv"],
# )

# # Dropbox to S3
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="dropbox-sync",
#     source_remote="dropbox:Work",
#     include_patterns=["*.pdf", "*.docx"],
# )

# # Local filesystem to S3 (using rclone)
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="local-sync",
#     source_remote="/mnt/network-share",
#     include_patterns=["*.pdf"],
# )
