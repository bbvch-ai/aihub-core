from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs_docs_only = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="/data/test_data",  # Absolute path inside rclone container
    rc_url="http://localhost:5572",  # Use localhost when running Dagster outside Docker
    include_patterns=[
        "Projects/Project Alpha/Documentation/*.pdf",
        "Projects/Project Gamma/Documentation/*.md",
    ],
    exclude_patterns=[
        # Version control
        "**/.git/**",
        # Build artifacts
        "**/__pycache__/**",
        "**/*.pyc",
        # OS files
        "**/.DS_Store",
        "**/Thumbs.db",
        # Temp files
        "**/temp/**",
        "**/tmp/**",
        "**/*~",
        "**/~$*",  # Office temp files
        # Archive folders
        "**/archiv/**",
        "**/Archiv/**",
        "**/archive/**",
        "**/backup/**",
    ],
    observe_job_hour=2,
    observe_job_minute=30,
)
