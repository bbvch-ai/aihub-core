import re
from typing import Annotated, Any

from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_sign_in import MediaWikiSignIn
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions

_ALLOW_LIST_VARIABLE = "STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS"
_REFUSED_SIGN_IN = (401, 403)
_MAIN_NAMESPACE = 0
_MAIN_NAMES = {"main", "(main)"}
_GENERATOR = re.compile(r"^MediaWiki (\d+)\.(\d+)")
# Bot passwords, the AuthManager login form and the login token from meta=tokens all arrived in MediaWiki 1.27; every
# other call the client makes is older.
_OLDEST_SUPPORTED = (1, 27)


class MediaWikiPreflight:
    """Signs in and checks a configuration against the wiki before a sync reads or a listing removes anything.

    Each mistake it catches would otherwise pass silently. A session that failed to sign in reads public pages only, and
    an empty listing removes the files of every page it no longer sees. An excluded category that does not exist
    excludes nothing, so the pages it was meant to keep out of the database would be synced. The host check comes
    first, so no request, and no credential, goes to an address inside the platform. The wiki's version is checked as
    well, so a wiki too old for the calls the client makes fails with its version named instead of with whichever call
    it does not know.
    """

    @classmethod
    def check(
        cls,
        client: Annotated[MediaWikiClient, "Client built from the configuration being checked"],
        options: Annotated[MediaWikiOptions, "The configuration, already checked for missing values"],
    ) -> dict[int, str]:
        """The namespaces to sync, by number, each with the name its knowledge namespace takes."""
        SourceHostGuard.require_public(
            options.base_url,
            StructuredPipelineSettings().private_host_allow_list(),
            _ALLOW_LIST_VARIABLE,
        )
        MediaWikiSignIn.sign_in(client, options.auth_method, options.username, options.password)
        account = cls._reading_account(client, options)
        site = client.site_info()
        cls._require_supported_version(site, client.site_url)
        namespaces = cls._namespaces(site, options.namespace_names())
        categories = [*options.included_categories(), *options.excluded_categories()]
        if categories:
            cls._require_categories(client, categories, account)
        return namespaces

    @classmethod
    def _reading_account(cls, client: MediaWikiClient, options: MediaWikiOptions) -> str:
        user = cls._user_info(client, options)
        if options.auth_method == "anonymous":
            return "an anonymous reader"
        if user.get("anon"):
            credential = "the OAuth access token" if options.auth_method == "oauth" else options.username
            raise ValueError(
                f"MediaWiki at {client.site_url} still reads anonymously after signing in with {credential}; check the "
                "sign-in method and that nothing between the platform and the wiki drops its cookies or headers."
            )
        return str(user.get("name") or options.username)

    @staticmethod
    def _user_info(client: MediaWikiClient, options: MediaWikiOptions) -> dict[str, Any]:
        """A refused OAuth token answers the first request with 401 or 403, and the message says what to check."""
        try:
            return client.user_info()
        except MediaWikiRequestError as refused:
            if options.auth_method != "oauth" or refused.status_code not in _REFUSED_SIGN_IN:
                raise
            raise ValueError(
                f"MediaWiki at {client.site_url} refused the OAuth access token ({refused.status_code}). Check that it "
                "is the access token of an owner-only OAuth 2 consumer, and that the consumer is not disabled. "
                f"The wiki said: {refused}"
            ) from refused

    @staticmethod
    def _require_supported_version(site: dict[str, Any], site_url: str) -> None:
        """The version is read from ``generator`` (``MediaWiki 1.43.11``, ``MediaWiki 1.48.0-wmf.1``); a wiki that
        reports something else is refused rather than assumed new enough."""
        generator = str((site.get("general") or {}).get("generator") or "")
        version = _GENERATOR.match(generator)
        if version is None:
            raise ValueError(
                f"The wiki at {site_url} reports {generator or 'no version'}, which is not a MediaWiki version."
            )
        if (int(version.group(1)), int(version.group(2))) < _OLDEST_SUPPORTED:
            oldest = ".".join(map(str, _OLDEST_SUPPORTED))
            raise ValueError(f"The wiki at {site_url} runs {generator}; the MediaWiki source needs {oldest} or newer.")

    @staticmethod
    def _namespaces(site: dict[str, Any], wanted: list[str]) -> dict[int, str]:
        """A namespace is named by its number, its local or canonical name, or ``Main``. Special and Media (negative
        numbers) hold no pages and are refused like unknown ones."""
        known = {int(number): entry for number, entry in (site.get("namespaces") or {}).items() if int(number) >= 0}
        by_name = {
            name.lower(): number
            for number, entry in known.items()
            for name in (entry.get("name"), entry.get("canonical"))
            if name
        }
        by_name.update(dict.fromkeys(_MAIN_NAMES, _MAIN_NAMESPACE))
        resolved: dict[int, str] = {}
        for entry in wanted:
            number = int(entry) if entry.lstrip("-").isdigit() else by_name.get(entry.lower())
            if number not in known:
                raise ValueError(f"The wiki has no namespace {entry}; it has {', '.join(map(str, sorted(known)))}.")
            resolved[number] = "Main" if number == _MAIN_NAMESPACE else known[number]["name"]
        return resolved

    @staticmethod
    def _require_categories(client: MediaWikiClient, names: list[str], account: str) -> None:
        """A category counts as existing when it has a page of its own or any member: a category is often used before
        anyone writes its page. An excluded category whose last member leaves it therefore stops existing unless it has
        a page, and the sync fails rather than guess whether the name is a typo."""
        for start in range(0, len(names), MediaWikiClient.IDS_PER_QUERY):
            for category in client.categories(names[start : start + MediaWikiClient.IDS_PER_QUERY]):
                exists = not category.get("missing") or (category.get("categoryinfo") or {}).get("size")
                if category.get("invalid") or not exists:
                    raise ValueError(
                        f"{category['title']} does not exist on the wiki, or {account} cannot see it. A category "
                        "without members exists only once it has a page of its own."
                    )
