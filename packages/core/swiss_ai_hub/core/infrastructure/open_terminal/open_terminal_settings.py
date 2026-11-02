from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class OpenTerminalSettings(EnvironmentSettings):
    """Where the open-terminal code sandbox runs and the key its callers share."""

    model_config = EnvironmentSettings.create_settings_config("OPEN_TERMINAL_")

    BASE_URL: Annotated[str, Field(description="The sandbox's API endpoint.")] = "http://open-terminal:8000"
    API_KEY: Annotated[SecretStr, Field(description="The bearer key every sandbox caller sends.")] = SecretStr("")
    TIMEOUT: Annotated[int, Field(description="Seconds a request may take, on top of a command's own wait.")] = 30
    MAX_FILE_BYTES: Annotated[
        int, Field(description="The largest file read whole from the sandbox, so one file cannot exhaust memory.")
    ] = 100_000_000
