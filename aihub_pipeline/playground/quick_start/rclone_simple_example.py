"""
Rclone Pipeline - Simple Example (Your Use Case)

This is the cleanest way to sync specific folders and extensions to S3.
Similar to your LocalFS pipeline, but with simpler glob patterns instead of regex.
"""

from dagster import Definitions

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions
from aihub_pipeline.util.rclone_pattern_utils import (
    EXCLUDE_COMMON,  # Pre-defined common exclusions
    combine_patterns,
    extension_pattern,
    folder_pattern,
)

# ============================================================================
# Option 1: Using helper functions (most readable)
# ============================================================================

# Define what you want
project_folders = ["Project Alpha", "Project Beta", "Project Gamma"]
document_extensions = [".pdf", ".md"]

defs_with_helpers = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Users/michelefundneider/Documents/GitHub/hub/aihub-core/aihub_pipeline/playground/test_data",
    include_patterns=combine_patterns(
        folder_pattern(project_folders),  # Project Alpha/**, Project Beta/**, ...
        extension_pattern(document_extensions),  # *.pdf, *.md
    ),
    exclude_patterns=EXCLUDE_COMMON,  # Excludes archiv, temp, .git, node_modules, etc.
    observe_job_hour=2,
    observe_job_minute=30,
)

# ============================================================================
# Option 2: Direct glob patterns (simplest, no helpers needed)
# ============================================================================

defs_direct = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Users/michelefundneider/Documents/GitHub/hub/aihub-core/aihub_pipeline/playground/test_data",
    include_patterns=[
        # Folders
        "Project Alpha/**",
        "Project Beta/**",
        "Project Gamma/**",
        # Extensions
        "*.pdf",
        "*.md",
    ],
    exclude_patterns=[
        "**/archiv/**",
        "**/Archiv/**",
        "**/temp/**",
        "**/.git/**",
    ],
    observe_job_hour=2,
    observe_job_minute=30,
)

# ============================================================================
# Option 3: More specific - only Documentation subfolders
# ============================================================================

from aihub_pipeline.util.rclone_pattern_utils import subfolder_pattern

defs_docs_only = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Users/michelefundneider/Documents/GitHub/hub/aihub-core/aihub_pipeline/playground/test_data",
    include_patterns=combine_patterns(
        # Only "Documentation" subfolders within project folders
        [
            "Project Alpha/Documentation/**",
            "Project Beta/Documentation/**",
            "Project Gamma/Documentation/**",
        ],
        extension_pattern([".pdf", ".md"]),
    ),
    exclude_patterns=EXCLUDE_COMMON,
    observe_job_hour=2,
    observe_job_minute=30,
)

# ============================================================================
# Choose which one to use:
# ============================================================================

# Uncomment the one you want:
defs = defs_with_helpers  # ← Recommended: Most readable
# defs = defs_direct          # ← Simplest: No imports needed
# defs = defs_docs_only       # ← Most specific: Only Documentation folders


# ============================================================================
# Quick comparison to your LocalFS example:
# ============================================================================

# YOUR LOCALFS EXAMPLE (complex regex):
# --------------------------------------
# from aihub_pipeline.util.pattern_utils import exact_match_pattern, extension_pattern
#
# defs = default_local_filesystem_to_datalake_definitions(
#     datalake_container_name="playground",
#     base_path=projects_path,
#     include_folders=[exact_match_pattern(project_folders)],           # Returns: '^(Project Alpha|Project Beta|Project Gamma)$'
#     include_subfolders=[exact_match_pattern(["Documentation"])],      # Returns: '^(Documentation)$'
#     include_extensions=[extension_pattern([".pdf", ".md"])],          # Returns: '\\.(pdf|md)$'
#     observe_job_hour=2,
#     observe_job_minute=30,
# )

# RCLONE EQUIVALENT (simple globs):
# -----------------------------------
# from aihub_pipeline.util.rclone_pattern_utils import folder_pattern, extension_pattern
#
# defs = default_rclone_to_datalake_definitions(
#     datalake_container_name="spike",
#     source_remote="local:C:/path/to/projects",
#     include_patterns=combine_patterns(
#         folder_pattern(project_folders),              # Returns: ['Project Alpha/**', 'Project Beta/**', ...]
#         extension_pattern([".pdf", ".md"]),           # Returns: ['*.pdf', '*.md']
#     ),
#     exclude_patterns=EXCLUDE_COMMON,
#     observe_job_hour=2,
#     observe_job_minute=30,
# )
#
# Benefits:
# - Same structured API as LocalFS (folder_pattern, extension_pattern)
# - Actually simpler (glob patterns are more intuitive than regex)
# - Works with 70+ cloud providers (not just local FS)
# - No need for base_path - source_remote includes the path
