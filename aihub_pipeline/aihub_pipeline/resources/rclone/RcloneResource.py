import asyncio
from typing import Annotated

from dagster import ConfigurableResource
from pydantic import Field, PrivateAttr

from aihub_lib.infrastructure.rclone import RcloneSourceConfig
from aihub_lib.infrastructure.rclone.RcloneSettings import RcloneSettings
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

    rclone_config: Annotated[
        RcloneSourceConfig | None, Field(description="Configuration to auto-create/update the remote")
    ] = None

    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = ["**/archiv/**"]

    _client: RcloneClient | None = PrivateAttr(default=None)

    @property
    def client(self) -> RcloneClient:
        """
        Lazy initialization of the client.
        Ensures the remote exists before returning the client.
        """
        if self._client is None:
            self._client = RcloneClient(base_url=RcloneSettings().URL, default_remote=self.source_remote)

            if self.rclone_config:
                self._client.ensure_remote(self.rclone_config)

        return self._client

    def fetch_minimal_files(self) -> list[MinimalRcloneFile]:
        return asyncio.run(self.client.list_files(include=self.include_patterns, exclude=self.exclude_patterns))

    def download_file(self, file_path: str) -> RcloneFile:
        return asyncio.run(self.client.download_bytes(file_path))
