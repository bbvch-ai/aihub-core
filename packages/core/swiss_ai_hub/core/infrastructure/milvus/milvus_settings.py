from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class MilvusSettings(EnvironmentSettings):
    """Settings for Milvus vector database connection with optional token authentication."""

    model_config = EnvironmentSettings.create_settings_config("MILVUS_")

    URL: Annotated[str, Field(description="Connection URL for Milvus DB Server")]
    DIMENSION: Annotated[int, Field(description="Dimension of the embedding vector")]
    ROOT_PASSWORD: Annotated[
        SecretStr | None,
        Field(
            default=None,
            description=(
                "Root password for Milvus authentication. If not set, no auth is used. Username is always 'root'."
            ),
        ),
    ]

    def get_token(self) -> str | None:
        """Get the token value for Milvus authentication in format 'root:password', or None if not configured."""
        if self.ROOT_PASSWORD is None:
            return None
        return f"root:{self.ROOT_PASSWORD.get_secret_value()}"
