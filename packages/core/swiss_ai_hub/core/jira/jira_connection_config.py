from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.i18n.locale_string import LocaleString

# An http(s) URL with no credentials, query or fragment: a "?" or "#" would turn the API path appended to it into a
# query, so the URL could name any path on any host. Empty is allowed so that an unfilled group still validates and
# problems() can say what is missing. Which hosts it may name is checked before every search (SourceHostGuard).
_BASE_URL_PATTERN = r"^(https?://[^\s/@?#]+(/[^\s?#]*)?)?$"
_I18N = "lib.jira.config"
_DEPLOYMENT_REF = "jira_connection_deployment"
_CLOUD_SELECTED = f"$get({_DEPLOYMENT_REF}).value === 'cloud'"

JiraDeployment = Literal["cloud", "data_center"]


class JiraConnectionConfig(StepConfig):
    """Where Jira is and how to sign in to it — injected as a StepConfig into the steps that read Jira.

    It carries no projects or query: those belong to the agent that embeds it. Rules that depend on another field
    (Cloud needs an e-mail) are reported by ``problems`` when a search starts, never by a validator, which would
    take the whole profile down on every event (ADR 2026_08_07) and quote the token in its error.
    """

    base_url: Annotated[
        Annotated[str, StringConstraints(pattern=_BASE_URL_PATTERN)] | InputText,
        Field(description="Jira's base URL, e.g. https://acme.atlassian.net or https://jira.acme.ch/jira."),
    ] = ""
    deployment: Annotated[JiraDeployment | Select, Field(description="Jira Cloud or Jira Data Center.")] = "cloud"
    email: Annotated[str | InputText, Field(description="E-mail of the Jira Cloud account the token belongs to.")] = ""
    api_token: Annotated[
        str | Password,
        Field(repr=False, description="API token without scopes (Cloud) or personal access token (Data Center)."),
    ] = ""
    page_size: Annotated[
        int,
        Field(
            ge=1,
            le=100,
            description="Deployment-fixed: issues asked for per search page. Jira answers at most 100 when fields "
            "are requested, and Cloud returns fewer when the fields are large, so paging never relies on it.",
        ),
    ] = 100
    request_timeout_seconds: Annotated[
        float,
        Field(gt=0, le=120, description="Deployment-fixed: how long one request may take before it is given up."),
    ] = 30.0
    max_tickets: Annotated[
        int,
        Field(
            ge=1,
            le=10_000,
            description="Deployment-fixed: a search matching more tickets fails instead of being cut short, so one "
            "chat message cannot pull a whole project into an agent's memory.",
        ),
    ] = 1000

    def problems(self) -> list[str]:
        """What keeps this connection from being used, worded for the administrator who entered it."""
        found = []
        if not self.base_url:
            found.append("the Jira URL is missing")
        if not self.api_token:
            found.append("the token is missing")
        if self.deployment == "cloud" and not self.email:
            found.append("Jira Cloud needs the e-mail of the account the API token belongs to")
        return found

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            base_url=InputText(
                **cls._labels("base_url"),
                placeholder="https://acme.atlassian.net",
                required=True,
                additional_validation_rules="url",
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
            ),
            email=InputText(**cls._labels("email"), required=True, condition_if=_CLOUD_SELECTED),
            api_token=Password(**cls._labels("api_token"), feedback=False, toggle_mask=True, required=True),
        )

    @staticmethod
    def _labels(field: str) -> dict[str, LocaleString]:
        return {
            "label": LocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": LocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
