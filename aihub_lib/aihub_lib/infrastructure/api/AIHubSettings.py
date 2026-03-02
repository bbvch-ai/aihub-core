from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AIHubSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AIHUB_")

    API_DEBUG_MODE: Annotated[bool, Field(description="Debug mode for development")] = False
    VERSION: Annotated[str, Field(description="Version of the app")]

    CREATE_DEFAULT_ROLES: Annotated[
        bool, Field(description="Creates default roles like AI-Hub Admin and AI-Hub User")
    ] = True

    CREATE_DEFAULT_BUCKETS: Annotated[bool, Field(description="Creates default knowledge buckets and namespaces")] = (
        True
    )

    DEFAULT_BUCKET_NAME: Annotated[str, Field(description="Name of the default knowledge bucket")] = "defaultknowledge"

    SHARED_BUCKET_NAME: Annotated[str, Field(description="Name of the shared knowledge bucket")] = "sharedknowledge"

    DEFAULT_NAMESPACE_NAME: Annotated[str, Field(description="Name of the default namespace")] = "defaultnamespace"

    SHARED_NAMESPACE_NAME: Annotated[str, Field(description="Name of the shared namespace")] = "sharednamespace"

    OPENAI_API_BASE_URL: Annotated[
        str,
        Field(
            pattern=r"^https?://.*$",
            description="Base URL of AI-Hub's OpenAI-compatible endpoint, used for Langfuse LLM connection",
        ),
    ] = "http://api:8000/api/v1/openai"

    FRONTEND_ORIGIN: Annotated[str, Field(description="Comma separated list of origins to allow CORS")]

    MONGO_MAIN_DB_NAME: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z]+$",
            description="Name of mongodb database that will be used to store data",
        ),
    ] = "aihub"
