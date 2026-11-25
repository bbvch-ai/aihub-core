from typing import Annotated, Any, Self

from pydantic import BaseModel, Field


class SearxngResult(BaseModel):
    """One hit from SearXNG's JSON answer, with only the fields an agent grounds an answer in."""

    url: Annotated[str, Field(description="The page the hit links to.")]
    title: Annotated[str, Field(description="The page's title as the engine reported it.")] = ""
    content: Annotated[str, Field(description="The engine's snippet of the page.")] = ""
    engine: Annotated[str, Field(description="The engine that ranked the hit highest.")] = ""

    @classmethod
    def from_searxng(cls, hit: dict[str, Any]) -> Self:
        return cls(
            url=hit["url"],
            title=hit.get("title") or "",
            content=hit.get("content") or "",
            engine=hit.get("engine") or "",
        )
