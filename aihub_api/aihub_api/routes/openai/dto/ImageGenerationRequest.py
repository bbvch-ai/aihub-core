from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class ImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    prompt: Annotated[
        str,
        Field(
            min_length=1,
            max_length=4000,
            description="A text description of the desired image(s). "
            "Max 1000 characters for DALL-E 2, 4000 for DALL-E 3.",
        ),
    ]

    model: Annotated[
        str | None,
        Field(description="The model to use for image generation. Defaults to dall-e-2."),
    ] = "image-generation"

    n: int | None = None
    quality: Literal["standard", "hd"] | None = None
    response_format: Literal["url", "b64_json"] | None = None
    size: Literal["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"] | None = None
    style: Literal["vivid", "natural"] | None = None
