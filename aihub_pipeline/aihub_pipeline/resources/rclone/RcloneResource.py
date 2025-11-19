import json
import subprocess
from datetime import datetime
from typing import Annotated

from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneResource(ConfigurableResource):
    """
    Generic rclone-based file sync and listing resource.

    Supports any rclone backend (70+ providers) including OneDrive, SharePoint, S3,
    Azure Blob, Google Drive, Dropbox, Box, local filesystem, and more.

    **Why rclone**: Single implementation works across all cloud providers without
    provider-specific SDKs, authentication logic, or API clients.

    **Setup**: Requires rclone binary installed and configured remotes in rclone.conf.
    Use environment variables or mount secrets for authentication.

    **Architecture**: Uses subprocess to call rclone CLI commands. Mature, stable,
    and provides access to all rclone features.
    """

    source_remote: Annotated[
        str,
        Field(description="Rclone remote name and optional path (e.g., 'onedrive:Documents', 's3:bucket/prefix')"),
    ]

    target_remote: Annotated[
        str | None,
        Field(
            default=None,
            description="Rclone target remote for sync operations (e.g., 's3:bucket/path'). "
            "Required for sync operations, optional for list-only usage.",
        ),
    ] = None

    include_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Include patterns using rclone glob syntax (e.g., ['*.pdf', '*.docx']). "
            "None = include all files.",
        ),
    ]

    exclude_patterns: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: ["**/archiv/**", "**/Archiv/**"],
            description="Exclude patterns using rclone glob syntax (case-sensitive by default). "
            "Common: ['**/temp/**', '**/.git/**', '**/node_modules/**']",
        ),
    ]

    sync_deletions: Annotated[
        bool,
        Field(
            default=False,
            description="If True, use 'rclone sync' (mirrors source to target, deletes extra files). "
            "If False, use 'rclone copy' (append-only, relies on application-level cleanup).",
        ),
    ]

    max_delete: Annotated[
        int,
        Field(
            default=100,
            description="Maximum number of files to delete in single sync run (safety limit). "
            "-1 = unlimited. Only applies when sync_deletions=True.",
        ),
    ]

    dry_run: Annotated[
        bool,
        Field(
            default=False,
            description="If True, simulate operations without actual transfers (reports what would happen).",
        ),
    ]

    rclone_config_path: Annotated[
        str | None,
        Field(
            default=None,
            description="Path to rclone.conf file. None = use default location (~/.config/rclone/rclone.conf).",
        ),
    ] = None

    _remote_name: str = PrivateAttr(default="")

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        # Extract remote name from source_remote (e.g., "onedrive:Documents" -> "onedrive:")
        if ":" in self.source_remote:
            self._remote_name = self.source_remote.split(":")[0] + ":"
        else:
            self._remote_name = self.source_remote

    def _build_base_command(self) -> list[str]:
        """Build base rclone command with config path if specified."""
        cmd = ["rclone"]
        if self.rclone_config_path:
            cmd.extend(["--config", self.rclone_config_path])
        return cmd

    def _add_filter_flags(self, cmd: list[str]) -> None:
        """Add include/exclude filter flags to command."""
        if self.include_patterns:
            for pattern in self.include_patterns:
                cmd.extend(["--include", pattern])

        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                cmd.extend(["--exclude", pattern])

    def sync_files(self) -> dict[str, str | int]:
        """
        Sync files from source to target remote.

        Returns dict with stdout, stderr, and returncode.

        Raises:
            ValueError: If target_remote is not configured
            subprocess.CalledProcessError: If rclone command fails
        """
        if not self.target_remote:
            raise ValueError("target_remote must be configured for sync operations")

        operation = "sync" if self.sync_deletions else "copy"
        cmd = self._build_base_command()
        cmd.extend([operation, self.source_remote, self.target_remote])

        self._add_filter_flags(cmd)

        # Common performance flags
        cmd.extend(
            [
                "--progress",
                "--stats-one-line",
                "--fast-list",  # Faster for large directories
                "--transfers=4",  # Parallel transfers
                "--checkers=8",  # Parallel checkers
            ]
        )

        # Safety flags for sync with deletions
        if self.sync_deletions:
            cmd.extend(
                [
                    "--max-delete",
                    str(self.max_delete),
                    "--delete-after",  # Delete only after successful transfer
                ]
            )

        if self.dry_run:
            cmd.extend(["--dry-run", "-vv"])

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        """
        List all files in source remote matching configured filters.

        Returns list of MinimalRcloneFile with metadata only (no content).
        Similar to SharePointResource.fetch_minimal_files() and LocalFileSystemResource.fetch_all_files().

        Uses 'rclone lsjson' for efficient metadata-only listing.
        """
        cmd = self._build_base_command()
        cmd.extend(
            [
                "lsjson",
                self.source_remote,
                "--recursive",
                "--files-only",  # Exclude directories from results
                "--no-modtime",  # Skip modification time if not needed for performance
            ]
        )

        self._add_filter_flags(cmd)

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if not result.stdout.strip():
            return []

        files_json = json.loads(result.stdout)
        minimal_files = []

        for file_data in files_json:
            # Skip directories (double-check since --files-only should handle this)
            if file_data.get("IsDir", False):
                continue

            # Parse modification time from rclone's ISO format
            mod_time_str = file_data.get("ModTime", "")
            if mod_time_str:
                dt = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
                modified = int(dt.timestamp())
            else:
                modified = 0

            minimal_files.append(
                MinimalRcloneFile(
                    name=file_data["Name"],
                    path=file_data["Path"],
                    size=file_data.get("Size", 0),
                    modified=modified,
                    remote=self._remote_name,
                    is_dir=file_data.get("IsDir", False),
                    mime_type=file_data.get("MimeType"),
                    id=file_data.get("ID"),
                )
            )

        return minimal_files

    def download_file(self, file_path: str) -> RcloneFile:
        """
        Download a single file from the remote and return RcloneFile with content.

        Similar to SharePointResource.download_file() and LocalFileSystemResource.get_local_file().

        Args:
            file_path: Relative path of the file within the source remote

        Returns:
            RcloneFile with content and metadata
        """
        # First, get metadata using lsjson
        cmd = self._build_base_command()
        cmd.extend(["lsjson", f"{self.source_remote.rstrip('/')}/{file_path}"])

        metadata_result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        file_metadata = json.loads(metadata_result.stdout)

        if not file_metadata or len(file_metadata) == 0:
            raise FileNotFoundError(f"File not found: {file_path}")

        file_data = file_metadata[0]

        # Download file content using 'rclone cat'
        cmd = self._build_base_command()
        cmd.extend(["cat", f"{self.source_remote.rstrip('/')}/{file_path}"])

        content_result = subprocess.run(cmd, capture_output=True, check=True)

        # Parse timestamps
        mod_time_str = file_data.get("ModTime", "")
        if mod_time_str:
            dt = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
            modified = int(dt.timestamp())
            created = modified  # rclone doesn't always provide separate created time
        else:
            modified = 0
            created = 0

        return RcloneFile(
            name=file_data["Name"],
            path=file_data["Path"],
            content=content_result.stdout,
            size=file_data.get("Size", 0),
            modified=modified,
            created=created,
            content_type=file_data.get("MimeType"),
            remote=self._remote_name,
            remote_path=file_data["Path"],
            mime_type=file_data.get("MimeType"),
            id=file_data.get("ID"),
        )
