from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class Neo4jSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("NEO4J_")

    URL: Annotated[str, Field(description="Connection URL for Neo4j DB Server")]
    USERNAME: Annotated[str, Field(description="Username for Neo4j DB Server")]
    PASSWORD: Annotated[SecretStr, Field(description="Password for Neo4j DB Server")]
