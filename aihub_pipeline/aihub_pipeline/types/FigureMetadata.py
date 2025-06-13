from pydantic import BaseModel, Field


class FigureMetadata(BaseModel):
    """Contains metadata about an extracted figure from a document."""

    figure_path: str = Field(..., description="Blob storage path to the saved figure.")
    figure_url: str = Field(
        ...,
        description="Externally accessible URL of the saved figure for reference in a document.",
    )
