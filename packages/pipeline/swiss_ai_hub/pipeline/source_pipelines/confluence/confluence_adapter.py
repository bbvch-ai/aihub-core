import logging
from collections.abc import Iterable, Iterator
from typing import Any

import dlt
from dlt.extract import DltResource, DltSource
from swiss_ai_hub.core.form import ChipsInput, InputText, Password, Select
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.resources.confluence.confluence_client import ConfluenceClient
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_options import ConfluenceOptions
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_page import ConfluencePage
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_preflight import ConfluencePreflight
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

logger = logging.getLogger(__name__)

_I18N = "lib.source_pipelines.structured.config.confluence"
_DEPLOYMENT_REF = "confluence_deployment"
# Enough to place a page in the tree and tell whether it changed; bodies are read only for the pages that did.
_SUMMARY_EXPAND = "ancestors,version,space,metadata.labels"
_PAGE_EXPAND = "body.storage,ancestors,version,history,metadata.labels,space"
_SEEN = "seen"


class ConfluenceAdapter(AbstractStructuredSourceAdapter[ConfluenceOptions]):
    """Syncs the pages of the configured Confluence spaces, one markdown file per page at
    ``{space}/{ancestor titles}/{title}.md``.

    Each space becomes a namespace and its page tree becomes folders. What changed is found by comparing every page's
    version, path and labels with the previous sync's, not by a last-modified cursor: renaming or moving a page moves
    its descendants' files too, while their own versions stay the same, and neither a move nor a label change gives a
    page a new version.
    """

    kind = "confluence"
    display_name = LocaleString.from_i18n_path(f"{_I18N}.display_name")

    @classmethod
    def options_form(cls) -> ConfluenceOptions:
        shown = cls.shown_for(cls.kind)
        return ConfluenceOptions(
            base_url=InputText(
                **cls._labels("base_url"),
                placeholder="https://acme.atlassian.net/wiki",
                required=True,
                additional_validation_rules="url",
                condition_if=shown,
            ),
            deployment=Select(
                **cls._labels("deployment"),
                options=[
                    {"label": LocaleString.from_i18n_path(f"{_I18N}.deployment.{value}"), "value": value}
                    for value in ("cloud", "data_center")
                ],
                option_label="label",
                option_value="value",
                ref=_DEPLOYMENT_REF,
                required=True,
                condition_if=shown,
            ),
            email=InputText(
                **cls._labels("email"),
                required=True,
                condition_if=f"{shown} && $get({_DEPLOYMENT_REF}).value === 'cloud'",
            ),
            api_token=Password(
                **cls._labels("api_token"), feedback=False, toggle_mask=True, required=True, condition_if=shown
            ),
            space_keys=ChipsInput(**cls._labels("space_keys"), placeholder="ENG", required=True, condition_if=shown),
            labels=ChipsInput(**cls._labels("labels"), condition_if=shown),
            ancestor_page_ids=ChipsInput(**cls._labels("ancestor_page_ids"), placeholder="123456", condition_if=shown),
        )

    def dlt_source(self, options: ConfluenceOptions) -> DltSource:
        """The pages that are new, edited, renamed, moved or relabelled since the last successful sync, all of them on
        the first.

        Every page's ``version|path|labels`` is kept in the resource state, which is saved only after a sync succeeded.
        A page is recorded only once it was read or did not need to be, so one whose body could not be read this time,
        say because it was deleted between the two queries, is compared again next time instead of being taken as done.
        """
        client = self._checked_client(options)

        @dlt.source(name="confluence")
        def confluence() -> DltResource:
            @dlt.resource(name="pages", primary_key="id")
            def pages() -> Iterator[list[dict[str, Any]]]:
                seen: dict[str, str] = dlt.current.resource_state().setdefault(_SEEN, {})
                current = {
                    page["id"]: self._fingerprint(page)
                    for page in self._current(client.search(options.scope_cql(), _SUMMARY_EXPAND))
                }
                changed = {page_id for page_id, fingerprint in current.items() if seen.get(page_id) != fingerprint}
                read: set[str] = set()
                for batch in self._read(client, sorted(changed)):
                    read.update(page["id"] for page in batch)
                    yield batch
                seen.clear()
                seen.update(
                    {
                        page_id: fingerprint
                        for page_id, fingerprint in current.items()
                        if page_id in read or page_id not in changed
                    }
                )

            return pages

        return confluence()

    def _read(self, client: ConfluenceClient, page_ids: list[str]) -> Iterator[list[dict[str, Any]]]:
        for results in client.pages_by_id(page_ids, _PAGE_EXPAND):
            if batch := [ConfluencePage.from_result(page).model_dump() for page in self._current([results])]:
                yield batch

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile:
        return ConfluencePage.model_validate(record).to_record_file()

    def list_record_paths(self, options: ConfluenceOptions) -> set[str]:
        """Two pages can end up at one path: a title cut at the length a file name may have, or a ``/`` written as
        the ``_`` of another title. Only one of them is kept; the other is named in the log until one is renamed."""
        client = self._checked_client(options)
        owners: dict[str, str] = {}
        for page in self._current(client.search(options.scope_cql(), _SUMMARY_EXPAND)):
            path = ConfluencePage.object_key_of(page)
            if path in owners:
                logger.warning(
                    f"Confluence pages {owners[path]} and {page['id']} share the file {path}; one is left out."
                )
            owners.setdefault(path, page["id"])
        return set(owners)

    @staticmethod
    def _current(pages: Iterable[list[dict[str, Any]]]) -> Iterator[dict[str, Any]]:
        """Archived pages are left out here instead of trusting CQL to do it, so they are removed like deleted ones."""
        return (page for results in pages for page in results if page.get("status") == "current")

    @staticmethod
    def _fingerprint(page: dict[str, Any]) -> str:
        labels = ",".join(ConfluencePage.labels_of(page))
        return f"{page['version']['number']}|{ConfluencePage.object_key_of(page)}|{labels}"

    @staticmethod
    def _checked_client(options: ConfluenceOptions) -> ConfluenceClient:
        """Checked before anything is read, in the sync and again in the listing, which runs as its own step: a
        listing that silently comes back short removes the files of pages that still exist."""
        problems = options.problems()
        if problems:
            raise ValueError(f"The Confluence source cannot sync: {'; '.join(problems)}.")
        client = ConfluenceClient(
            base_url=options.base_url, deployment=options.deployment, email=options.email, token=options.api_token
        )
        ConfluencePreflight.check(client, options)
        return client

    @staticmethod
    def _labels(field: str) -> dict[str, LocaleString]:
        return {
            "label": LocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": LocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
