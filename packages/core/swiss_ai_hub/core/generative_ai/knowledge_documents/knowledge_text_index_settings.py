from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class KnowledgeTextIndexSettings(EnvironmentSettings):
    """Read-only access to the PostgreSQL behind FerretDB, where the content search's trigram indexes live.

    Without a password the index is never used and every content search scans, as it did before the index existed.
    """

    model_config = EnvironmentSettings.create_settings_config("KNOWLEDGE_TEXT_INDEX_")

    HOST: Annotated[str, Field(description="Host of FerretDB's PostgreSQL.")] = "postgres-ferretdb"
    PORT: Annotated[int, Field(description="Port of FerretDB's PostgreSQL.")] = 5432
    DATABASE: Annotated[str, Field(description="Database holding every FerretDB collection's table.")] = "postgres"
    USER: Annotated[str, Field(description="Read-only role that ferretdb-init creates.")] = "aihub_text_search"
    PASSWORD: Annotated[
        SecretStr, Field(description="Password of the read-only role aihub_text_search; empty turns the index off.")
    ] = SecretStr("")

    @property
    def enabled(self) -> bool:
        return bool(self.PASSWORD.get_secret_value())
