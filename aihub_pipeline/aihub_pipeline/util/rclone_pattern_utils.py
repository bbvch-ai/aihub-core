"""
Helper functions for creating rclone glob patterns.

These helpers make it easy to create include/exclude patterns for rclone filtering
without manually writing glob patterns.

Examples:
    >>> from aihub_pipeline.util.rclone_pattern_utils import (
    ...     folder_pattern,
    ...     extension_pattern,
    ...     exclude_folder_pattern,
    ... )
    ...
    >>> # Include specific folders
    >>> folder_pattern(["Project Alpha", "Project Beta"])
    ['Project Alpha/**', 'Project Beta/**']
    ...
    >>> # Include specific extensions
    >>> extension_pattern([".pdf", ".md", ".docx"])
    ['*.pdf', '*.md', '*.docx']
    ...
    >>> # Exclude folders anywhere in tree
    >>> exclude_folder_pattern(["archiv", "temp"])
    ['**/archiv/**', '**/temp/**']
"""

from typing import Annotated


def folder_pattern(
    folders: Annotated[list[str], "List of folder names to include (at root level)"],
) -> list[str]:
    """
    Create glob patterns to include specific folders at root level.

    Examples:
        >>> folder_pattern(["Project Alpha", "Project Beta"])
        ['Project Alpha/**', 'Project Beta/**']

        >>> folder_pattern(["Clients", "Important"])
        ['Clients/**', 'Important/**']
    """
    return [f"{folder}/**" for folder in folders]


def subfolder_pattern(
    subfolders: Annotated[list[str], "List of subfolder names to include anywhere in tree"],
) -> list[str]:
    """
    Create glob patterns to include specific subfolders anywhere in directory tree.

    Examples:
        >>> subfolder_pattern(["Documentation", "Reports"])
        ['**/Documentation/**', '**/Reports/**']

        >>> subfolder_pattern(["src", "tests"])
        ['**/src/**', '**/tests/**']
    """
    return [f"**/{subfolder}/**" for subfolder in subfolders]


def extension_pattern(
    extensions: Annotated[list[str], "List of file extensions (with or without leading dot)"],
) -> list[str]:
    """
    Create glob patterns for file extensions.

    Examples:
        >>> extension_pattern([".pdf", ".docx", ".xlsx"])
        ['*.pdf', '*.docx', '*.xlsx']

        >>> extension_pattern(["pdf", "md"])
        ['*.pdf', '*.md']
    """
    # Remove leading dots if present, then add asterisk
    clean_exts = [ext.lstrip(".") for ext in extensions]
    return [f"*.{ext}" for ext in clean_exts]


def exclude_folder_pattern(
    folders: Annotated[list[str], "List of folder names to exclude anywhere in tree"],
) -> list[str]:
    """
    Create glob patterns to exclude folders anywhere in directory tree.

    Examples:
        >>> exclude_folder_pattern(["archiv", "temp", "backup"])
        ['**/archiv/**', '**/temp/**', '**/backup/**']

        >>> exclude_folder_pattern(["node_modules", ".git"])
        ['**/node_modules/**', '**/.git/**']
    """
    return [f"**/{folder}/**" for folder in folders]


def exclude_file_pattern(
    patterns: Annotated[list[str], "List of filename patterns to exclude"],
) -> list[str]:
    """
    Create glob patterns to exclude specific files or file patterns.

    Examples:
        >>> exclude_file_pattern([".DS_Store", "Thumbs.db"])
        ['**/.DS_Store', '**/Thumbs.db']

        >>> exclude_file_pattern(["*_old.*", "*~", "~$*"])
        ['**/*_old.*', '**/*~', '**/~$*']
    """
    return [f"**/{pattern}" for pattern in patterns]


def combine_patterns(*pattern_lists: list[str]) -> list[str]:
    """
    Combine multiple pattern lists into a single list.

    Examples:
        >>> folders = folder_pattern(["Project Alpha", "Project Beta"])
        >>> extensions = extension_pattern([".pdf", ".md"])
        >>> combine_patterns(folders, extensions)
        ['Project Alpha/**', 'Project Beta/**', '*.pdf', '*.md']

        >>> includes = extension_pattern([".pdf"])
        >>> excludes = exclude_folder_pattern(["temp"])
        >>> combine_patterns(includes, excludes)
        ['*.pdf', '**/temp/**']
    """
    result = []
    for patterns in pattern_lists:
        result.extend(patterns)
    return result


# Common exclusion patterns that can be reused
EXCLUDE_VERSION_CONTROL = [
    "**/.git/**",
    "**/.svn/**",
    "**/.hg/**",
]

EXCLUDE_DEPENDENCIES = [
    "**/node_modules/**",
    "**/venv/**",
    "**/.venv/**",
    "**/vendor/**",
    "**/packages/**",
]

EXCLUDE_BUILD_ARTIFACTS = [
    "**/dist/**",
    "**/build/**",
    "**/target/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/bin/**",
    "**/obj/**",
]

EXCLUDE_OS_FILES = [
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/desktop.ini",
    "**/$RECYCLE.BIN/**",
]

EXCLUDE_TEMP_FILES = [
    "**/temp/**",
    "**/tmp/**",
    "**/*~",
    "**/~$*",  # Office temp files
    "**/*.tmp",
    "**/*.bak",
]

EXCLUDE_ARCHIVE_FOLDERS = [
    "**/archiv/**",
    "**/Archiv/**",
    "**/Archive/**",
    "**/archive/**",
    "**/backup/**",
    "**/Backup/**",
]

# Combine all common exclusions
EXCLUDE_COMMON = combine_patterns(
    EXCLUDE_VERSION_CONTROL,
    EXCLUDE_DEPENDENCIES,
    EXCLUDE_BUILD_ARTIFACTS,
    EXCLUDE_OS_FILES,
    EXCLUDE_TEMP_FILES,
    EXCLUDE_ARCHIVE_FOLDERS,
)
