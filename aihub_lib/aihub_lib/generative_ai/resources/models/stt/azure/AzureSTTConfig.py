from typing import Literal, Optional, List

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic import Field

from aihub_lib.generative_ai.resources.models.AzureResourceConfig import AzureResourceConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter
from aihub_lib.generative_ai.resources.models.stt.STTConfig import STTConfig


class AzureSTTParameter(ResourceParameter):
    language: Optional[str] = Field(
        None,
        description="The language of the input audio in ISO-639-1 format (e.g., 'en'). Improves accuracy and latency.",
    )
    prompt: Optional[str] = Field(
        None,
        description="An optional text prompt to guide the model's style or continue from a previous audio segment.",
    )
    response_format: Optional[Literal["json", "text", "srt", "verbose_json", "vtt"]] = Field(
        "json", description="The format of the output transcription."
    )
    temperature: Optional[float] = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for randomness, between 0 and 1. Higher values make output more random.",
    )
    timestamp_granularities: Optional[List[Literal["word", "segment"]]] = Field(
        None,
        description="Timestamp granularities to populate in verbose_json format. Supports 'word' and/or 'segment'.",
    )


class AzureSTTConfig(STTConfig, AzureResourceConfig):
    default_parameter: AzureSTTParameter = Field(
        ...,
        description="Default parameters for the Azure speech-to-text model.",
        default_factory=lambda: AzureSTTParameter(),
    )
