from typing import Annotated

from pydantic import Field, field_validator

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class ParsingSettings(EnvironmentSettings):
    """Controls which file types the parsing service accepts without error."""

    model_config = EnvironmentSettings.create_settings_config("PARSING_")

    PASSTHROUGH_EXTENSIONS: Annotated[
        list[str],
        Field(
            description="File extensions that return empty content instead of 400 (e.g. for agent-only processing). "
            'Set via env as JSON array: PARSING_PASSTHROUGH_EXTENSIONS=\'["zip","wav"]\'',
        ),
    ] = []

    @field_validator("PASSTHROUGH_EXTENSIONS", mode="after")
    @classmethod
    def normalize_extensions(cls, v: list[str]) -> list[str]:
        """Strip leading dots, trim whitespace, and lowercase for consistent matching."""
        return [ext.strip().lstrip(".").lower() for ext in v if ext.strip()]
