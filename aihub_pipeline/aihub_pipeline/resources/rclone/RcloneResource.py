import asyncio
from typing import Annotated, Any

from aihub_lib.infrastructure.rclone.RcloneSettings import RcloneSettings
from aihub_lib.infrastructure.rclone.RcloneSourceConfig import RcloneSourceConfig
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.resources.rclone.RcloneClient import RcloneClient
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


def _run_async(coro):
    """
    Run an async coroutine safely, handling the case where an event loop is already running.

    This prevents RuntimeError when called from within an async context (e.g., pytest-asyncio,
    async frameworks). Uses the existing loop if available, otherwise creates a new one.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, safe to use asyncio.run()
        return asyncio.run(coro)

    # Loop is already running - run in new thread to avoid RuntimeError
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


class RcloneResource(ConfigurableResource):
    """
    Universal cloud storage access via rclone RC API.

    Wraps the RcloneClient to make it usable as a Dagster resource.
    Handles automatic remote configuration (upsert) if rclone_config_dict is provided.

    Note:
        This resource provides synchronous methods that wrap async operations.
        The async operations are executed safely even when called from within
        an existing event loop.
    """

    source_remote: Annotated[
        str,
        Field(description="Rclone remote name (e.g., 'onedrive:Documents', 's3:bucket/prefix')"),
    ]

    include_patterns: Annotated[list[str] | None, Field(description="Glob patterns to include")] = None
    exclude_patterns: Annotated[list[str] | None, Field(description="Glob patterns to exclude")] = None

    rclone_config_dict: dict[str, Any] | None = None

    _client: RcloneClient | None = PrivateAttr(default=None)

    def _get_rclone_config(self) -> RcloneSourceConfig | None:
        """Reconstruct RcloneSourceConfig from serialized dict."""
        if self.rclone_config_dict:
            return RcloneSourceConfig.model_validate(self.rclone_config_dict)
        return None

    @property
    def client(self) -> RcloneClient:
        """
        Lazy initialization of the client.
        Automatically ensures the remote exists in Rclone if config is provided.
        """
        if self._client is None:
            self._client = RcloneClient(base_url=RcloneSettings().URL, default_remote=self.source_remote)
        return self._client

    def _ensure_remote_configured(self) -> None:
        """
        Ensures the rclone remote is configured before any operation.
        """
        rclone_config = self._get_rclone_config()
        if rclone_config:
            self.client.ensure_remote(rclone_config)

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        """Fetch file metadata from rclone source (no content)."""
        self._ensure_remote_configured()
        return _run_async(self.client.list_files(include=self.include_patterns, exclude=self.exclude_patterns))

    def download_file(self, file_path: str) -> RcloneFile:
        """Download a file from the rclone source."""
        self._ensure_remote_configured()
        return _run_async(self.client.download_bytes(file_path))

    async def fetch_minimal_files_async(self) -> list[MinimalRcloneFile]:
        """Async version: Fetch file metadata from rclone source (no content)."""
        self._ensure_remote_configured()
        return await self.client.list_files(include=self.include_patterns, exclude=self.exclude_patterns)

    async def download_file_async(self, file_path: str) -> RcloneFile:
        """Async version: Download a file from the rclone source."""
        self._ensure_remote_configured()
        return await self.client.download_bytes(file_path)
