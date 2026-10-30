import re
from typing import Annotated, Any

from swiss_ai_hub.core.infrastructure import StructuredPipelineSettings
from swiss_ai_hub.core.network import SourceHostGuard
from swiss_ai_hub.core.persistence import NamespaceEntity

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_sign_in import MediaWikiSignIn
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_collections import MediaWikiCollections
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions

_ALLOW_LIST_VARIABLE = "STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS"
_REFUSED_SIGN_IN = (401, 403)
_MAIN_NAMESPACE = 0
_MAIN_COLLECTION = "Main"
_FILE_NAMESPACE = 6
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
    it does not know. Two namespaces whose collections would share a name are refused: pages of the same title in both
    would compete for one file, and one of them would be missing from the database.
    """

    @classmethod
    def check(
        cls,
        client: Annotated[MediaWikiClient, "Client built from the configuration being checked"],
        options: Annotated[MediaWikiOptions, "The configuration, already checked for missing values"],
    ) -> MediaWikiCollections:
        """The namespaces to sync and the collections they and the files land in."""
        SourceHostGuard.require_public(
            options.base_url,
            StructuredPipelineSettings().private_host_allow_list(),
            _ALLOW_LIST_VARIABLE,
        )
        MediaWikiSignIn.sign_in(client, options.auth_method, options.username, options.password)
        account = cls._reading_account(client, options)
        site = client.site_info()
        cls._require_supported_version(site, client.site_url)
        collections = cls._collections(site, options)
        categories = [*options.included_categories(), *options.excluded_categories()]
        if categories:
            cls._require_categories(client, categories, account)
        return collections

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

    @classmethod
    def _collections(cls, site: dict[str, Any], options: MediaWikiOptions) -> MediaWikiCollections:
        known = {int(number): entry for number, entry in (site.get("namespaces") or {}).items() if int(number) >= 0}
        pages = {
            number: cls._collection_of(number, known) for number in cls._namespaces(known, options.namespace_names())
        }
        files = cls._collection_of(_FILE_NAMESPACE, known) if options.syncs_files() else None
        cls._require_distinct(pages, files, known)
        return MediaWikiCollections(pages=pages, files=files)

    @staticmethod
    def _collection_of(number: int, known: dict[int, dict[str, Any]]) -> str:
        """A custom namespace a wiki reports without a canonical name keeps its local one."""
        if number == _MAIN_NAMESPACE:
            return _MAIN_COLLECTION
        return known[number].get("canonical") or known[number]["name"]

    @staticmethod
    def _require_distinct(pages: dict[int, str], files: str | None, known: dict[int, dict[str, Any]]) -> None:
        """Collections are compared as the platform stores them, every character other than a letter, digit, ``_``
        or ``-`` written as ``_``. The file namespace's own pages may share the file collection: a page and a file are
        stored under different keys."""
        targets = dict(pages)
        if files is not None and _FILE_NAMESPACE not in targets:
            targets[_FILE_NAMESPACE] = files
        owners: dict[str, int] = {}
        for number, collection in sorted(targets.items()):
            stored = NamespaceEntity.sanitize_namespace_name(collection)
            if stored in owners:
                first = MediaWikiPreflight._label(owners[stored], known)
                raise ValueError(
                    f"The wiki namespaces {first} and {MediaWikiPreflight._label(number, known)} would both be stored "
                    f"in the collection {stored}; sync only one of them, or each into a knowledge database of its own."
                )
            owners[stored] = number

    @staticmethod
    def _label(number: int, known: dict[int, dict[str, Any]]) -> str:
        return f"{known[number].get('name') or _MAIN_COLLECTION} ({number})"

    @staticmethod
    def _namespaces(known: dict[int, dict[str, Any]], wanted: list[str]) -> list[int]:
        """A namespace is named by its number, its local or canonical name, or ``Main``. Special and Media (negative
        numbers) hold no pages and are refused like unknown ones."""
        by_name = {
            name.lower(): number
            for number, entry in known.items()
            for name in (entry.get("name"), entry.get("canonical"))
            if name
        }
        by_name.update(dict.fromkeys(_MAIN_NAMES, _MAIN_NAMESPACE))
        resolved: list[int] = []
        for entry in wanted:
            number = int(entry) if entry.lstrip("-").isdigit() else by_name.get(entry.lower())
            if number not in known:
                raise ValueError(f"The wiki has no namespace {entry}; it has {', '.join(map(str, sorted(known)))}.")
            resolved.append(number)
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
