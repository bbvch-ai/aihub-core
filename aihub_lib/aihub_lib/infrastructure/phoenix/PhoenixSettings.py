from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class PhoenixSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("PHOENIX_")

    ENDPOINT: Annotated[str, Field(pattern=r"^https?://.*$")]
    AUTH_TOKEN: Annotated[SecretStr | None, Field(description="Phoenix API Token")] = None
