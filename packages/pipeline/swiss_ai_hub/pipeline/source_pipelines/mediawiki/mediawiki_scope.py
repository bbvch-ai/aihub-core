from collections.abc import Iterator
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_page import MediaWikiPage


class MediaWikiScope(BaseModel):
    """Which pages of a wiki a database holds, resolved against the wiki once per step.

    Category membership is read as page ids before the pages are listed, so a page is filtered by what the wiki's
    category index says, including categories a template assigns, which its own listing entry does not show.
    """

    namespaces: Annotated[dict[int, str], Field(description="Namespace numbers to sync, with their knowledge names.")]
    included_ids: Annotated[
        set[int] | None, Field(description="Ids of the pages in an included category; None when none is configured.")
    ] = None
    excluded_ids: Annotated[set[int], Field(description="Ids of the pages in an excluded category.")] = set()

    @classmethod
    def read(
        cls,
        client: Annotated[MediaWikiClient, "Signed-in client"],
        namespaces: Annotated[dict[int, str], "Namespaces the preflight resolved"],
        options: Annotated[MediaWikiOptions, "The checked configuration"],
    ) -> Self:
        included = options.included_categories()
        return cls(
            namespaces=namespaces,
            included_ids=cls._members(client, included) if included else None,
            excluded_ids=cls._members(client, options.excluded_categories()),
        )

    def pages(self, client: Annotated[MediaWikiClient, "Signed-in client"]) -> Iterator[dict[str, Any]]:
        """Every page in scope as the listing returns it: id, title, namespace, latest revision and canonical URL."""
        for number in sorted(self.namespaces):
            for batch in client.pages(number):
                yield from (page for page in batch if self._in_scope(page["pageid"]))

    def namespace_of(self, page: dict[str, Any]) -> str:
        return self.namespaces[page["ns"]]

    def object_key_of(self, page: dict[str, Any]) -> str:
        return MediaWikiPage.object_key_of(page, self.namespace_of(page))

    def _in_scope(self, page_id: int) -> bool:
        if page_id in self.excluded_ids:
            return False
        return self.included_ids is None or page_id in self.included_ids

    @staticmethod
    def _members(client: MediaWikiClient, categories: list[str]) -> set[int]:
        return {page_id for category in categories for page_id in client.category_member_ids(category)}
