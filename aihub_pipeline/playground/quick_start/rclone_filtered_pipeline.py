"""
Rclone Pipeline with Folder & Extension Filtering

This example shows how to sync specific folders and file types from a source
(local filesystem, OneDrive, SharePoint, etc.) to S3 using rclone.

Glob patterns are simpler than regex:
- *.pdf                     - All PDF files
- Project Alpha/**          - Everything in "Project Alpha" folder
- **/Documentation/**       - "Documentation" folder anywhere in tree
- **/archiv/**              - Exclude "archiv" folder anywhere
"""

from dagster import Definitions

from aihub_pipeline.util.definitions_util import default_rclone_to_datalake_definitions

# Example 1: Local filesystem to S3 (similar to your test)
# Sync specific project folders with specific extensions only
defs_local = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Users/michelefundneider/Documents/GitHub/hub/aihub-core/aihub_pipeline/playground/test_data",
    include_patterns=[
        # Include specific folders
        "Project Alpha/**",  # Everything in Project Alpha
        "Project Beta/**",  # Everything in Project Beta
        "Project Gamma/**",  # Everything in Project Gamma
        # AND only these extensions
        "*.pdf",
        "*.md",
    ],
    exclude_patterns=[
        "**/archiv/**",  # Exclude archiv folders anywhere
        "**/Archiv/**",  # Case variations
        "**/temp/**",  # Exclude temp folders
        "**/.*",  # Exclude hidden files (.git, .DS_Store, etc.)
    ],
    observe_job_hour=2,
    observe_job_minute=30,
)

# Example 2: More specific - only Documentation folders within specific projects
defs_docs_only = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Users/michelefundneider/Documents/GitHub/hub/aihub-core/aihub_pipeline/playground/test_data",
    include_patterns=[
        # Only Documentation folders within Project Alpha/Beta/Gamma
        "Project Alpha/Documentation/**",
        "Project Beta/Documentation/**",
        "Project Gamma/Documentation/**",
        # Only these extensions
        "*.pdf",
        "*.md",
        "*.docx",
    ],
    exclude_patterns=[
        "**/draft/**",  # Exclude draft folders
        "**/*_old.*",  # Exclude files ending with _old
        "**/*~",  # Exclude temp files
    ],
)

# Example 3: OneDrive to S3 (when you switch to cloud)
defs_onedrive = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="onedrive:Documents/Projects",
    include_patterns=[
        # Specific project folders
        "ProjectAlpha/**",
        "ProjectBeta/**",
        # Only PDFs and Markdown
        "*.pdf",
        "*.md",
    ],
    exclude_patterns=[
        "**/archiv/**",
        "**/Archiv/**",
        "**/Archive/**",
    ],
    observe_job_hour=3,  # Run at 3 AM
    observe_job_minute=0,
)

# Example 4: Multiple extensions with complex folder structure
defs_complex = default_rclone_to_datalake_definitions(
    datalake_container_name="spike",
    source_remote="local:C:/Projects",
    include_patterns=[
        # Documents
        "*.pdf",
        "*.docx",
        "*.xlsx",
        "*.pptx",
        # Code & configs (if needed)
        "*.py",
        "*.json",
        "*.yaml",
        # Specific important folders
        "Important/**",
        "Clients/**",
    ],
    exclude_patterns=[
        # Standard exclusions
        "**/node_modules/**",  # Node packages
        "**/.git/**",  # Git folders
        "**/venv/**",  # Python virtual envs
        "**/archiv/**",  # Archives
        "**/__pycache__/**",  # Python cache
        "**/temp/**",  # Temp folders
        "**/tmp/**",  # Temp folders
        "**/.DS_Store",  # macOS files
        "**/Thumbs.db",  # Windows files
        "**/*~",  # Backup files
        "**/~$*",  # Office temp files
    ],
)

# Choose which definitions to use (uncomment one):
defs = defs_local
# defs = defs_docs_only
# defs = defs_onedrive
# defs = defs_complex


# Glob Pattern Cheat Sheet:
# ========================
#
# Extensions:
# -----------
# *.pdf                - All PDF files anywhere
# *.{pdf,docx,xlsx}    - Multiple extensions (if rclone supports brace expansion)
#
# Folders:
# --------
# FolderName/**        - Everything in FolderName (at root level)
# **/FolderName/**     - FolderName anywhere in tree
# Folder/Sub/**        - Specific nested path
#
# Exclusions:
# -----------
# **/archiv/**         - Exclude "archiv" folder anywhere
# **/.git/**           - Exclude .git folders
# **/temp/**           - Exclude temp folders
#
# Special patterns:
# -----------------
# **/*_old.*           - Files ending with _old (any extension)
# **/*~                - Backup files (ending with ~)
# **/~$*               - Office temp files (starting with ~$)
# **/.*                - Hidden files (starting with .)
#
# Combining patterns:
# -------------------
# Include patterns are OR-ed: A file matches if it matches ANY include pattern
# Exclude patterns are OR-ed: A file is excluded if it matches ANY exclude pattern
# Exclude takes precedence: If a file matches both include and exclude, it's excluded
