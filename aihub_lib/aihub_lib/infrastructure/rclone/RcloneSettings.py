from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class RcloneSettings(EnvironmentSettings):
    """
    Global configuration for the Rclone service connection.
    """

    model_config = EnvironmentSettings.create_settings_config("RCLONE_")

    URL: Annotated[
        str,
        Field(description="Rclone RC API URL (e.g., http://rclone:5572)."),
    ] = "http://rclone:5572"
