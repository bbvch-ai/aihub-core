import re
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator
from swiss_ai_hub.core.form import ChipsInput, Form, InputText, Password, Select

from swiss_ai_hub.pipeline.resources.confluence.confluence_client import ConfluenceClient

# An http(s) URL with no credentials, query or fragment: a "?" or "#" would turn the API path appended to it into a
# query, so the URL could name any path on any host. Empty is allowed, because a hidden option group validates as its
# defaults. Which hosts it may name is checked on every run, against the deployment (PublicHostGuard).
_BASE_URL_PATTERN = r"^(https?://[^\s/@?#]+(/[^\s?#]*)?)?$"
_PAGE_ID = re.compile(r"^[0-9]+$")


class ConfluenceOptions(Form):
    """What a knowledge database synced from Confluence is configured with: where Confluence is, how to sign in, and
    which pages.

    The URL and the deployment are constrained in their types, so the API refuses a bad value when the database is
    saved. Everything that depends on another field (Cloud needs an e-mail) is checked by ``problems`` when a sync
    starts, not by a model validator, whose error would quote the whole input, token included.
    """

    base_url: Annotated[
        Annotated[str, StringConstraints(pattern=_BASE_URL_PATTERN)] | InputText,
        Field(description="Confluence's base URL, e.g. https://acme.atlassian.net/wiki or https://confluence.acme.ch."),
    ] = ""
    deployment: Annotated[
        Literal["cloud", "data_center"] | Select, Field(description="Confluence Cloud or Confluence Data Center.")
    ] = "cloud"
    email: Annotated[
        str | InputText, Field(description="E-mail of the Confluence Cloud account the token belongs to.")
    ] = ""
    api_token: Annotated[
        str | Password, Field(description="API token (Cloud) or personal access token (Data Center).")
    ] = ""
    # Nullable because an untouched chips input submits nothing, which the normaliser turns into None.
    space_keys: Annotated[
        list[str] | ChipsInput | None, Field(description="Keys of the spaces to sync; each becomes a namespace.")
    ] = None
    labels: Annotated[
        list[str] | ChipsInput | None, Field(description="When set, only pages carrying one of these labels.")
    ] = None
    ancestor_page_ids: Annotated[
        list[str] | ChipsInput | None, Field(description="When set, only these pages and the pages below them.")
    ] = None

    @field_validator("space_keys", "labels", "ancestor_page_ids", mode="before")
    @classmethod
    def _blank_chips_mean_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("space_keys", "labels", "ancestor_page_ids", mode="after")
    @classmethod
    def _canonical_chips(cls, value: list[str] | ChipsInput | None) -> list[str] | ChipsInput | None:
        """Stored sorted and de-duplicated, so retyping the same scope in another order does not change the scope
        fingerprint, which would re-read everything. Case is kept: a personal space's key (``~…``) is case-sensitive."""
        if not isinstance(value, list):
            return value
        return sorted({entry.strip() for entry in value if entry.strip()})

    def site_url(self) -> str:
        return self.base_url.rstrip("/")

    def spaces(self) -> list[str]:
        return self.space_keys if isinstance(self.space_keys, list) else []

    def page_labels(self) -> list[str]:
        return self.labels if isinstance(self.labels, list) else []

    def parent_pages(self) -> list[str]:
        return self.ancestor_page_ids if isinstance(self.ancestor_page_ids, list) else []

    def problems(self) -> list[str]:
        """What keeps this configuration from syncing, worded for the person who entered it."""
        found = []
        if not self.base_url:
            found.append("the Confluence URL is missing")
        if not self.api_token:
            found.append("the token is missing")
        if self.deployment == "cloud" and not self.email:
            found.append("Confluence Cloud needs the e-mail of the account the API token belongs to")
        if not self.spaces():
            found.append("no space key is given")
        invalid = [page_id for page_id in self.parent_pages() if not _PAGE_ID.match(page_id)]
        if invalid:
            found.append(f"{', '.join(invalid)} {'is' if len(invalid) == 1 else 'are'} not a Confluence page ID")
        return found

    def scope_cql(self) -> str:
        """CQL selecting every page in scope, for a configuration without ``problems``. Whoever configures the
        database writes these values, so text is quoted and page IDs are digits: neither can change the query."""
        clauses = ["type = page", f"space in ({self._quoted(self.spaces())})"]
        if self.page_labels():
            clauses.append(f"label in ({self._quoted(self.page_labels())})")
        if self.parent_pages():
            page_ids = ", ".join(self.parent_pages())
            clauses.append(f"(ancestor in ({page_ids}) or id in ({page_ids}))")
        return " and ".join(clauses)

    @staticmethod
    def _quoted(values: list[str]) -> str:
        return ", ".join(ConfluenceClient.cql_string(value) for value in values)
