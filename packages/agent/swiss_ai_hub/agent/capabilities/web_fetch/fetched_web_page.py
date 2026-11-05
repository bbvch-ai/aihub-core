import hashlib
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import IngestedNode

WEB_NAMESPACE = "web"


class FetchedWebPage(BaseModel):
    """A web page read on the user's behalf, convertible to a node so it reaches the answer through the same rendering
    and source listing as retrieved knowledge."""

    url: Annotated[str, Field(description="The URL as the user sent it, which the citation shows.")]
    title: Annotated[str | None, Field(description="The page's title, if it has one.")] = None
    markdown: Annotated[str, Field(description="The page's main content as markdown.")]
    truncated: Annotated[bool, Field(description="Whether the content was cut to the configured page limit.")] = False
    fetched_at: Annotated[datetime, Field(description="When the page was read.")] = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    def to_ingested_node(self) -> IngestedNode:
        """One node per page, its id from the URL alone, so the same page cited on two turns keeps one citation id.

        `source_origin` is what chat clients link a source to; a page without a title is labelled by its URL.
        """
        page_id = hashlib.sha256(self.url.encode("utf-8")).hexdigest()
        fetched_at = self.fetched_at.isoformat()
        return IngestedNode(
            id=page_id,
            document_id=page_id,
            source=self.url,
            source_origin=self.url,
            namespace=WEB_NAMESPACE,
            document_title=self.title or self.url,
            content=self.markdown,
            created_at=fetched_at,
            updated_at=fetched_at,
            inserted_at=fetched_at,
        )
