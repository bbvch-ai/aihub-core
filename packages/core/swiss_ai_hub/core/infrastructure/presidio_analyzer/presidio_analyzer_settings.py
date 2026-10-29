from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class PresidioAnalyzerSettings(EnvironmentSettings):
    """Where the deployment's Presidio analyzer runs and the key its callers share (the gateway reads the same two)."""

    model_config = EnvironmentSettings.create_settings_config("PRESIDIO_ANALYZER_")

    API_BASE: Annotated[str, Field(description="The analyzer's API endpoint.")] = "http://presidio-analyzer:3000"
    API_KEY: Annotated[SecretStr, Field(description="The bearer key every analyzer caller sends.")] = SecretStr("")
    TIMEOUT: Annotated[
        int, Field(description="Seconds one analysis may take; a 20k-token text needs about 50 on 4 CPU threads.")
    ] = 150
