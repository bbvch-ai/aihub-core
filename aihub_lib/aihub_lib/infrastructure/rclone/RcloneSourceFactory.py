from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.infrastructure.rclone.RcloneSourceConfig import RcloneBackendType, RcloneSourceConfig
from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class RcloneSourceSettings(EnvironmentSettings):
    """
    Generic rclone source configuration that reads from environment variables.

    Supports dynamic prefixes (e.g. SHAREPOINT_, GDRIVE_) and automatically
    maps to the RcloneSourceConfig domain model.
    """

    # Required
    NAME: Annotated[str, Field(description="Rclone remote name")]
    TYPE: Annotated[RcloneBackendType, Field(description="Rclone backend type")]

    # Authentication (optional)
    CLIENT_ID: str | None = None
    CLIENT_SECRET: SecretStr | None = None
    TENANT: str | None = None

    # OneDrive/SharePoint specific (optional)
    SITE_URL: str | None = None
    DRIVE_TYPE: str | None = None

    def to_rclone_source(self) -> RcloneSourceConfig:
        """Convert settings to RcloneSourceConfig."""
        return RcloneSourceConfig(
            name=self.NAME,
            backend_type=self.TYPE,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            tenant=self.TENANT,
            site_url=self.SITE_URL,
            drive_type=self.DRIVE_TYPE,
            extra_config=self._extract_options(),
        )

    def _extract_options(self) -> dict[str, str]:
        """Extract OPTION_* env vars into rclone config format."""
        options = {}
        for key, value in (self.model_extra or {}).items():
            if "option_" in key.lower():
                config_key = key.lower().split("option_", 1)[1]
                options[config_key] = str(value)
        return options

    @classmethod
    def load(cls, prefix: str) -> RcloneSourceConfig:
        """Load config for a prefix (e.g., 'AZUREBLOB' loads AZUREBLOB_* env vars)."""

        class PrefixedSettings(cls):
            model_config = EnvironmentSettings.create_settings_config(f"{prefix}_", extra="allow")

        return PrefixedSettings().to_rclone_source()


def sharepoint_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("SHAREPOINT")


def onedrive_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("ONEDRIVE")


def google_drive_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("GDRIVE")


def s3_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("S3")


def azure_blob_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("AZUREBLOB")


def sftp_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("SFTP")


def local_fs_source() -> RcloneSourceConfig:
    return RcloneSourceSettings.load("LOCAL_FS")
