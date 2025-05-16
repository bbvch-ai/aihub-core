from typing import List

from pydantic import BaseModel, Field


class FigureMetadata(BaseModel):
    """Contains metadata about extracted figures from a document"""

    figure_paths: List[str] = Field(default_factory=list, description="Paths to the saved figures")
    figure_urls: List[str] = Field(default_factory=list, description="URLs of the saved figures")
    container_name: str = Field(description="Azure Blob Storage container name")
