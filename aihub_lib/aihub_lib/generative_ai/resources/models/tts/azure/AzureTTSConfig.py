from typing import Literal, Optional

from pydantic import Field
from typing_extensions import Annotated

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter
from aihub_lib.generative_ai.resources.models.tts.TTSConfig import TTSConfig


class AzureTTSParameter(ResourceParameter):
    voice: Annotated[
        Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"],
        Field(description="The voice to use when generating audio."),
    ] = "alloy"

    response_format: Annotated[
        Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]],
        Field(description="The format of the generated audio file. Defaults to 'mp3'."),
    ] = "mp3"

    speed: Annotated[
        Optional[float],
        Field(ge=0.25, le=4.0, description="The speed of the generated audio. Defaults to 1.0. Range: 0.25 to 4.0."),
    ] = 1.0


class AzureOpenaiTTSConfig(TTSConfig, AzureOpenaiResourceConfig):
    """
    Resource representing the parameters for the Azure text-to-speech model.
    """

    # Keeping Field() explicitly for default_factory
    default_parameter: AzureTTSParameter = Field(
        default_factory=lambda: AzureTTSParameter(),
        description="Default parameters for the Azure text-to-speech model.",
    )
