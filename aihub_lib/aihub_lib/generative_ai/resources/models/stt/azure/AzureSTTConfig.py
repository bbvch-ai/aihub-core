from typing import List, Literal, Optional

from pydantic import Field
from typing_extensions import Annotated

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter
from aihub_lib.generative_ai.resources.models.stt.STTConfig import STTConfig


class AzureSTTParameter(ResourceParameter):
    language: Annotated[
        Optional[str],
        Field(
            description="The language of the input audio in ISO-639-1 format (e.g., 'en'). Improves accuracy and latency."
        ),
    ] = None

    prompt: Annotated[
        Optional[str],
        Field(
            description="An optional text prompt to guide the model's style or continue from a previous audio segment."
        ),
    ] = None

    response_format: Annotated[
        Optional[Literal["json", "text", "srt", "verbose_json", "vtt"]],
        Field(description="The format of the output transcription."),
    ] = "json"

    temperature: Annotated[
        Optional[float],
        Field(
            ge=0.0,
            le=1.0,
            description="Sampling temperature for randomness, between 0 and 1. Higher values make output more random.",
        ),
    ] = 0.0

    timestamp_granularities: Annotated[
        Optional[List[Literal["word", "segment"]]],
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
