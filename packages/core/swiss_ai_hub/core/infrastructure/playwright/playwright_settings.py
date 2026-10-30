from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class PlaywrightSettings(EnvironmentSettings):
    """Where the platform's browser runs and how it leaves the platform. Agents have no internet access of their own,
    so every page they read is loaded by this Playwright server, whose only way out is `browser-proxy`."""

    model_config = EnvironmentSettings.create_settings_config("PLAYWRIGHT_")

    WS_URL: Annotated[str, Field(description="WebSocket endpoint of the Playwright server.")] = "ws://playwright:3000"
    PROXY_URL: Annotated[
        str,
        Field(
            description="Forward proxy the browser reaches the internet through. The Playwright server connects to "
            "it, so the name resolves on its network, not the caller's."
        ),
    ] = "http://browser-proxy:3128"
