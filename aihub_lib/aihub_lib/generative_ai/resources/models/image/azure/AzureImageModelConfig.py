from typing import Annotated, Literal

from pydantic import Field

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.image.ImageModelConfig import ImageModelConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter


class AzureImageModelParameter(ResourceParameter):
    quality: Annotated[
        Literal["standard", "hd"] | None,
        Field(
            description="The quality of the generated image. "
            "'hd' creates images with finer details. Only supported for DALL-E 3."
        ),
    ] = "hd"

    response_format: Annotated[
        Literal["url", "b64_json"] | None,
        Field(description="The format in which images are returned. URLs are valid for 60 minutes."),
    ] = "url"

    size: Annotated[
        Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] | None,
        Field(description="The size of the image. Supported sizes vary between DALL-E 2 and DALL-E 3."),
    ] = "1024x1792"

    style: Annotated[
        Literal["vivid", "natural"] | None,
        Field(
            description="The style of the image. 'vivid' leans towards hyper-realism, "
            "while 'natural' produces more natural images. Only for DALL-E 3."
        ),
    ] = "natural"


class AzureOpenaiImageModelConfig(ImageModelConfig, AzureOpenaiResourceConfig):
    """
    Resource representing the parameters for the Azure DALL-E image model.
    """

    # Keeping Field() explicitly for default_factory
    default_parameter: Annotated[
        AzureImageModelParameter,
        Field(
            description="Default parameters for the Azure image model.",
        ),
    ] = AzureImageModelParameter()
