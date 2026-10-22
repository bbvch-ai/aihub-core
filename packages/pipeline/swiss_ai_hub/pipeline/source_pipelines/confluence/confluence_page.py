from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_storage import ConfluenceStorage
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

_REST_PATH = "/rest/api/"


class ConfluencePage(BaseModel):
    """One Confluence page as the sync yields it: the fields its file shows, read from a search result.

    It carries the site URL Confluence reports in the result itself, so the link in the file points where users open
    Confluence even when the pipeline reaches it under another host name, and turning it into a file needs nothing but
    the page.
    """

    id: Annotated[str, Field(description="Confluence's page id, stable when the page is renamed or moved.")]
    site: Annotated[str, Field(description="Confluence's base URL as Confluence reports it, …/wiki on Cloud.")]
    title: Annotated[str, Field(description="The page title.")]
    space: Annotated[str, Field(description="Key of the space the page is in; it names the namespace.")]
    ancestors: Annotated[list[str], Field(description="Titles of the pages above this one, the space's root first.")]
    path_segments: Annotated[list[str], Field(description="Folders below the namespace, then the file name.")]
    labels: Annotated[list[str], Field(description="Label names.")] = []
    author: Annotated[str | None, Field(description="Display name of the page's creator.")] = None
    version: Annotated[int, Field(description="Version number; it grows with every edit and rename, not with a move.")]
    created: Annotated[str | None, Field(description="Creation time, ISO-8601 with an offset.")] = None
    updated: Annotated[str, Field(description="Time of the current version, ISO-8601 with an offset.")]
    web_path: Annotated[str, Field(description="The page's address relative to the site.")]
    storage: Annotated[str, Field(description="The body in Confluence's storage format.")] = ""

    @classmethod
    def from_result(cls, page: dict[str, Any]) -> Self:
        """From a search result expanded with body, ancestors, version, history, labels and space."""
        space, path_segments = cls.path_of(page)
        history = page.get("history") or {}
        return cls(
            id=str(page["id"]),
            site=page["_links"]["self"].split(_REST_PATH, 1)[0],
            title=page["title"],
            space=space,
            ancestors=[ancestor["title"] for ancestor in page.get("ancestors") or []],
            path_segments=path_segments,
            labels=cls.labels_of(page),
            author=(history.get("createdBy") or {}).get("displayName"),
            version=page["version"]["number"],
            created=history.get("createdDate"),
            updated=page["version"]["when"],
            web_path=page["_links"]["webui"],
            storage=((page.get("body") or {}).get("storage") or {}).get("value") or "",
        )

    @classmethod
    def path_of(cls, page: dict[str, Any]) -> tuple[str, list[str]]:
        """Where a page's file lives: its space, then the titles of its ancestors, then its own. Both a summary and
        a full result carry these, and the listing and the sync both name files this way: a listed key the sync
        never writes would have the reconcile step delete data."""
        chain = [*(page.get("ancestors") or []), page]
        return page["space"]["key"], [cls._segment(entry["title"], str(entry["id"])) for entry in chain]

    @classmethod
    def object_key_of(cls, page: dict[str, Any]) -> str:
        return StructuredRecordFile.object_key_for(*cls.path_of(page))

    @staticmethod
    def labels_of(page: dict[str, Any]) -> list[str]:
        """The label names, sorted, from a result expanded with ``metadata.labels``: the file shows them, and the sync
        compares them, because adding or removing a label leaves the page's version as it was."""
        return sorted(label["name"] for label in ((page.get("metadata") or {}).get("labels") or {}).get("results", []))

    def to_record_file(self) -> StructuredRecordFile:
        return StructuredRecordFile(
            namespace=self.space,
            path_segments=self.path_segments,
            frontmatter={
                "title": self.title,
                "url": f"{self.site}{self.web_path}",
                "created": self.created,
                "updated": self.updated,
                "page_id": self.id,
                "space": self.space,
                "ancestors": self.ancestors or None,
                "labels": self.labels or None,
                "author": self.author,
                "page_version": self.version,
            },
            body=self._body(),
        )

    def _body(self) -> str:
        content = ConfluenceStorage.to_markdown(self.storage, self.site)
        return f"# {self.title}\n\n{content}" if content else f"# {self.title}"

    @staticmethod
    def _segment(title: str, page_id: str) -> str:
        """A title of dots alone cannot be a folder or file name, and one such page would fail every sync of the
        database; its id stands in."""
        return title if title.strip(" .") else f"page {page_id}"
