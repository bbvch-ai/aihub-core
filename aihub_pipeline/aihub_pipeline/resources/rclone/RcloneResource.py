import asyncio
from datetime import datetime
from typing import Annotated

import aiohttp
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneResource(ConfigurableResource):
    """
    Rclone RC API-based resource for universal cloud storage sync.

    Uses rclone's Remote Control API for efficient async operations across 70+ cloud
    providers (OneDrive, SharePoint, S3, Azure Blob, Google Drive, Dropbox, etc.).

    **Why RC API**: Follows same pattern as SharePointResource (async HTTP client).
    More efficient than subprocess (connection pooling, no process overhead).

    **Architecture**: HTTP calls to rclone daemon running as Docker service.
    Same pattern as SharePoint → Graph API, but rclone → RC API.

    **Setup**: Requires rclone service running in Docker Compose with RC API enabled.
    Configure remotes via environment variables or rclone.conf.
    """

    rc_url: Annotated[
        str,
        Field(
            default="http://aihub-rclone:5572",
            description="Rclone RC API URL (default: http://aihub-rclone:5572)",
        ),
    ]

    source_remote: Annotated[
        str,
        Field(description="Rclone remote name and optional path (e.g., 'onedrive:Documents', 's3:bucket/prefix')"),
    ]

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

    max_retries: Annotated[
        int,
        Field(
            default=3,
            ge=1,
            le=5,
            description="Maximum HTTP retry attempts for rate limit/server errors (1-5). "
            "Rclone handles backend retries internally.",
        ),
    ]

    initial_retry_delay: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.1,
            le=5.0,
            description="Initial HTTP retry delay in seconds (0.1-5.0). Doubles after each attempt.",
        ),
    ]

    _remote_name: str = PrivateAttr(default="")

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        # Extract remote name from source_remote (e.g., "onedrive:Documents" -> "onedrive:")
        if ":" in self.source_remote:
            self._remote_name = self.source_remote.split(":")[0] + ":"
        else:
            self._remote_name = self.source_remote

    @staticmethod
    def _parse_rclone_timestamp(mod_time_str: str | None) -> int:
        """Parse rclone ISO timestamp to Unix timestamp. Returns 0 if missing/invalid."""
        if not mod_time_str:
            return 0
        try:
            dt = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            return 0

    async def _make_async_request(self, session: aiohttp.ClientSession, operation: str, params: dict) -> dict:
        """
        Make async HTTP request to rclone RC API with retry logic.

        Only retries transient HTTP errors (rate limits, server errors).
        Rclone handles backend retries (network, auth, etc.) internally.
        """
        delay = self.initial_retry_delay
        url = f"{self.rc_url}/{operation}"

        for attempt in range(self.max_retries):
            try:
                async with session.post(url, json=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                # Only retry on transient HTTP errors: 429 (rate limit) or 5xx (server errors)
                is_retryable = e.status == 429 or e.status >= 500
                is_last_attempt = attempt >= self.max_retries - 1

                if is_retryable and not is_last_attempt:
                    # Honor Retry-After header if present
                    retry_after = e.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after else delay
                    await asyncio.sleep(wait_time)
                    if not retry_after:
                        delay *= 2  # Exponential backoff
                else:
                    raise
        raise Exception(f"Request failed after {self.max_retries} retries.")

    def _build_filter_opts(self) -> dict | None:
        """
        Build filter options for rclone RC API.

        Returns filter dict in rclone format or None if no filters.
        RC API uses FilterRule with + (include) and - (exclude) prefixes.
        Rclone filter syntax: https://rclone.org/filtering/
        """
        if not self.include_patterns and not self.exclude_patterns:
            return None

        # Use FilterRule instead of separate IncludeRule/ExcludeRule to avoid warning
        filter_rules = []

        # Add include patterns with + prefix
        if self.include_patterns:
            for pattern in self.include_patterns:
                filter_rules.append(f"+ {pattern}")

        # Add exclude patterns with - prefix
        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                filter_rules.append(f"- {pattern}")

        # If we have include patterns, exclude everything else at the end
        if self.include_patterns:
            filter_rules.append("- **")

        return {"FilterRule": filter_rules}

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        """
        List all files from rclone remote using RC API.

        Synchronous wrapper around async implementation (same as SharePoint pattern).
        """
        return asyncio.run(self._fetch_minimal_files_async())

    async def _fetch_minimal_files_async(self) -> list[MinimalRcloneFile]:
        """
        Async implementation of file listing.

        Uses rclone RC API operations/list endpoint.
        """
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)
        connector = aiohttp.TCPConnector(limit=5)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Build parameters for operations/list
            params = {
                "fs": self.source_remote,
                "remote": "",  # Remote path within fs (empty = root of fs)
                "opt": {
                    "recurse": True,
                    "filesOnly": True,
                    "showHash": True,  # Get hash checksums from backend for content-based change detection
                },
            }

            # Add native rclone filters if specified
            # IMPORTANT: Filters go in "_filter" at top level, NOT in "opt"!
            filter_opts = self._build_filter_opts()
            if filter_opts:
                params["_filter"] = filter_opts

            response = await self._make_async_request(session, "operations/list", params)

            # Parse response (rclone already filtered server-side with filesOnly=True)
            files_json = response.get("list", [])
            minimal_files = []

            for file_data in files_json:
                # filesOnly=True ensures we only get files, but assert just to be safe
                assert not file_data.get("IsDir", False), f"Unexpected directory in response: {file_data['Path']}"

                minimal_files.append(
                    MinimalRcloneFile(
                        name=file_data["Name"],
                        path=file_data["Path"],
                        size=file_data.get("Size", 0),
                        modified=self._parse_rclone_timestamp(file_data.get("ModTime")),
                        remote=self._remote_name,
                        is_dir=False,  # filesOnly=True guarantees this
                        mime_type=file_data.get("MimeType"),
                        id=file_data.get("ID"),
                        hashes=file_data.get("Hashes"),  # Content-based checksums from backend
                    )
                )

            return minimal_files

    def download_file(self, file_path: str) -> RcloneFile:
        """
        Download a single file from the remote and return RcloneFile with content.

        Similar to SharePointResource.download_file().
        """
        return asyncio.run(self._download_file_async(file_path))

    async def _download_file_async(self, file_path: str) -> RcloneFile:
        """
        Async file download using RC API.

        NOTE: We need operations/stat to get metadata (size, mtime, mime type) since
        download_file() is called with only the file path. Alternative would be to
        change the interface to accept metadata from list operation, but that requires
        refactoring the IO Manager pattern.
        """
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Get file metadata using operations/stat
            stat_params = {"fs": self.source_remote, "remote": file_path}
            stat_response = await self._make_async_request(session, "operations/stat", stat_params)
            file_data = stat_response.get("item", {})

            # Download content using core/command with cat
            # RC API doesn't have operations/cat, so we use core/command to run rclone cat
            full_path = f"{self.source_remote}/{file_path}"
            cat_params = {"command": "cat", "arg": [full_path], "returnType": "STREAM"}
            cat_url = f"{self.rc_url}/core/command"

            async with session.post(cat_url, json=cat_params) as response:
                response.raise_for_status()
                content = await response.read()

            # Parse timestamps using helper
            modified = self._parse_rclone_timestamp(file_data.get("ModTime"))
            created = modified  # rclone doesn't always provide separate created time

            return RcloneFile(
                name=file_data["Name"],
                path=file_data["Path"],
                content=content,
                size=file_data.get("Size", 0),
                modified=modified,
                created=created,
                content_type=file_data.get("MimeType"),
                remote=self._remote_name,
                remote_path=file_data["Path"],
                mime_type=file_data.get("MimeType"),
                id=file_data.get("ID"),
            )
