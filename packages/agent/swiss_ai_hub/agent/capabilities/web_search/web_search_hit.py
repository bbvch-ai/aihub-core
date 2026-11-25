import hashlib
from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.agent import WebSearchResult
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.infrastructure import SearxngResult

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import WEB_NAMESPACE


class WebSearchHit(BaseModel):
    """A hit whose page was not read whole, convertible to a node so its snippet is cited like a page read.

    The node's id comes from the URL alone, as a fetched page's does, so the same site has one citation id whether
    it was read or only found.
    """

    url: Annotated[str, Field(description="The page the hit links to.")]
    title: Annotated[str, Field(description="The page's title as the search engine reported it.")] = ""
    snippet: Annotated[str, Field(description="The search engine's excerpt of the page.")] = ""
    engine: Annotated[str, Field(description="The search engine that ranked the hit highest.")] = ""
    found_at: Annotated[datetime, Field(description="When the search returned the hit.")] = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    @classmethod
    def from_searxng(cls, result: SearxngResult) -> Self:
        return cls(url=result.url, title=result.title, snippet=result.content, engine=result.engine)

    def to_result(self, read: bool) -> WebSearchResult:
        return WebSearchResult(url=self.url, title=self.title, snippet=self.snippet, engine=self.engine, read=read)

    def to_ingested_node(self, snippet_marker: str) -> IngestedNode:
        """`snippet_marker` says the page itself was not read, so the answer does not present a snippet as the page."""
        hit_id = hashlib.sha256(self.url.encode("utf-8")).hexdigest()
        found_at = self.found_at.isoformat()
        return IngestedNode(
            id=hit_id,
            document_id=hit_id,
            source=self.url,
            source_origin=self.url,
            namespace=WEB_NAMESPACE,
            document_title=self.title or self.url,
            content=f"{self.snippet}\n\n{snippet_marker}".strip(),
            created_at=found_at,
            updated_at=found_at,
            inserted_at=found_at,
        )
