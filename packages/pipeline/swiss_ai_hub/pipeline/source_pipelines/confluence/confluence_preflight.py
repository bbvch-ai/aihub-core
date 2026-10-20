from typing import Annotated, Any

from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings

from swiss_ai_hub.pipeline.resources.confluence.confluence_client import ConfluenceClient
from swiss_ai_hub.pipeline.resources.confluence.confluence_request_error import ConfluenceRequestError
from swiss_ai_hub.pipeline.resources.structured.source_host_guard import SourceHostGuard
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_options import ConfluenceOptions

_REFUSED_SIGN_IN = (401, 403)


class ConfluencePreflight:
    """Checks a configuration against Confluence before a sync reads or a listing removes anything.

    Each mistake it catches would otherwise pass silently: Confluence answers a search in a space the account cannot
    see, or below a parent page that does not exist, with no pages at all, and an empty listing removes that space's
    files. The host check comes first, so no request, and no credential, goes to an address inside the platform.
    Spaces and parent pages are found through CQL search, which both editions answer: Cloud's REST v1 no longer serves
    a space by its key or a page by its ID. Failing here also keeps the message ours, instead of one dlt wraps around
    the first failed request.
    """

    @classmethod
    def check(
        cls,
        client: Annotated[ConfluenceClient, "Client built from the configuration being checked"],
        options: Annotated[ConfluenceOptions, "The configuration, already checked for missing values"],
    ) -> None:
        SourceHostGuard.require_public(options.base_url, StructuredPipelineSettings().private_host_allow_list())
        account = cls._signed_in_account(client, options.base_url)
        name = account.get("displayName") or account.get("publicName") or "this account"
        for space in options.spaces():
            cls._require_visible_space(client, space, name)
        for page_id in options.parent_pages():
            cls._require_parent_in_scope(client, page_id, options.spaces(), name)

    @staticmethod
    def _signed_in_account(client: ConfluenceClient, base_url: str) -> dict[str, Any]:
        """An anonymous answer means the credentials never arrived, and anonymous access reads public pages only: the
        listing would remove every page the account was meant to read."""
        try:
            account = client.current_user()
        except ConfluenceRequestError as refused:
            if refused.status_code not in _REFUSED_SIGN_IN:
                raise
            raise ValueError(
                f"Confluence rejected the credentials for {base_url} ({refused.status_code}). Check the account e-mail "
                "and API token (Confluence Cloud) or the personal access token (Confluence Data Center)."
            ) from refused
        if account.get("type") == "anonymous":
            raise ValueError(
                f"Confluence at {base_url} answered as if no credentials were sent; check that nothing between the "
                "platform and Confluence removes them."
            )
        return account

    @staticmethod
    def _require_visible_space(client: ConfluenceClient, space: str, account: str) -> None:
        if client.find_space(space) is None:
            raise ValueError(f"Confluence space {space} does not exist, or {account} cannot see it.")

    @staticmethod
    def _require_parent_in_scope(client: ConfluenceClient, page_id: str, spaces: list[str], account: str) -> None:
        """A parent page outside the listed spaces narrows the scope to nothing."""
        page = client.find_page(page_id)
        if page is None:
            raise ValueError(f"Confluence page {page_id} does not exist, or {account} cannot see it.")
        space = (page.get("space") or {}).get("key")
        if space not in spaces:
            raise ValueError(
                f"Confluence page {page_id} is in space {space}, which is not one of the database's spaces."
            )
