from typing import Literal, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI
from pydantic import Field

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.image.ImageModelConfig import ImageModelConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter


class AzureImageModelParameter(ResourceParameter):
    quality: Optional[Literal["standard", "hd"]] = Field(
        "hd",
        description="The quality of the generated image. 'hd' creates images with finer details. Only supported for DALL-E 3.",
    )
    response_format: Optional[Literal["url", "b64_json"]] = Field(
        "url", description="The format in which images are returned. URLs are valid for 60 minutes."
    )
    size: Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]] = Field(
        "1024x1792", description="The size of the image. Supported sizes vary between DALL-E 2 and DALL-E 3."
    )
    style: Optional[Literal["vivid", "natural"]] = Field(
        "natural",
        description="The style of the image. 'vivid' leans towards hyper-realism, while 'natural' produces more natural images. Only for DALL-E 3.",
    )


class AzureOpenaiImageModelConfig(ImageModelConfig, AzureOpenaiResourceConfig):
    """
    Resource representing the parameters for the Azure Dall-E image model.
    """

    default_parameter: AzureImageModelParameter = Field(
        ...,
        description="Default parameters for the Azure image model.",
        default_factory=lambda: AzureImageModelParameter(),
    )

    def get_openai_client(self) -> AsyncAzureOpenAI:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )

        return AsyncAzureOpenAI(
            azure_endpoint=self.base_url,
            azure_deployment=self.name,
            azure_ad_token_provider=token_provider,
            api_version=self.api_version,
        )
