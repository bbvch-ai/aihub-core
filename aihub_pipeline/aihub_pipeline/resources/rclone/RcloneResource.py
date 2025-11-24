import asyncio
from typing import Annotated, Any

from aihub_lib.infrastructure.rclone import RcloneSourceConfig
from aihub_lib.infrastructure.rclone.RcloneSettings import RcloneSettings
from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_pipeline.resources.rclone.RcloneClient import RcloneClient
from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile


class RcloneResource(ConfigurableResource):
    """
    Universal cloud storage access via rclone RC API.
    """

    source_remote: Annotated[
        str,
        Field(description="Rclone remote name (e.g., 'onedrive:Documents', 's3:bucket/prefix')"),
    ]

    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None

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
        return asyncio.run(self.client.list_files(include=self.include_patterns, exclude=self.exclude_patterns))

    def download_file(self, file_path: str) -> RcloneFile:
        self._ensure_remote_configured()
        return asyncio.run(self.client.download_bytes(file_path))
