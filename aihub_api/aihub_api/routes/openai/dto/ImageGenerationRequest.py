from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal


class ImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="A text description of the desired image(s). Max 1000 characters for DALL-E 2, 4000 for DALL-E 3.",
    )
    model: Optional[Literal["dall-e-2", "dall-e-3"]] = Field(
        "dall-e-2", description="The model to use for image generation. Defaults to dall-e-2."
    )
