from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class PlaywrightSettings(EnvironmentSettings):
    """Where the platform's browser runs. Agents have no internet access of their own, so every page they read is
    loaded by this Playwright server, which alone sits on the `egress` network."""

    model_config = EnvironmentSettings.create_settings_config("PLAYWRIGHT_")

    WS_URL: Annotated[str, Field(description="WebSocket endpoint of the Playwright server.")] = "ws://playwright:3000"
