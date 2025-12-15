from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AIHubSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AIHUB_")

    API_DEBUG_MODE: Annotated[bool, Field(description="Debug mode for development")] = False
    API_VERSION: Annotated[str, Field(description="Version of the app")]

    CREATE_DEFAULT_ROLES: Annotated[
        bool, Field(description="Creates default roles like AI-Hub Admin and AI-Hub User")
    ] = True

    CREATE_DEFAULT_KNOWLEDGE: Annotated[
        bool, Field(description="Creates default knowledge bucket and namespace at startup")
    ] = True

    DEFAULT_KNOWLEDGE_BUCKET: Annotated[str, Field(description="Name of the default knowledge bucket to create")] = (
        "defaultknowledge"
    )

    DEFAULT_KNOWLEDGE_NAMESPACE: Annotated[
        str, Field(description="Name of the default namespace within the knowledge bucket")
    ] = "defaultnamespace"

    CREATE_SHARED_KNOWLEDGE: Annotated[
        bool, Field(description="Creates shared knowledge bucket and namespace at startup")
    ] = True

    SHARED_KNOWLEDGE_BUCKET: Annotated[str, Field(description="Name of the shared knowledge bucket to create")] = (
        "sharedknowledge"
    )

    SHARED_KNOWLEDGE_NAMESPACE: Annotated[
        str, Field(description="Name of the default namespace within the shared knowledge bucket")
    ] = "defaultnamespace"

    FRONTEND_ORIGIN: Annotated[str, Field(description="Comma separated list of origins to allow CORS")]

    MONGO_MAIN_DB_NAME: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z]+$",
            description="Name of mongodb database that will be used to store data",
        ),
    ] = "aihub"
