from typing import Annotated

import httpx
from pydantic import BaseModel, Field, SecretStr

from aihub_lib.infrastructure.rclone.RcloneSettings import RcloneSettings


class RcloneSourceConfig(BaseModel):
    """
    Configuration for an rclone remote source.

    This model represents a cloud storage source that can be accessed via rclone.
    Each source is configured with provider-specific credentials and settings.

    Example:
        ```python
        sharepoint = RcloneSourceConfig(
            name="sharepoint",
            type="onedrive",
            client_id="...",
            client_secret=SecretStr("..."),
            tenant="...",
            drive_id="...",
            drive_type="documentLibrary",
        )
        ```
    """

    name: Annotated[str, Field(description="Remote name (e.g., 'sharepoint', 'gdrive', 'dropbox')")]
    type: Annotated[str, Field(description="Rclone backend type (e.g., 'onedrive', 'drive', 'dropbox', 's3')")]

    # OAuth/Authentication
    client_id: Annotated[str | None, Field(description="OAuth2 client ID")] = None
    client_secret: Annotated[SecretStr | None, Field(description="OAuth2 client secret")] = None
    tenant: Annotated[str | None, Field(description="Tenant ID (for OneDrive/SharePoint)")] = None

    # OneDrive/SharePoint specific
    site_url: Annotated[str | None, Field(description="SharePoint site URL (easier than drive_id)")] = None
    drive_type: Annotated[str | None, Field(description="Drive type: personal, business, documentLibrary")] = None
    region: Annotated[str, Field(description="Region: global, us, de, cn")] = "global"

    # Advanced
    extra_config: Annotated[dict[str, str], Field(description="Additional provider-specific configuration")] = dict()

    def to_rclone_options(self) -> dict[str, str]:
        """
        Convert this source config to rclone config options.

        Returns a dictionary of option names and values that can be passed to
        the rclone RC API config/create endpoint.
        """
        options = {}

        if self.client_id:
            options["client_id"] = self.client_id
        if self.client_secret:
            options["client_secret"] = self.client_secret.get_secret_value()
        if self.tenant:
            options["tenant"] = self.tenant
            options["client_credentials"] = "true"
        if self.site_url:
            options["config_site_url"] = self.site_url
            options["config_type"] = "url"  # Required when using site_url
        if self.drive_type:
            options["drive_type"] = self.drive_type
        if self.region:
            options["region"] = self.region

        # Add extra config
        options.update(self.extra_config)

        return options

    def create_remote(self) -> None:
        """
        Create this remote in rclone via RC API.

        This method calls the rclone RC API config/create endpoint to dynamically
        create the remote without requiring environment variables or config files.
        """
        rc_url = RcloneSettings().URL

        options = self.to_rclone_options()

        # Build parameters for config/create
        params = {
            "name": self.name,
            "type": self.type,
            "parameters": options,
        }

        # Call RC API
        print("Creating remote...")
        response = httpx.post(f"{rc_url}/config/create", json=params)
        response.raise_for_status()

    def ensure_remote_exists(self) -> None:
        """
        Ensure this remote exists in rclone, creating it if necessary.

        This method checks if the remote exists and creates it if it doesn't.
        Safe to call multiple times (idempotent).
        """
        rc_url = RcloneSettings().URL

        try:
            response = httpx.post(f"{rc_url}/config/get", json={"name": self.name})
            response.raise_for_status()

            config = response.json()

            # Empty response means remote doesn't exist
            if not config or len(config) == 0:
                self.create_remote()
        except httpx.HTTPStatusError:
            self.create_remote()

    @classmethod
    def from_sharepoint(
        cls,
        name: str,
        client_id: str,
        client_secret: str,
        tenant: str,
        site_url: str,
        region: str = "global",
    ) -> "RcloneSourceConfig":
        """
        Create a SharePoint source configuration.
        """
        return cls(
            name=name,
            type="onedrive",
            client_id=client_id,
            client_secret=SecretStr(client_secret),
            tenant=tenant,
            site_url=site_url,
            drive_type="documentLibrary",
            region=region,
        )

    @classmethod
    def from_onedrive(
        cls,
        name: str,
        client_id: str,
        client_secret: str,
        tenant: str,
        drive_type: str = "business",
        region: str = "global",
    ) -> "RcloneSourceConfig":
        """
        Create a OneDrive source configuration.
        """
        return cls(
            name=name,
            type="onedrive",
            client_id=client_id,
            client_secret=SecretStr(client_secret),
            tenant=tenant,
            drive_type=drive_type,
            region=region,
        )

    @classmethod
    def from_google_drive(
        cls,
        name: str,
        client_id: str,
        client_secret: str,
    ) -> "RcloneSourceConfig":
        """
        Create a Google Drive source configuration.
        """
        return cls(
            name=name,
            type="drive",
            client_id=client_id,
            client_secret=SecretStr(client_secret),
        )
