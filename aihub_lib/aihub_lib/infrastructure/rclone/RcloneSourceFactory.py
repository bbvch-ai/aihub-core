import os
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings
from aihub_lib.infrastructure.rclone.RcloneSourceConfig import RcloneSourceConfig, RcloneBackendType


class GenericRcloneSourceSettings(EnvironmentSettings):
    """
    Generic rclone source configuration that reads from environment variables.

    Supports dynamic prefixes (e.g. SHAREPOINT_, GDRIVE_) and automatically
    maps to the RcloneSourceConfig domain model.
    """

    model_config = SettingsConfigDict(extra="ignore")

    # Required
    NAME: Annotated[str, Field(description="Rclone remote name")]
    TYPE: Annotated[RcloneBackendType, Field(description="Rclone backend type")]

    # Authentication
    CLIENT_ID: Annotated[str | None, Field(default=None, description="OAuth2 client ID")] = None
    CLIENT_SECRET: Annotated[SecretStr | None, Field(default=None, description="OAuth2 client secret")] = None
    TENANT: Annotated[str | None, Field(default=None, description="Tenant ID (Azure AD)")] = None

    # OneDrive/SharePoint specific
    SITE_URL: Annotated[str | None, Field(default=None, description="SharePoint site URL")] = None
    DRIVE_TYPE: Annotated[
        str | None, Field(default=None, description="Drive type (personal, business, documentLibrary)")
    ] = None

    def _get_extra_options(self) -> dict[str, str]:
        """
        Scans environment variables for keys starting with {PREFIX}OPTION_.
        Example: SHAREPOINT_OPTION_ACCESS_TIER -> access_tier
        """
        extra_config = {}
        # Retrieve the prefix used to initialize this instance (e.g., "SHAREPOINT_")
        prefix = self.model_config.get("env_prefix", "")

        if not prefix:
            return {}

        # We iterate os.environ because pydantic filters out extra fields based on the 'extra=ignore' config.
        for key, value in os.environ.items():
            if key.startswith(prefix + "OPTION_"):
                # Remove prefix and "OPTION_", then lowercase
                # e.g. SHAREPOINT_OPTION_READ_ONLY -> read_only
                clean_key = key[len(prefix + "OPTION_") :].lower()
                extra_config[clean_key] = value

        return extra_config

    def to_rclone_source(self) -> RcloneSourceConfig:
        """
        Convert settings to RcloneSourceConfig domain model.
        """
        return RcloneSourceConfig(
            name=self.NAME,
            backend_type=self.TYPE,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            tenant=self.TENANT,
            site_url=self.SITE_URL,
            drive_type=self.DRIVE_TYPE,
            extra_config=self._get_extra_options(),
        )

    @classmethod
    def load(cls, prefix: str) -> RcloneSourceConfig:
        """
        Factory method to load configuration for a specific source prefix.
        """
        clean_prefix = f"{prefix.upper().rstrip('_')}_"

        class ScopedSettings(cls):
            model_config = SettingsConfigDict(env_prefix=clean_prefix, extra="ignore")

        settings = ScopedSettings()
        return settings.to_rclone_source()


def sharepoint_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("SHAREPOINT")


def onedrive_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("ONEDRIVE")


def google_drive_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("GDRIVE")


def s3_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("S3")


def local_fs_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("LOCAL_FS")


def azure_blob_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("AZUREBLOB")


def sftp_source() -> RcloneSourceConfig:
    return GenericRcloneSourceSettings.load("SFTP")
