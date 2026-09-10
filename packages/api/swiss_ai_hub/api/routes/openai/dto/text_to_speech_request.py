from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class TextToSpeechRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: Annotated[
        str,
        Field(min_length=1, description="The TTS model to use, e.g. 'speech/<model-name>'."),
    ]

    input: Annotated[
        str,
        Field(
            min_length=1,
            max_length=4096,
            description="The text to generate audio for. Maximum length is 4096 characters.",
        ),
    ]

    voice: Annotated[
        Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"],
        Field(description="The voice to use when generating audio."),
    ]

    response_format: Annotated[
        Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] | None,
        Field(description="The format of the generated audio file. Defaults to 'mp3'."),
    ] = "mp3"

    speed: Annotated[
        float | None,
        Field(ge=0.25, le=4.0, description="The speed of the generated audio. Defaults to 1.0. Range: 0.25 to 4.0."),
    ] = 1.0
