from typing import Annotated

from pydantic import BaseModel, Field


class KnowledgeContentSearchLimits(BaseModel):
    """Bounds on one content search call, so a result always fits a model's context and a tool loop never stalls."""

    max_documents: Annotated[
        int, Field(ge=1, le=100, description="Documents returned per call; page with the offset")
    ] = 20
    max_lines_per_document: Annotated[
        int, Field(ge=1, le=50, description="Matching lines returned per document; all of them are still counted")
    ] = 5
    max_line_chars: Annotated[
        int, Field(ge=40, le=2000, description="Longest line returned; a longer one is clipped around its match")
    ] = 240
    timeout_seconds: Annotated[
        float, Field(gt=0, le=30, description="Time budget of the whole call, database and line extraction together")
    ] = 5.0
