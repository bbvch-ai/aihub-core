import logging
from collections.abc import Iterator
from typing import Any
from urllib.parse import urlsplit

import dlt
from dlt.extract import DltResource, DltSource
from swiss_ai_hub.core.form import Checkbox, ChipsInput, InputNumber, InputText, Password, Select
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_file import MediaWikiFile
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_page import MediaWikiPage
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_preflight import MediaWikiPreflight
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_scope import MediaWikiScope
from swiss_ai_hub.pipeline.source_pipelines.structured_file_unavailable_error import StructuredFileUnavailableError
from swiss_ai_hub.pipeline.types.structured_file_reference import StructuredFileReference
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

logger = logging.getLogger(__name__)

_I18N = "lib.source_pipelines.structured.config.mediawiki"
_AUTH_METHOD_REF = "mediawiki_auth_method"
_SYNC_FILES_REF = "mediawiki_sync_files"
_SEEN = "seen"
_ALLOW_LIST_VARIABLE = "STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS"
# What a file download answers when the wiki will not serve that file: forbidden, missing, or deleted since listed.
_UNAVAILABLE = {403, 404, 410}


class MediaWikiAdapter(AbstractStructuredSourceAdapter[MediaWikiOptions]):
    """Syncs the pages of the configured MediaWiki namespaces, one markdown file per page at
    ``{namespace}/{title, split into subpages}.md``, and with ``sync_files`` the documents those pages use, each as it
    is at ``{file namespace}/{name}``.

    What changed is found by comparing every page's latest revision and path with the previous sync's, not by a
    last-modified cursor: a page renamed or moved into scope (a new category, a removed exclusion) keeps the revision it
    had. A template edit re-renders the pages using it without giving them a new revision, so they are read again only
    when they are next edited themselves.
    """

    kind = "mediawiki"
    layout_version = 2
    """2: collections named after a namespace's canonical name instead of its local one."""
    _client: MediaWikiClient | None = None
    display_name = LocaleString.from_i18n_path(f"{_I18N}.display_name")

    @classmethod
    def options_form(cls) -> MediaWikiOptions:
        shown = cls.shown_for(cls.kind)
        method = f"$get({_AUTH_METHOD_REF}).value"
        with_password = f"{shown} && ({method} === 'bot_password' || {method} === 'web_form')"
        return MediaWikiOptions(
            base_url=InputText(
                **cls._labels("base_url"),
                placeholder="https://wiki.acme.ch",
                required=True,
                additional_validation_rules="url",
                condition_if=shown,
            ),
            auth_method=Select(
                **cls._labels("auth_method"),
                options=[
                    {"label": LocaleString.from_i18n_path(f"{_I18N}.auth_method.{value}"), "value": value}
                    for value in ("bot_password", "web_form", "oauth", "anonymous")
                ],
                option_label="label",
                option_value="value",
                ref=_AUTH_METHOD_REF,
                required=True,
                condition_if=shown,
            ),
            username=InputText(**cls._labels("username"), required=True, condition_if=with_password),
            password=Password(
                **cls._labels("password"), feedback=False, toggle_mask=True, required=True, condition_if=with_password
            ),
            access_token=Password(
                **cls._labels("access_token"),
                feedback=False,
                toggle_mask=True,
                required=True,
                condition_if=f"{shown} && {method} === 'oauth'",
            ),
            namespaces=ChipsInput(**cls._labels("namespaces"), placeholder="Main", condition_if=shown),
            include_categories=ChipsInput(**cls._labels("include_categories"), condition_if=shown),
            exclude_categories=ChipsInput(**cls._labels("exclude_categories"), condition_if=shown),
            sync_files=Checkbox(**cls._labels("sync_files"), ref=_SYNC_FILES_REF, condition_if=shown),
            max_file_size_mb=InputNumber(
                **cls._labels("max_file_size_mb"),
                min=1,
                max=500,
                use_grouping=False,
                condition_if=f"{shown} && $get({_SYNC_FILES_REF}).value",
            ),
        )

    def dlt_source(self, options: MediaWikiOptions) -> DltSource:
        """The pages that are new, edited, renamed or newly in scope since the last successful sync, all of them on the
        first.

        Every page's ``revision|path`` is kept in the resource state, which is saved only after a sync succeeded. A
        page is recorded only once it was read or did not need to be, so one that could not be read this time, say
        because it was deleted between the listing and the read, is compared again next time instead of being taken as
        done.
        """
        client, scope = self._checked(options)
        self._client = client

        @dlt.source(name="mediawiki")
        def mediawiki() -> list[DltResource]:
            @dlt.resource(name="pages", primary_key="page_id")
            def pages() -> Iterator[list[dict[str, Any]]]:
                seen: dict[str, str] = dlt.current.resource_state().setdefault(_SEEN, {})
                listed = {str(page["pageid"]): page for page in scope.pages(client)}
                current = {page_id: self._fingerprint(scope, page) for page_id, page in listed.items()}
                changed = sorted(
                    page_id for page_id, fingerprint in current.items() if seen.get(page_id) != fingerprint
                )
                read: set[str] = set()
                for batch in self._read(client, scope, [listed[page_id] for page_id in changed]):
                    read.update(str(page["page_id"]) for page in batch)
                    yield batch
                seen.clear()
                seen.update(
                    {
                        page_id: fingerprint
                        for page_id, fingerprint in current.items()
                        if page_id in read or page_id not in changed
                    }
                )

            @dlt.resource(name="files", primary_key="download_url")
            def files() -> Iterator[list[dict[str, Any]]]:
                """The files that are new or changed. Each is recorded by its checksum and key in ``FILES_SEEN``; the
                pipeline removes a file the destination could not read before the state is saved."""
                seen: dict[str, str] = dlt.current.resource_state().setdefault(self.FILES_SEEN, {})
                current = {file.object_key: file for file in scope.files(client, options)}
                changed = [file for key, file in current.items() if seen.get(key) != file.fingerprint]
                seen.clear()
                seen.update({key: file.fingerprint for key, file in current.items()})
                for start in range(0, len(changed), MediaWikiClient.IDS_PER_QUERY):
                    yield [file.model_dump() for file in changed[start : start + MediaWikiClient.IDS_PER_QUERY]]

            return [pages, files] if options.sync_files else [pages]

        return mediawiki()

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile | StructuredFileReference:
        if "sha1" in record:
            return MediaWikiFile.model_validate(record).to_reference()
        return MediaWikiPage.model_validate(record).to_record_file()

    def read_file(self, options: MediaWikiOptions, reference: StructuredFileReference) -> bytes:
        """Downloads with the session the sync signed in with. A file stored on another host than the wiki's, as
        Wikimedia's are, is checked against the address guard first."""
        if urlsplit(reference.download_url).netloc != urlsplit(options.site_url()).netloc:
            SourceHostGuard.require_public(
                reference.download_url, StructuredPipelineSettings().private_host_allow_list(), _ALLOW_LIST_VARIABLE
            )
        try:
            content = self._signed_in(options).download(reference.download_url, options.max_file_bytes())
        except MediaWikiRequestError as refused:
            if refused.status_code in _UNAVAILABLE:
                raise StructuredFileUnavailableError(str(refused)) from refused
            raise
        if content is None:
            raise StructuredFileUnavailableError(f"it is larger than {options.max_file_size_mb} MB")
        return content

    def list_record_paths(self, options: MediaWikiOptions) -> set[str]:
        """Two pages can end up at one path: a title cut at the length a file name may have, or a ``/`` written as the
        ``_`` of another title. Only one of them is kept; the other is named in the log until one is renamed."""
        client, scope = self._checked(options)
        owners: dict[str, int] = {}
        for page in scope.pages(client):
            path = scope.object_key_of(page)
            if path in owners:
                logger.warning(
                    f"Wiki pages {owners[path]} and {page['pageid']} share the file {path}; one is left out."
                )
            owners.setdefault(path, page["pageid"])
        return set(owners) | {file.object_key for file in scope.files(client, options)}

    @staticmethod
    def _read(
        client: MediaWikiClient, scope: MediaWikiScope, pages: list[dict[str, Any]]
    ) -> Iterator[list[dict[str, Any]]]:
        """Renders the pages a batch at a time; a page deleted since it was listed is skipped."""
        for start in range(0, len(pages), MediaWikiClient.IDS_PER_QUERY):
            rendered = [
                (page, parsed)
                for page in pages[start : start + MediaWikiClient.IDS_PER_QUERY]
                if (parsed := client.parse(page["pageid"])) is not None
            ]
            saved = client.revision_times([parsed["revid"] for _, parsed in rendered])
            batch = [
                MediaWikiPage.from_parse(
                    page,
                    parsed,
                    scope.namespace_of(page),
                    created=client.first_revision_time(page["pageid"]),
                    updated=saved.get(parsed["revid"]),
                ).model_dump()
                for page, parsed in rendered
            ]
            if batch:
                yield batch

    @staticmethod
    def _fingerprint(scope: MediaWikiScope, page: dict[str, Any]) -> str:
        return f"{page['lastrevid']}|{scope.object_key_of(page)}"

    def _signed_in(self, options: MediaWikiOptions) -> MediaWikiClient:
        """The client the sync signed in with; an adapter reading files without having synced signs in once."""
        if self._client is None:
            self._client, _ = self._checked(options)
        return self._client

    @staticmethod
    def _checked(options: MediaWikiOptions) -> tuple[MediaWikiClient, MediaWikiScope]:
        """Checked before anything is read, in the sync and again in the listing, which runs as its own step: a
        listing that silently comes back short removes the files of pages that still exist."""
        problems = options.problems()
        if problems:
            raise ValueError(f"The MediaWiki source cannot sync: {'; '.join(problems)}.")
        client = MediaWikiClient(base_url=options.site_url(), access_token=options.oauth_token())
        collections = MediaWikiPreflight.check(client, options)
        return client, MediaWikiScope.read(client, collections, options)

    @staticmethod
    def _labels(field: str) -> dict[str, LocaleString]:
        return {
            "label": LocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": LocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
