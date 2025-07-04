from typing import Optional, Annotated

from pydantic import Field

from aihub_lib.generative_ai.resources.models.OpenaiResourceSettings import OpenaiResourceSettings


class DevelopmentOpenaiResourceSettings(OpenaiResourceSettings):
    AZURE_OPENAI_API_KEY_SWEDEN_WHISPER: Annotated[
        Optional[str], Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")
    ] = None
