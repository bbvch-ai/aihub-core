from typing import List, Optional

from pydantic import BaseModel, Field


class FigureMetadata(BaseModel):
    """Contains metadata about extracted figures from a document"""

    figure_paths: Optional[List[str]] = Field(
        default_factory=list, description="Blob storage paths to the saved figures"
    )
    figure_urls: Optional[List[str]] = Field(
        default_factory=list,
        description="Externally accessible URLs of the saved figures for reference in the document",
    )
