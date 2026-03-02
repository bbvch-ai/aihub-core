from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class ParsingSettings(EnvironmentSettings):
    """Controls which file types the parsing service accepts without error."""

    model_config = EnvironmentSettings.create_settings_config("PARSING_")

    PASSTHROUGH_EXTENSIONS: Annotated[
        list[str],
        Field(description="File extensions that return empty content instead of 400 (e.g. for agent-only processing)"),
    ] = []
