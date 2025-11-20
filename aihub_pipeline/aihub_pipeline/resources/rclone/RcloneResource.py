import asyncio
from datetime import datetime
from typing import Annotated

import aiohttp
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneResource(ConfigurableResource):
    """
    Universal cloud storage access via rclone RC API.

    Supports 70+ providers: OneDrive, SharePoint, Dropbox, Google Drive, S3, Azure Blob, etc.

    **Why RC API instead of subprocess**: Async HTTP client pattern (same as SharePointResource).
    Connection pooling, no process overhead, better error handling.

    **Why operations/stat in download**: IO Manager pattern only provides file path, not metadata.
    Alternative would require refactoring the interface to pass metadata from list operation.
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
        if ":" in self.source_remote:
            self._remote_name = self.source_remote.split(":")[0] + ":"
        else:
            self._remote_name = self.source_remote

    @staticmethod
    def _to_unix_timestamp(rfc3339_str: str | None) -> int:
        """Convert rclone RFC3339 timestamp to Unix timestamp (SourceFile requires int)."""
        if not rfc3339_str:
            return 0
        try:
            dt = datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            return 0

    async def _make_async_request(self, session: aiohttp.ClientSession, operation: str, params: dict) -> dict:
        """
        Make async HTTP request to rclone RC API with exponential backoff.

        **Why only HTTP retries**: Rclone handles backend retries (network, auth) internally.
        We only retry transient HTTP errors (429 rate limit, 5xx server errors).
        """
        delay = self.initial_retry_delay
        url = f"{self.rc_url}/{operation}"

        for attempt in range(self.max_retries):
            try:
                async with session.post(url, json=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                is_retryable = e.status == 429 or e.status >= 500
                is_last_attempt = attempt >= self.max_retries - 1

                if is_retryable and not is_last_attempt:
                    retry_after = e.headers.get("Retry-After")
                    wait_time = float(retry_after) if retry_after else delay
                    await asyncio.sleep(wait_time)
                    if not retry_after:
                        delay *= 2
                else:
                    raise
        raise Exception(f"Request failed after {self.max_retries} retries.")

    def _build_filter_opts(self) -> dict | None:
        """
        Build filter options for rclone RC API.

        **Why FilterRule instead of IncludeRule/ExcludeRule**: Avoids rclone warning about
        indeterminate parsing order. FilterRule uses + (include) and - (exclude) prefixes.
        See: https://rclone.org/filtering/
        """
        if not self.include_patterns and not self.exclude_patterns:
            return None

        filter_rules = []

        if self.include_patterns:
            for pattern in self.include_patterns:
                filter_rules.append(f"+ {pattern}")

        if self.exclude_patterns:
            for pattern in self.exclude_patterns:
                filter_rules.append(f"- {pattern}")

        if self.include_patterns:
            filter_rules.append("- **")

        return {"FilterRule": filter_rules}

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        return asyncio.run(self._fetch_minimal_files_async())

    async def _fetch_minimal_files_async(self) -> list[MinimalRcloneFile]:
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=60)
        connector = aiohttp.TCPConnector(limit=5)

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            params = {
                "fs": self.source_remote,
                "remote": "",
                "opt": {"recurse": True, "filesOnly": True, "showHash": True},
            }

            filter_opts = self._build_filter_opts()
            if filter_opts:
                params["_filter"] = filter_opts

            response = await self._make_async_request(session, "operations/list", params)
            return [self._parse_minimal_file(f) for f in response.get("list", [])]

    def _parse_minimal_file(self, file_data: dict) -> MinimalRcloneFile:
        assert not file_data.get("IsDir", False), f"Unexpected directory: {file_data['Path']}"
        return MinimalRcloneFile(
            name=file_data["Name"],
            path=file_data["Path"],
            size=file_data.get("Size", 0),
            modified=self._to_unix_timestamp(file_data.get("ModTime")),
            remote=self._remote_name,
            is_dir=False,
            mime_type=file_data.get("MimeType"),
            id=file_data.get("ID"),
            hashes=file_data.get("Hashes"),
        )

    def download_file(self, file_path: str) -> RcloneFile:
        return asyncio.run(self._download_file_async(file_path))

    async def _download_file_async(self, file_path: str) -> RcloneFile:
        """
        **Why operations/stat + core/command**: IO Manager only provides file path.
        Need stat for metadata, then cat for content (RC API has no operations/cat).

        **Why created defaults to modified**: Most cloud backends don't expose BirthTime.
        Google Drive provides it with --drive-use-created-date, but Dropbox/OneDrive don't.
        """
        timeout = aiohttp.ClientTimeout(total=None, connect=10, sock_read=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            stat_params = {"fs": self.source_remote, "remote": file_path}
            stat_response = await self._make_async_request(session, "operations/stat", stat_params)
            metadata = stat_response.get("item", {})

            full_path = f"{self.source_remote}/{file_path}"
            cat_params = {"command": "cat", "arg": [full_path], "returnType": "STREAM"}

            async with session.post(f"{self.rc_url}/core/command", json=cat_params) as response:
                response.raise_for_status()
                content = await response.read()

            modified = self._to_unix_timestamp(metadata.get("ModTime"))
            created = self._to_unix_timestamp(metadata.get("BirthTime")) or modified

            return RcloneFile(
                name=metadata["Name"],
                path=metadata["Path"],
                content=content,
                size=metadata.get("Size", 0),
                modified=modified,
                created=created,
                content_type=metadata.get("MimeType"),
                remote=self._remote_name,
                remote_path=metadata["Path"],
                mime_type=metadata.get("MimeType"),
                id=metadata.get("ID"),
            )
