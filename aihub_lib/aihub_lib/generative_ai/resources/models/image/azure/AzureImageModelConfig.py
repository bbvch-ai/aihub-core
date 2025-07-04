from typing import Literal, Optional

from pydantic import Field
from typing_extensions import Annotated

from aihub_lib.generative_ai.resources.models.AzureOpenaiResourceConfig import AzureOpenaiResourceConfig
from aihub_lib.generative_ai.resources.models.image.ImageModelConfig import ImageModelConfig
from aihub_lib.generative_ai.resources.models.ResourceConfig import ResourceParameter


class AzureImageModelParameter(ResourceParameter):
    quality: Annotated[
        Optional[Literal["standard", "hd"]],
        Field(
            description="The quality of the generated image. 'hd' creates images with finer details. Only supported for DALL-E 3."
        ),
    ] = "hd"

    response_format: Annotated[
        Optional[Literal["url", "b64_json"]],
        Field(description="The format in which images are returned. URLs are valid for 60 minutes."),
    ] = "url"

    size: Annotated[
        Optional[Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]],
        Field(description="The size of the image. Supported sizes vary between DALL-E 2 and DALL-E 3."),
    ] = "1024x1792"

    style: Annotated[
        Optional[Literal["vivid", "natural"]],
        Field(
            description="The style of the image. 'vivid' leans towards hyper-realism, while 'natural' produces more natural images. Only for DALL-E 3."
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
