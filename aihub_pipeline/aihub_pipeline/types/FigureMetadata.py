from typing import Annotated

from pydantic import BaseModel, Field


class FigureMetadata(BaseModel):
    """Contains metadata about an extracted figure from a document."""

    figure_path: Annotated[str, Field(description="Blob storage path to the saved figure.")]
