from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator
from swiss_ai_hub.core.form import Checkbox, ChipsInput, Form, InputNumber, InputText, Password, Select

# An http(s) URL with no credentials, query or fragment: a "?" or "#" would turn the API path appended to it into a
# query, so the URL could name any path on any host. Empty is allowed, because a hidden option group validates as its
# defaults. Which hosts it may name is checked on every run, against the deployment (SourceHostGuard).
_BASE_URL_PATTERN = r"^(https?://[^\s/@?#]+(/[^\s?#]*)?)?$"
_CATEGORY_PREFIX = "category:"
_MEGABYTE = 1_000_000
# What the ingestion pipeline parses: MinerU (pdf and images), MarkItDown (Office), and plain text. The old binary
# Office formats (doc, ppt, pps) are not offered; neither are archives, videos or SVG, which nothing parses. tif is not
# an image type here: MinerU knows the extension tiff only.
_DOCUMENT_TYPES = frozenset({"pdf", "docx", "pptx", "xlsx", "xls", "txt", "md", "csv", "rtf"})
_IMAGE_TYPES = frozenset({"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff", "jp2"})
_SIGNED_IN_WITH_PASSWORD = {"bot_password", "web_form"}
# One printable line: a line break would let the value add headers of its own to every request.
_USER_AGENT_PATTERN = r"^[^\x00-\x1f\x7f]*$"


class MediaWikiOptions(Form):
    """What a knowledge database synced from a MediaWiki is configured with: where the wiki is, how to sign in, and
    which pages.

    The URL and the sign-in method are constrained in their types, so the API refuses a bad value when the database is
    saved. Everything that depends on another field (a sign-in needs a user name) is checked by ``problems`` when a
    sync starts, not by a model validator, whose error would quote the whole input, password included. Namespaces are
    resolved against the wiki itself, by ``MediaWikiPreflight``, because their names differ from wiki to wiki.
    """

    base_url: Annotated[
        Annotated[str, StringConstraints(pattern=_BASE_URL_PATTERN)] | InputText,
        Field(description="The folder holding the wiki's api.php, e.g. https://wiki.acme.ch or https://acme.ch/w."),
    ] = ""
    auth_method: Annotated[
        Literal["anonymous", "bot_password", "web_form", "oauth"] | Select,
        Field(
            description="How the pipeline signs in: not at all, with a bot password, through the login page, or with "
            "an OAuth access token."
        ),
    ] = "bot_password"
    username: Annotated[str | InputText, Field(description="Account name; User@BotName for a bot password.")] = ""
    password: Annotated[str | Password, Field(description="Bot password or account password.")] = ""
    access_token: Annotated[
        str | Password, Field(description="Access token of an owner-only OAuth 2 consumer (Extension:OAuth).")
    ] = ""
    # Nullable because an untouched chips input submits nothing, which the normaliser turns into None.
    namespaces: Annotated[
        list[str] | ChipsInput | None,
        Field(description="Names or numbers of the namespaces to sync; the main namespace when none is given."),
    ] = None
    include_categories: Annotated[
        list[str] | ChipsInput | None, Field(description="When set, only pages in one of these categories.")
    ] = None
    exclude_categories: Annotated[
        list[str] | ChipsInput | None, Field(description="Pages in one of these categories are never synced.")
    ] = None
    include_subcategories: Annotated[
        bool | Checkbox,
        Field(description="A category also holds the pages of the categories below it, for included and excluded."),
    ] = False
    sync_documents: Annotated[
        bool | Checkbox, Field(description="Also sync the documents the synced pages show or link to.")
    ] = False
    sync_images: Annotated[
        bool | Checkbox, Field(description="Also sync the images the synced pages show or link to.")
    ] = False
    max_file_size_mb: Annotated[
        Annotated[int, Field(ge=1, le=500)] | InputNumber,
        Field(description="Larger files are skipped; one file at a time is held in memory while it is written."),
    ] = 50
    min_image_pixels: Annotated[
        Annotated[int, Field(ge=0, le=2000)] | InputNumber,
        Field(description="Images narrower or lower than this are skipped as icons; 0 keeps every image."),
    ] = 100
    user_agent: Annotated[
        Annotated[str, StringConstraints(pattern=_USER_AGENT_PATTERN, max_length=200)] | InputText,
        Field(
            description="Sent as User-Agent with every request, e.g. a name and a contact address, as Wikimedia's "
            "wikis ask for; empty keeps the default."
        ),
    ] = ""

    @field_validator("namespaces", "include_categories", "exclude_categories", mode="before")
    @classmethod
    def _blank_chips_mean_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("namespaces", mode="after")
    @classmethod
    def _canonical_namespaces(cls, value: list[str] | ChipsInput | None) -> list[str] | ChipsInput | None:
        """Stored sorted and de-duplicated, so retyping the same scope in another order does not change the scope
        fingerprint, which would re-read everything."""
        if not isinstance(value, list):
            return value
        return sorted({entry.strip() for entry in value if entry.strip()})

    @field_validator("include_categories", "exclude_categories", mode="after")
    @classmethod
    def _canonical_categories(cls, value: list[str] | ChipsInput | None) -> list[str] | ChipsInput | None:
        """A category is stored without its ``Category:`` prefix and with spaces rather than underscores, the two ways
        one category is commonly written twice. Case is kept: a wiki can be configured with case-sensitive titles."""
        if not isinstance(value, list):
            return value
        return sorted({name for entry in value if (name := cls._category_name(entry))})

    @staticmethod
    def _category_name(entry: str) -> str:
        name = entry.strip()
        if name.lower().startswith(_CATEGORY_PREFIX):
            name = name[len(_CATEGORY_PREFIX) :]
        return " ".join(name.replace("_", " ").split())

    def site_url(self) -> str:
        return self.base_url.rstrip("/")

    def namespace_names(self) -> list[str]:
        return self.namespaces if isinstance(self.namespaces, list) and self.namespaces else ["0"]

    def included_categories(self) -> list[str]:
        return self.include_categories if isinstance(self.include_categories, list) else []

    def excluded_categories(self) -> list[str]:
        return self.exclude_categories if isinstance(self.exclude_categories, list) else []

    def problems(self) -> list[str]:
        """What keeps this configuration from syncing, worded for the person who entered it."""
        found = []
        if not self.base_url:
            found.append("the wiki URL is missing")
        if self.auth_method in _SIGNED_IN_WITH_PASSWORD and not self.username:
            found.append("the user name is missing")
        if self.auth_method in _SIGNED_IN_WITH_PASSWORD and not self.password:
            found.append("the password is missing")
        if self.auth_method == "oauth" and not self.access_token:
            found.append("the OAuth access token is missing")
        return found

    def max_file_bytes(self) -> int:
        return self.max_file_size_mb * _MEGABYTE

    def syncs_files(self) -> bool:
        return bool(self.sync_documents or self.sync_images)

    def file_types(self) -> frozenset[str]:
        """The extensions synced, after the switches for documents and images."""
        return (_DOCUMENT_TYPES if self.sync_documents else frozenset()) | (
            _IMAGE_TYPES if self.sync_images else frozenset()
        )

    @staticmethod
    def image_types() -> frozenset[str]:
        return _IMAGE_TYPES

    def oauth_token(self) -> str | None:
        """The token the client sends with every request; None unless the wiki is read through OAuth, so a token left
        over from an earlier setting never travels with a password sign-in."""
        return self.access_token if self.auth_method == "oauth" and self.access_token else None
