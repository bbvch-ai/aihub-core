from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AIHubSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AIHUB_")

    API_DEBUG_MODE: Annotated[bool, Field(description="Debug mode for development")] = False
    API_VERSION: Annotated[str, Field(description="Version of the app")]

    FRONTEND_ORIGIN: Annotated[str, Field(description="Comma separated list of origins to allow CORS")]

    MONGO_MAIN_DB_NAME: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z]+$",
            description="Name of mongodb database that will be used to store data",
        ),
    ] = "aihub"
