from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_html import MediaWikiHtml
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

_MAIN_NAMESPACE = 0


class MediaWikiPage(BaseModel):
    """One wiki page as the sync yields it: the fields its file shows, read from a listing entry and a parse.

    It carries the page's canonical URL as the wiki reports it, so the link in the file points where users open the
    wiki even when the pipeline reaches it under another host name, and relative links in the body resolve against it.
    """

    page_id: Annotated[int, Field(description="MediaWiki's page id, stable when the page is renamed.")]
    title: Annotated[str, Field(description="The full title, with its namespace prefix.")]
    namespace: Annotated[str, Field(description="Collection, after the canonical name of the page's namespace.")]
    path_segments: Annotated[list[str], Field(description="Folders below the namespace, then the file name.")]
    url: Annotated[str, Field(description="The page's canonical URL.")]
    revision: Annotated[int, Field(description="Id of the revision the body was rendered from.")]
    created: Annotated[str | None, Field(description="Time of the first revision, ISO-8601 in UTC.")] = None
    updated: Annotated[str | None, Field(description="Time of the current revision, ISO-8601 in UTC.")] = None
    categories: Annotated[list[str], Field(description="Names of the page's visible categories.")] = []
    html: Annotated[str, Field(description="The current revision rendered as HTML.")] = ""

    @classmethod
    def from_parse(
        cls,
        listed: Annotated[dict[str, Any], "The page's listing entry, with its canonical URL"],
        parsed: Annotated[dict[str, Any], "The parse answer for the page"],
        namespace: Annotated[str, "Knowledge namespace of the page's wiki namespace"],
        created: Annotated[str | None, "Time of the first revision"],
        updated: Annotated[str | None, "Time of the parsed revision"],
    ) -> Self:
        """Hidden categories (maintenance, tracking) are left out: they say how the page is kept, not what it is."""
        _, path_segments = cls.path_of(listed, namespace)
        return cls(
            page_id=listed["pageid"],
            title=listed["title"],
            namespace=namespace,
            path_segments=path_segments,
            url=listed.get("canonicalurl") or listed["fullurl"],
            revision=parsed["revid"],
            created=created,
            updated=updated,
            categories=sorted(
                category["category"].replace("_", " ")
                for category in parsed.get("categories") or []
                if not category.get("hidden")
            ),
            html=parsed.get("text") or "",
        )

    @classmethod
    def path_of(cls, page: dict[str, Any], namespace: str) -> tuple[str, list[str]]:
        """Where a page's file lives: the namespace, then its title without the namespace prefix, split at ``/`` as
        MediaWiki splits subpages. Both the listing and the sync name files this way: a listed key the sync never
        writes would have the reconcile step delete data.

        A title whose split would give an empty or dots-only folder keeps its ``/`` (written as ``_``) in one file
        name, and a title of dots alone, which cannot be a file name, is written as its id.
        """
        title = page["title"] if page["ns"] == _MAIN_NAMESPACE else page["title"].split(":", 1)[1]
        parts = title.split("/")
        if all(part.strip(" .") for part in parts):
            return namespace, parts
        return namespace, [title if title.strip(" ./") else f"page {page['pageid']}"]

    @classmethod
    def object_key_of(cls, page: dict[str, Any], namespace: str) -> str:
        return StructuredRecordFile.object_key_for(*cls.path_of(page, namespace))

    def to_record_file(self) -> StructuredRecordFile:
        return StructuredRecordFile(
            namespace=self.namespace,
            path_segments=self.path_segments,
            frontmatter={
                "title": self.title,
                "url": self.url,
                "created": self.created,
                "updated": self.updated,
                "page_id": self.page_id,
                "revision": self.revision,
                "categories": self.categories or None,
            },
            body=self._body(),
        )

    def _body(self) -> str:
        content = MediaWikiHtml.to_markdown(self.html, self.url)
        return f"# {self.title}\n\n{content}" if content else f"# {self.title}"
