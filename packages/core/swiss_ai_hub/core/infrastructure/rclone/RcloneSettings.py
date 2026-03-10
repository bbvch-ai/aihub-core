from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class RcloneSettings(EnvironmentSettings):
    """
    Global configuration for the Rclone service connection.

    Authentication:
        RC_USER and RC_PASS are required in non-dev environments where rclone
        is started with --rc-user and --rc-pass flags.
    """

    model_config = EnvironmentSettings.create_settings_config("RCLONE_")

    URL: Annotated[
        str,
        Field(description="Rclone RC API URL (e.g., http://rclone:5572)."),
    ] = "http://rclone:5572"

    RC_USER: Annotated[
        str | None,
        Field(description="RC API username for authentication."),
    ] = None

    RC_PASS: Annotated[
        SecretStr | None,
        Field(description="RC API password for authentication."),
    ] = None
