from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class TextToSpeechRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: Literal["tts-1", "tts-1-hd"] = Field(
        ..., description="The TTS model to use. Available options: 'tts-1' or 'tts-1-hd'."
    )
    input: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="The text to generate audio for. Maximum length is 4096 characters.",
    )
    voice: Literal["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"] = Field(
        ..., description="The voice to use when generating audio."
    )
    response_format: Optional[Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]] = Field(
        "mp3", description="The format of the generated audio file. Defaults to 'mp3'."
    )
    speed: Optional[float] = Field(
        1.0, ge=0.25, le=4.0, description="The speed of the generated audio. Defaults to 1.0. Range: 0.25 to 4.0."
    )
