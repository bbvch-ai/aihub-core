import asyncio
import os
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
            default=5,
            ge=1,
            le=10,
            description="Maximum number of retry attempts for failed HTTP requests (1-10).",
        ),
    ]

    initial_retry_delay: Annotated[
        float,
        Field(
            default=1.0,
            ge=0.1,
            le=10.0,
            description="Initial delay in seconds between retry attempts. "
            "Delay doubles after each failed attempt (0.1-10.0).",
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

    async def _make_async_request(self, session: aiohttp.ClientSession, operation: str, params: dict) -> dict:
        """
        Make async HTTP request to rclone RC API with retry logic.

        Same pattern as SharePointResource._make_async_request()
        """
        delay = self.initial_retry_delay
        url = f"{self.rc_url}/{operation}"

        for attempt in range(self.max_retries):
            try:
                async with session.post(url, json=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                # Retry on 429 (rate limit) or 5xx errors
                if (e.status == 429 or e.status >= 500) and attempt < self.max_retries - 1:
                    retry_after = e.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after else delay
                    await asyncio.sleep(wait_time)
                    if not retry_after:
                        delay *= 2
                else:
                    raise
        raise Exception(f"Request failed after {self.max_retries} retries.")

    def _build_filter_rules(self) -> list[dict]:
        """
        Build filter rules for RC API.

        Returns list of filter rules in rclone format:
        [{"Include": True, "Pattern": "*.pdf"}, {"Include": False, "Pattern": "**/temp/**"}]
        """
        rules = []

        # Include patterns first
        if self.include_patterns:
            for pattern in self.include_patterns:
                rules.append({"Include": True, "Pattern": pattern})

        # Then exclude patterns
        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                rules.append({"Include": False, "Pattern": pattern})

        return rules

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
                "opt": {
                    "recurse": True,
                    "filesOnly": True,
                },
            }

            # Add filter rules if specified
            filter_rules = self._build_filter_rules()
            if filter_rules:
                params["opt"]["metadata"] = True  # Need metadata for filtering

            response = await self._make_async_request(session, "operations/list", params)

            # Parse response
            files_json = response.get("list", [])
            minimal_files = []

            for file_data in files_json:
                # Skip directories
                if file_data.get("IsDir", False):
                    continue

                # Apply client-side filtering (RC API doesn't support all filter features)
                if filter_rules and not self._matches_filters(file_data["Path"], filter_rules):
                    continue

                # Parse modification time
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

    def _matches_filters(self, path: str, filter_rules: list[dict]) -> bool:
        """
        Apply filter rules to a path.

        Simple glob pattern matching (not full rclone filter syntax).
        First match wins.
        """
        import fnmatch

        for rule in filter_rules:
            pattern = rule["Pattern"]
            include = rule["Include"]

            # Convert rclone glob to Python fnmatch
            # **/ means match in any subdirectory
            if pattern.startswith("**/"):
                pattern = pattern[3:]  # Remove **/
                if fnmatch.fnmatch(os.path.basename(path), pattern) or fnmatch.fnmatch(path, f"*/{pattern}"):
                    return include
            elif fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return include

        # If no include patterns, default to include
        has_includes = any(rule["Include"] for rule in filter_rules)
        return not has_includes

    def download_file(self, file_path: str) -> RcloneFile:
        """
        Download a single file from the remote and return RcloneFile with content.

        Similar to SharePointResource.download_file().
        """
        return asyncio.run(self._download_file_async(file_path))

    async def _download_file_async(self, file_path: str) -> RcloneFile:
        """Async file download using RC API."""
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Get file metadata using operations/stat
            stat_params = {"fs": self.source_remote, "remote": file_path}

            stat_response = await self._make_async_request(session, "operations/stat", stat_params)
            file_data = stat_response.get("item", {})

            # Download content using operations/cat
            # Note: operations/cat returns the file content as response body, not JSON
            cat_url = f"{self.rc_url}/[{self.source_remote}]/{file_path}"

            async with session.get(cat_url) as response:
                response.raise_for_status()
                content = await response.read()

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
