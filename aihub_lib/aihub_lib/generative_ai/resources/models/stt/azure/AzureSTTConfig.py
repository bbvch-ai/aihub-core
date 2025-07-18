from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter
from aihub_lib.generative_ai.resources.models.stt.STTConfig import STTConfig


class AzureSTTParameter(ResourceParameter):
    language: Annotated[
        str | None,
        Field(
            description="The language of the input audio in ISO-639-1 format "
            "(e.g., 'en'). Improves accuracy and latency."
        ),
    ] = None

    prompt: Annotated[
        str | None,
        Field(
            description="An optional text prompt to guide the model's style or continue from a previous audio segment."
        ),
    ] = None

    response_format: Annotated[
        Literal["json", "text", "srt", "verbose_json", "vtt"] | None,
        Field(description="The format of the output transcription."),
    ] = "json"

    temperature: Annotated[
        float | None,
        Field(
            ge=0.0,
            le=1.0,
            description="Sampling temperature for randomness, between 0 and 1. Higher values make output more random.",
        ),
    ] = 0.0

    timestamp_granularities: Annotated[
        list[Literal["word", "segment"]] | None,
        Field(
            description="Timestamp granularities to populate in verbose_json format. Supports 'word' and/or 'segment'."
        ),
    ] = None


class AzureOpenaiSTTConfig(STTConfig, AzureOpenaiResourceConfig):
    """
    Resource representing the parameters for the Azure speech-to-text model.
    """

    default_parameter: Annotated[
        AzureSTTParameter,
        Field(
            description="Default parameters for the Azure speech-to-text model.",
        ),
    ] = AzureSTTParameter()
