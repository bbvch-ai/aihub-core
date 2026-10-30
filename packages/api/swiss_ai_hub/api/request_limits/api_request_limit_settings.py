from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.settings import EnvironmentSettings


class ApiRequestLimitSettings(EnvironmentSettings):
    """Bounds on what one request may make the API hold in memory."""

    model_config = EnvironmentSettings.create_settings_config("API_REQUEST_")

    MAX_JSON_BODY_BYTES: Annotated[
        int,
        Field(
            description="Largest JSON request body accepted, in bytes. It bounds base64 files sent inline too, which "
            "grow by a third when encoded."
        ),
    ] = 64 * 1024 * 1024
