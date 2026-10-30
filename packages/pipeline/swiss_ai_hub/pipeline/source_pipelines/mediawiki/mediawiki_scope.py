import logging
from collections import Counter
from collections.abc import Iterator
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, PrivateAttr

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_collections import MediaWikiCollections
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_file import MediaWikiFile
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_page import MediaWikiPage

logger = logging.getLogger(__name__)

_LOCAL_REPOSITORY = "local"
_TEMPLATE_NAMESPACE = 10


class MediaWikiScope(BaseModel):
    """Which pages and files of a wiki a database holds, resolved against the wiki once per step.

    Category membership is read as page ids before the pages are listed, so a page is filtered by what the wiki's
    category index says, including categories a template assigns, which its own listing entry does not show. Files
    follow the pages: only those a page in scope shows or links to are synced, so a file used only on an excluded page
    stays out. A file's own excluded categories apply too; included categories do not, since files are rarely
    categorised and are already in scope through their pages. With subcategories, a category holds the members of the
    categories below it as well.

    The pages are listed once per step, and every part of the step works from that listing: the sync, its files and the
    listing step therefore agree on which page owns a path two titles share.

    An image a template shows on its own page is left out, wherever it is used: that is the logo, icon or flag a
    template puts on every page using it. An image passed to a template as a parameter is not shown on the template's
    page, so it stays in. Images smaller than the configured minimum are left out as the icons placed by hand.
    """

    namespaces: Annotated[dict[int, str], Field(description="Namespace numbers to sync, with their collection names.")]
    included_ids: Annotated[
        set[int] | None, Field(description="Ids of the pages in an included category; None when none is configured.")
    ] = None
    excluded_ids: Annotated[set[int], Field(description="Ids of the pages in an excluded category.")] = set()
    file_namespace: Annotated[
        str | None, Field(description="Knowledge namespace of the files; None when files are not synced.")
    ] = None
    _listed: list[dict[str, Any]] | None = PrivateAttr(default=None)

    @classmethod
    def read(
        cls,
        client: Annotated[MediaWikiClient, "Signed-in client"],
        collections: Annotated[MediaWikiCollections, "Namespaces and collections the preflight resolved"],
        options: Annotated[MediaWikiOptions, "The checked configuration"],
    ) -> Self:
        included = options.included_categories()
        deep = bool(options.include_subcategories)
        return cls(
            namespaces=collections.pages,
            included_ids=cls._members(client, included, deep) if included else None,
            excluded_ids=cls._members(client, options.excluded_categories(), deep),
            file_namespace=collections.files,
        )

    def pages(self, client: Annotated[MediaWikiClient, "Signed-in client"]) -> list[dict[str, Any]]:
        """Every page in scope as the listing returns it: id, title, namespace, latest revision and canonical URL.

        Two titles can end up at one path: a title cut at the length a file name may have, or a ``/`` written as the
        ``_`` of another title. The first one listed keeps the path; the other is named in the log and left out until
        one of them is renamed.
        """
        if self._listed is None:
            owners: dict[str, dict[str, Any]] = {}
            for page in self._in_scope_pages(client):
                path = self.object_key_of(page)
                if path in owners:
                    logger.warning(
                        f"Wiki pages {owners[path]['pageid']} and {page['pageid']} share the file {path}; "
                        f"page {page['pageid']} is left out."
                    )
                    continue
                owners[path] = page
            self._listed = list(owners.values())
        return self._listed

    def files(
        self,
        client: Annotated[MediaWikiClient, "Signed-in client"],
        options: Annotated[MediaWikiOptions, "The checked configuration"],
    ) -> list[MediaWikiFile]:
        """Every file in scope, none when files are not synced. Files of a shared repository (Wikimedia Commons on
        many wikis) are left out, and so are types not synced, files above the size limit and images taken for
        decoration; the run's log says how many of each. Files are looked up for the pages the listing kept."""
        if self.file_namespace is None:
            return []
        skipped: Counter[str] = Counter()
        files = []
        template_images = self._template_images(client) if options.sync_images else set()
        pages = self.pages(client)
        taken = {self.object_key_of(page) for page in pages}
        used = client.files_used_by([page["pageid"] for page in pages])
        for listed in sorted(used, key=lambda file: file["title"]):
            if listed.get("imagerepository") != _LOCAL_REPOSITORY:
                skipped["from a shared repository"] += 1
                continue
            file = MediaWikiFile.from_listing(listed, self.file_namespace)
            reason = self._reason_to_skip(file, template_images, options) or self._reason_to_skip_key(file, taken)
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

    def _in_scope_pages(self, client: MediaWikiClient) -> Iterator[dict[str, Any]]:
        for number in sorted(self.namespaces):
            for batch in client.pages(number):
                yield from (page for page in batch if self._in_scope(page["pageid"]))

    def _in_scope(self, page_id: int) -> bool:
        if page_id in self.excluded_ids:
            return False
        return self.included_ids is None or page_id in self.included_ids

    def _reason_to_skip(self, file: MediaWikiFile, template_images: set[str], options: MediaWikiOptions) -> str | None:
        if file.page_id in self.excluded_ids:
            return "in an excluded category"
        if file.extension not in options.file_types():
            return "of a type that is not synced"
        if file.size > options.max_file_bytes():
            return "larger than the limit"
        if file.extension in options.image_types():
            return self._reason_to_skip_image(file, template_images, options)
        return None

    @staticmethod
    def _reason_to_skip_key(file: MediaWikiFile, taken: set[str]) -> str | None:
        """A file's key is taken by a page of the file namespace (``File:Notes`` is ``File/Notes.md``, as the file
        ``Notes.md`` is) or by a file whose extension differs only in case (``Logo.PNG``, ``Logo.png``). The page, or
        the file first by name, keeps it."""
        if file.object_key in taken:
            logger.warning(
                f"Wiki file {file.name} would be stored at {file.object_key}, which is taken; it is left out."
            )
            return "stored at a path that is taken"
        taken.add(file.object_key)
        return None

    @staticmethod
    def _reason_to_skip_image(file: MediaWikiFile, template_images: set[str], options: MediaWikiOptions) -> str | None:
        if file.name in template_images:
            return "shown by a template"
        if min(file.width, file.height) < options.min_image_pixels:
            return "smaller than the minimum image size"
        return None

    @staticmethod
    def _template_images(client: MediaWikiClient) -> set[str]:
        """Names, without the namespace prefix, of the files the template pages show themselves."""
        template_ids = [page["pageid"] for batch in client.pages(_TEMPLATE_NAMESPACE) for page in batch]
        return {file["title"].split(":", 1)[1] for file in client.files_used_by(template_ids)}

    @staticmethod
    def _members(client: MediaWikiClient, categories: list[str], with_subcategories: bool) -> set[int]:
        return {
            page_id
            for category in categories
            for page_id in client.category_member_ids(category, with_subcategories=with_subcategories)
        }
