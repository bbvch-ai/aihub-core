from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class MilvusSettings(EnvironmentSettings):
    """Settings for Milvus vector database connection with optional token authentication."""

    model_config = EnvironmentSettings.create_settings_config("MILVUS_")

    URL: Annotated[str, Field(description="Connection URL for Milvus DB Server")]
    DIMENSION: Annotated[int, Field(description="Dimension of the embedding vector")]
    TOKEN: Annotated[
        SecretStr | None,
        Field(
            default=None,
            description="Authentication token for Milvus in format 'username:password'. If not set, no auth is used.",
        ),
    ]

    def get_token(self) -> str | None:
        """Get the token value for Milvus authentication, or None if not configured."""
        if self.TOKEN is None:
            return None
        return self.TOKEN.get_secret_value()
