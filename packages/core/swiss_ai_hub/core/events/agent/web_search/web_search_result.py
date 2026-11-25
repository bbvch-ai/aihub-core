from typing import Annotated

from pydantic import BaseModel, Field


class WebSearchResult(BaseModel):
    """One hit a web search returned, as a chat client lists it under "searched N sites"."""

    url: Annotated[str, Field(description="The page the hit links to.")]
    title: Annotated[str, Field(description="The page's title as the search engine reported it.")] = ""
    snippet: Annotated[str, Field(description="The search engine's excerpt of the page.")] = ""
    engine: Annotated[str, Field(description="The search engine that ranked the hit highest.")] = ""
    read: Annotated[
        bool, Field(description="Whether the whole page was read, rather than only its snippet handed to the model.")
    ] = False
