import logging
from collections import Counter
from collections.abc import Iterator
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_collections import MediaWikiCollections
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_file import MediaWikiFile
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_page import MediaWikiPage

logger = logging.getLogger(__name__)

_LOCAL_REPOSITORY = "local"


class MediaWikiScope(BaseModel):
    """Which pages and files of a wiki a database holds, resolved against the wiki once per step.

    Category membership is read as page ids before the pages are listed, so a page is filtered by what the wiki's
    category index says, including categories a template assigns, which its own listing entry does not show. Files
    follow the pages: only those a page in scope shows or links to are synced, so a file used only on an excluded page
    stays out. A file's own excluded categories apply too; included categories do not, since files are rarely
    categorised and are already in scope through their pages.
    """

    namespaces: Annotated[dict[int, str], Field(description="Namespace numbers to sync, with their collection names.")]
    included_ids: Annotated[
        set[int] | None, Field(description="Ids of the pages in an included category; None when none is configured.")
    ] = None
    excluded_ids: Annotated[set[int], Field(description="Ids of the pages in an excluded category.")] = set()
    file_namespace: Annotated[
        str | None, Field(description="Knowledge namespace of the files; None when files are not synced.")
    ] = None

    @classmethod
    def read(
        cls,
        client: Annotated[MediaWikiClient, "Signed-in client"],
        collections: Annotated[MediaWikiCollections, "Namespaces and collections the preflight resolved"],
        options: Annotated[MediaWikiOptions, "The checked configuration"],
    ) -> Self:
        included = options.included_categories()
        return cls(
            namespaces=collections.pages,
            included_ids=cls._members(client, included) if included else None,
            excluded_ids=cls._members(client, options.excluded_categories()),
            file_namespace=collections.files,
        )

    def pages(self, client: Annotated[MediaWikiClient, "Signed-in client"]) -> Iterator[dict[str, Any]]:
        """Every page in scope as the listing returns it: id, title, namespace, latest revision and canonical URL."""
        for number in sorted(self.namespaces):
            for batch in client.pages(number):
                yield from (page for page in batch if self._in_scope(page["pageid"]))

    def files(
        self,
        client: Annotated[MediaWikiClient, "Signed-in client"],
        options: Annotated[MediaWikiOptions, "The checked configuration"],
    ) -> list[MediaWikiFile]:
        """Every file in scope, none when files are not synced. Files of a shared repository (Wikimedia Commons on
        many wikis) are left out, and so are types the ingestion pipeline cannot parse and files above the size limit;
        the run's log says how many of each."""
        if self.file_namespace is None:
            return []
        skipped: Counter[str] = Counter()
        files = []
        for listed in client.files_used_by([page["pageid"] for page in self.pages(client)]):
            if listed.get("imagerepository") != _LOCAL_REPOSITORY:
                skipped["from a shared repository"] += 1
                continue
            file = MediaWikiFile.from_listing(listed, self.file_namespace)
            reason = self._reason_to_skip(file, options)
            if reason:
                skipped[reason] += 1
            else:
                files.append(file)
        if skipped:
            logger.info(
                f"Wiki files left out: {', '.join(f'{count} {why}' for why, count in sorted(skipped.items()))}."
            )
        return files

    def namespace_of(self, page: dict[str, Any]) -> str:
        return self.namespaces[page["ns"]]

    def object_key_of(self, page: dict[str, Any]) -> str:
        return MediaWikiPage.object_key_of(page, self.namespace_of(page))

    def _in_scope(self, page_id: int) -> bool:
        if page_id in self.excluded_ids:
            return False
        return self.included_ids is None or page_id in self.included_ids

    def _reason_to_skip(self, file: MediaWikiFile, options: MediaWikiOptions) -> str | None:
        if file.page_id in self.excluded_ids:
            return "in an excluded category"
        if file.extension not in options.document_types():
            return "of a type that is not synced"
        if file.size > options.max_file_bytes():
            return "larger than the limit"
        return None

    @staticmethod
    def _members(client: MediaWikiClient, categories: list[str]) -> set[int]:
        return {page_id for category in categories for page_id in client.category_member_ids(category)}
