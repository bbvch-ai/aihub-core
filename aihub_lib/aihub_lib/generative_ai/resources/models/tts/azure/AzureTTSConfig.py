from typing import Literal, Optional

from pydantic import Field

from aihub_lib.generative_ai.resources.models.AzureResourceConfig import AzureResourceConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter
from aihub_lib.generative_ai.resources.models.tts.TTSConfig import TTSConfig


class AzureTTSParameter(ResourceParameter):
    voice: Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"] = Field(
        "alloy", description="The voice to use when generating audio."
    )
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = Field(
        "mp3", description="The format of the generated audio file. Defaults to 'mp3'."
    )
    speed: Optional[float] = Field(
        1.0, ge=0.25, le=4.0, description="The speed of the generated audio. Defaults to 1.0. Range: 0.25 to 4.0."
    )


class AzureTTSConfig(TTSConfig, AzureResourceConfig):
    default_parameter: AzureTTSParameter = Field(
        ...,
        description="Default parameters for the Azure text-to-speech model.",
        default_factory=lambda: AzureTTSParameter(),
    )
