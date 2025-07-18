from typing import Annotated

from aihub_lib.generative_ai.resources.models.OpenaiResourceSettings import OpenaiResourceSettings
from pydantic import Field


class DevelopmentOpenaiResourceSettings(OpenaiResourceSettings):
    AZURE_OPENAI_API_KEY_SWEDEN_WHISPER: Annotated[
        str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")
    ] = None
