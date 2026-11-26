import re
from typing import Annotated, Literal

from pydantic import Field, StringConstraints, field_validator
from swiss_ai_hub.core.form import ChipsInput, Form, InputText, Password, Select, Textarea

# An http(s) URL with no credentials, query or fragment: a "?" or "#" would turn the API path appended to it into a
# query, so the URL could name any path on any host. Empty is allowed, because a hidden option group validates as its
# defaults. Which hosts it may name is checked on every run, against the deployment (PublicHostGuard).
_BASE_URL_PATTERN = r"^(https?://[^\s/@?#]+(/[^\s?#]*)?)?$"
_PROJECT_KEY = re.compile(r"^[A-Z][A-Z0-9_]*$")
_ORDER_BY = re.compile(r"\border\s+by\b", re.IGNORECASE)


class JiraOptions(Form):
    """What a knowledge database synced from Jira is configured with: where Jira is, how to sign in, which projects.

    The URL and the deployment are constrained in their types, so the API refuses a bad value when the database is
    saved. Everything that depends on another field (Cloud needs an e-mail) is checked by ``problems`` when a sync
    starts, not by a model validator, whose error would quote the whole input, token included.
    """

    base_url: Annotated[
        Annotated[str, StringConstraints(pattern=_BASE_URL_PATTERN)] | InputText,
        Field(description="Jira's base URL, e.g. https://acme.atlassian.net or https://jira.acme.ch/jira."),
    ] = ""
    deployment: Annotated[
        Literal["cloud", "data_center"] | Select, Field(description="Jira Cloud or Jira Data Center.")
    ] = "cloud"
    email: Annotated[str | InputText, Field(description="E-mail of the Jira Cloud account the token belongs to.")] = ""
    api_token: Annotated[
        str | Password, Field(description="API token (Cloud) or personal access token (Data Center).")
    ] = ""
    # Nullable because an untouched chips input submits nothing, which the normaliser turns into None.
    project_keys: Annotated[
        list[str] | ChipsInput | None, Field(description="Keys of the projects to sync; each becomes a namespace.")
    ] = None
    jql: Annotated[
        str | Textarea, Field(description="Optional JQL clause every synced issue must also match, without ORDER BY.")
    ] = ""

    @field_validator("project_keys", mode="before")
    @classmethod
    def _blank_projects_mean_none(cls, value: object) -> object:
        return None if value == "" else value

    @field_validator("project_keys", mode="after")
    @classmethod
    def _canonical_project_keys(cls, value: list[str] | ChipsInput | None) -> list[str] | ChipsInput | None:
        """Jira's project keys are upper case. Stored sorted and de-duplicated, so retyping the same projects in
        another order does not change the scope fingerprint, which would re-read everything."""
        if not isinstance(value, list):
            return value
        return sorted({key.strip().upper() for key in value if key.strip()})

    def projects(self) -> list[str]:
        return self.project_keys if isinstance(self.project_keys, list) else []

    def problems(self) -> list[str]:
        """What keeps this configuration from syncing, worded for the person who entered it."""
        found = []
        if not self.base_url:
            found.append("the Jira URL is missing")
        if not self.api_token:
            found.append("the token is missing")
        if self.deployment == "cloud" and not self.email:
            found.append("Jira Cloud needs the e-mail of the account the API token belongs to")
        if not self.projects():
            found.append("no project key is given")
        invalid = [key for key in self.projects() if not _PROJECT_KEY.match(key)]
        if invalid:
            found.append(f"{', '.join(invalid)} {'is' if len(invalid) == 1 else 'are'} not a Jira project key")
        if _ORDER_BY.search(self.jql):
            found.append("the JQL clause must not contain ORDER BY")
        return found
