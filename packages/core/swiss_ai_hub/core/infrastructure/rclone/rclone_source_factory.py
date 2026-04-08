import os
from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.infrastructure.rclone.rclone_source_config import RcloneBackendType, RcloneSourceConfig
from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings

RCLONE_ENV_PREFIX = "RCLONE_"


class RcloneSourceSettings(EnvironmentSettings):
    """
    Loads rclone source configuration from environment variables.

    All rclone env vars are prefixed with RCLONE_ to avoid conflicts with other tools.

    Usage:
        config = RcloneSourceSettings.load("AZUREBLOB")
        # Loads: RCLONE_AZUREBLOB_NAME, RCLONE_AZUREBLOB_TYPE, RCLONE_AZUREBLOB_ACCOUNT, etc.

    Required env vars:
        RCLONE_{SOURCE}_NAME - Remote name
        RCLONE_{SOURCE}_TYPE - Backend type (onedrive, drive, s3, azureblob, sftp, local)

    All other env vars become backend-specific options:
        RCLONE_AZUREBLOB_ACCOUNT=myaccount -> options={'account': 'myaccount'}
        RCLONE_SHAREPOINT_CLIENT_ID=xxx    -> options={'client_id': 'xxx'}
    """

    # Required
    NAME: Annotated[str, Field(description="Rclone remote name")]
    TYPE: Annotated[RcloneBackendType, Field(description="Rclone backend type")]

    _source_name: str = ""  # Set by load() classmethod

    def to_rclone_source(self) -> RcloneSourceConfig:
        """Convert settings to RcloneSourceConfig."""
        return RcloneSourceConfig(
            name=self.NAME,
            backend_type=self.TYPE,
            options=self._extract_options(),
        )

    def _extract_options(self) -> dict[str, str]:
        """
        Extract backend-specific rclone options from environment variables.

        Scans os.environ for keys matching RCLONE_{SOURCE}_{OPTION} and returns
        them as {option: value} with the prefix stripped and lowercased.
        Declared fields (NAME, TYPE) are excluded.
        """
        if not self._source_name:
            return {}
        env_prefix = f"{RCLONE_ENV_PREFIX}{self._source_name.upper()}_"
        known_fields = {f.upper() for f in self.model_fields}
        return {
            key[len(env_prefix) :].lower(): value
            for key, value in os.environ.items()
            if key.startswith(env_prefix) and key[len(env_prefix) :] not in known_fields
        }

    @classmethod
    def load(cls, source: str) -> RcloneSourceConfig:
        """Load config for a source (e.g., 'AZUREBLOB' loads RCLONE_AZUREBLOB_* env vars)."""
        env_prefix = f"{RCLONE_ENV_PREFIX}{source.upper()}_"

        class PrefixedSettings(cls):
            model_config = EnvironmentSettings.create_settings_config(env_prefix, extra="allow")
            _source_name: str = source

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
