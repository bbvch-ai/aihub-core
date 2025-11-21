from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

defs_docs_only = default_rclone_to_datalake_definitions(
    datalake_container_name="playground",
    source_remote="/data/test_data/Projects",  # Make sure to mount this in your rclone container
    include_patterns=[
        "Project Alpha/**/*.md",
        "Project Beta/**/*.md",
        "Project Gamma/**/*.md",
    ],
    exclude_patterns=[
        "**/archive/**",
    ],
    observe_job_hour=2,
    observe_job_minute=30,
)
