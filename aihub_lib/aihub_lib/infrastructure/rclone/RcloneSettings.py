from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class RcloneSettings(EnvironmentSettings):
    """
    Configuration settings for rclone RC API.

    Rclone provides universal cloud storage access for 70+ providers including
    OneDrive, SharePoint, Dropbox, Google Drive, S3, Azure Blob, and more.
    """

    model_config = EnvironmentSettings.create_settings_config("RCLONE_")

    URL: Annotated[
        str,
        Field(
            description="Rclone RC API endpoint URL. Use http://localhost:5572 for local development.",
        ),
    ] = "http://rclone:5572"
