from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class SearxngSettings(EnvironmentSettings):
    """Where the platform's SearXNG metasearch runs. Agents have no internet access of their own, so their searches
    leave the platform through this one service, the same one OpenWebUI's own search uses."""

    model_config = EnvironmentSettings.create_settings_config("SEARXNG_")

    BASE_URL: Annotated[str, Field(description="SearXNG's endpoint on the backend network.")] = "http://searxng:8080"
    TIMEOUT: Annotated[
        float, Field(description="Seconds one search may take; SearXNG waits for its slowest engine.")
    ] = 15.0
