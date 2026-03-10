from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class MongoSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("MONGO_")

    CONNECTION_STRING: Annotated[SecretStr, Field(description="Overwrite the MongoDB connection string")]
