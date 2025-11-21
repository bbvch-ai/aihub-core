from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.infrastructure.rclone.RcloneSourceConfig import RcloneSourceConfig
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class GenericRcloneSourceSettings(EnvironmentSettings):
    """
    Generic rclone source configuration that reads from environment variables.

    This class can be used for ANY rclone backend type by setting the appropriate
    environment variables with a custom prefix.

    Example for SharePoint:
        SHAREPOINT_NAME=sharepoint
        SHAREPOINT_TYPE=onedrive
        SHAREPOINT_CLIENT_ID=...
        SHAREPOINT_CLIENT_SECRET=...
        SHAREPOINT_TENANT=...
        SHAREPOINT_SITE_URL=https://...
        SHAREPOINT_DRIVE_TYPE=documentLibrary
        SHAREPOINT_REGION=global

    Example for Google Drive:
        GDRIVE_NAME=gdrive
        GDRIVE_TYPE=drive
        GDRIVE_CLIENT_ID=...
        GDRIVE_CLIENT_SECRET=...

    Example for Dropbox:
        DROPBOX_NAME=dropbox
        DROPBOX_TYPE=dropbox
        DROPBOX_CLIENT_ID=...
        DROPBOX_CLIENT_SECRET=...
    """

    # Required
    NAME: Annotated[str, Field(description="Rclone remote name")]
    TYPE: Annotated[str, Field(description="Rclone backend type (onedrive, drive, dropbox, s3, etc.)")]

    # Authentication (optional, provider-specific)
    CLIENT_ID: Annotated[str | None, Field(default=None, description="OAuth2 client ID")]
    CLIENT_SECRET: Annotated[SecretStr | None, Field(default=None, description="OAuth2 client secret")]
    TENANT: Annotated[str | None, Field(default=None, description="Tenant ID (Azure AD)")]

    # OneDrive/SharePoint specific (optional)
    SITE_URL: Annotated[str | None, Field(default=None, description="SharePoint site URL")]
    DRIVE_TYPE: Annotated[
        str | None, Field(default=None, description="Drive type (personal, business, documentLibrary)")
    ]
    REGION: Annotated[str | None, Field(default=None, description="Region (global, us, de, cn)")]

    # Additional provider-specific options (optional)
    # Any additional OPTION_* environment variables will be included
    # Example: SHAREPOINT_OPTION_ACCESS_TIER=Hot

    def to_rclone_source(self) -> RcloneSourceConfig:
        """
        Convert these settings to a RcloneSourceConfig.

        This method automatically collects any OPTION_* environment variables
        and includes them in the extra_config dictionary.

        Returns:
            RcloneSourceConfig for this source.
        """
        # Build extra config from any OPTION_* env vars
        extra_config = {}
        prefix = self.model_config.get("env_prefix", "")

        # Get all environment variables with this prefix
        import os

        for key, value in os.environ.items():
            if key.startswith(prefix + "OPTION_"):
                option_name = key[len(prefix + "OPTION_") :].lower()
                extra_config[option_name] = value

        return RcloneSourceConfig(
            name=self.NAME,
            type=self.TYPE,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            tenant=self.TENANT,
            site_url=self.SITE_URL,
            drive_type=self.DRIVE_TYPE,
            region=self.REGION or "global",
            extra_config=extra_config,
        )

    @classmethod
    def for_source(cls, source_name: str) -> "GenericRcloneSourceSettings":
        """
        Create settings for a specific source by loading env vars with the source prefix.

        Example:
            ```python
            # Reads SHAREPOINT_NAME, SHAREPOINT_TYPE, SHAREPOINT_CLIENT_ID, etc.
            sharepoint = GenericRcloneSourceSettings.for_source("SHAREPOINT")

            # Reads GDRIVE_NAME, GDRIVE_TYPE, GDRIVE_CLIENT_ID, etc.
            gdrive = GenericRcloneSourceSettings.for_source("GDRIVE")
            ```
        """

        # Create a new class with custom prefix
        class SourceSettings(GenericRcloneSourceSettings):
            model_config = EnvironmentSettings.create_settings_config(f"{source_name}_")

        return SourceSettings()


def sharepoint_source() -> RcloneSourceConfig:
    """Load SharePoint source from SHAREPOINT_* environment variables."""
    return GenericRcloneSourceSettings.for_source("SHAREPOINT").to_rclone_source()


def onedrive_source() -> RcloneSourceConfig:
    """Load OneDrive source from ONEDRIVE_* environment variables."""
    return GenericRcloneSourceSettings.for_source("ONEDRIVE").to_rclone_source()


def google_drive_source() -> RcloneSourceConfig:
    """Load Google Drive source from GDRIVE_* environment variables."""
    return GenericRcloneSourceSettings.for_source("GDRIVE").to_rclone_source()


def dropbox_source() -> RcloneSourceConfig:
    """Load Dropbox source from DROPBOX_* environment variables."""
    return GenericRcloneSourceSettings.for_source("DROPBOX").to_rclone_source()


def box_source() -> RcloneSourceConfig:
    """Load Box source from BOX_* environment variables."""
    return GenericRcloneSourceSettings.for_source("BOX").to_rclone_source()


def local_fs_source() -> RcloneSourceConfig:
    """Load local filesystem source from LOCAL_FS_* environment variables."""
    return GenericRcloneSourceSettings.for_source("LOCAL_FS").to_rclone_source()
