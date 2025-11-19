import asyncio
from datetime import datetime
from typing import Annotated

import aiohttp
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneResource(ConfigurableResource):
    """
    Universal cloud storage adapter using rclone RC API.

    **The Universal Adapter**: Single implementation for 70+ providers (OneDrive, SharePoint,
    S3, Azure Blob, Google Drive, Dropbox, local filesystem, etc.).

    **Architecture**: Thin HTTP client → rclone daemon (handles all provider logic).
    Rclone does the heavy lifting (auth, rate limits, retries, filtering, provider quirks).
    We just make HTTP calls.

    **Why RC API**: Clean separation - rclone service handles providers, we handle Dagster pipeline.
    No subprocess overhead, no provider-specific Python code.

    **Filtering**: Uses rclone's native filtering (passed via _filter parameter).
    Much simpler than custom client-side filtering.
    """

    rc_url: Annotated[
        str,
        Field(
            default="http://aihub-rclone:5572",
            description="Rclone RC API endpoint",
        ),
    ]

    source_remote: Annotated[
        str,
        Field(description="Rclone remote:path (e.g., 'onedrive:Documents', 's3:bucket/prefix', 'local:/path')"),
    ]

    include_patterns: Annotated[
        list[str] | None,
        Field(
            default=None,
            description="Include patterns - rclone glob syntax (e.g., ['*.pdf', 'Project Alpha/**']). "
            "None = include all files.",
        ),
    ]

    exclude_patterns: Annotated[
        list[str] | None,
        Field(
            default_factory=lambda: ["**/archiv/**", "**/Archiv/**"],
            description="Exclude patterns - rclone glob syntax. Common: ['**/temp/**', '**/.git/**']",
        ),
    ]

    max_retries: Annotated[int, Field(default=3, ge=1, le=10, description="Max HTTP retry attempts")] = 3
    initial_retry_delay: Annotated[float, Field(default=1.0, ge=0.1, le=10.0, description="Retry delay (seconds)")] = (
        1.0
    )

    _remote_name: str = PrivateAttr(default="")

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        # Extract remote name (e.g., "onedrive:Documents" -> "onedrive:")
        if ":" in self.source_remote:
            self._remote_name = self.source_remote.split(":")[0] + ":"
        else:
            self._remote_name = self.source_remote

    async def _make_request(self, session: aiohttp.ClientSession, operation: str, params: dict) -> dict:
        """Make HTTP request to RC API with simple retry logic."""
        url = f"{self.rc_url}/{operation}"
        delay = self.initial_retry_delay

        for attempt in range(self.max_retries):
            try:
                async with session.post(url, json=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                # Retry on rate limit (429) or server errors (5xx)
                if (e.status == 429 or e.status >= 500) and attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    raise

        raise Exception(f"Request to {operation} failed after {self.max_retries} retries")

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        """
        List all files from source remote.

        Uses rclone's native filtering - patterns passed to RC API.
        """
        return asyncio.run(self._fetch_minimal_files_async())

    async def _fetch_minimal_files_async(self) -> list[MinimalRcloneFile]:
        """List files via RC API operations/list with native rclone filtering."""
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Build request params
            params: dict = {
                "fs": self.source_remote,
                "opt": {
                    "recurse": True,
                    "filesOnly": True,
                },
            }

            # Add rclone native filtering via _filter parameter
            # Rclone handles all the filtering - we just pass the patterns
            filter_config = {}
            if self.include_patterns:
                filter_config["IncludeRule"] = self.include_patterns
            if self.exclude_patterns:
                filter_config["ExcludeRule"] = self.exclude_patterns

            if filter_config:
                params["_filter"] = filter_config

            # Make request - rclone returns only matching files
            response = await self._make_request(session, "operations/list", params)

            # Parse file list
            files_json = response.get("list", [])
            minimal_files = []

            for file_data in files_json:
                # Skip directories (rclone might return them anyway)
                if file_data.get("IsDir", False):
                    continue

                # Parse timestamp
                mod_time_str = file_data.get("ModTime", "")
                modified = 0
                if mod_time_str:
                    try:
                        dt = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
                        modified = int(dt.timestamp())
                    except ValueError:
                        pass

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
        """Download single file with content."""
        return asyncio.run(self._download_file_async(file_path))

    async def _download_file_async(self, file_path: str) -> RcloneFile:
        """Download file via RC API operations/cat."""
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Get file metadata
            stat_params = {"fs": self.source_remote, "remote": file_path}
            stat_response = await self._make_request(session, "operations/stat", stat_params)
            file_data = stat_response.get("item", {})

            # Download content using special [remote] URL syntax
            # RC API serves file content at /[remote:path]/file/path
            cat_url = f"{self.rc_url}/[{self.source_remote}]/{file_path}"

            async with session.get(cat_url) as response:
                response.raise_for_status()
                content = await response.read()

            # Parse timestamps
            mod_time_str = file_data.get("ModTime", "")
            modified = created = 0
            if mod_time_str:
                try:
                    dt = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00"))
                    modified = created = int(dt.timestamp())
                except ValueError:
                    pass

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
