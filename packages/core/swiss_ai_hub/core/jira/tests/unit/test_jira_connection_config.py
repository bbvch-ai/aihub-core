from typing import Annotated

import pytest
from pydantic import Field, ValidationError

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.password import Password
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.secret_field_walker import SecretFieldWalker
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.jira.jira_connection_config import JiraConnectionConfig

_LOCALES = ("en", "de", "fr", "it")
_TUNING_FIELDS = ("page_size", "request_timeout_seconds", "max_tickets")


def _cloud(**overrides: object) -> JiraConnectionConfig:
    values = {"base_url": "https://acme.atlassian.net", "email": "bot@acme.ch", "api_token": "secret-token"}
    return JiraConnectionConfig(**{**values, **overrides})


class TestData:
    def test_an_unfilled_group_still_validates(self):
        """A cross-field check here would fail every dispatched event and take the profile down (ADR 2026_08_07)."""
        config = JiraConnectionConfig()

        assert (config.base_url, config.deployment, config.email, config.api_token) == ("", "cloud", "", "")

    def test_the_tuning_knobs_have_safe_defaults(self):
        config = JiraConnectionConfig()

        assert (config.page_size, config.request_timeout_seconds, config.max_tickets) == (100, 30.0, 1000)

    def test_the_token_never_appears_in_the_repr(self):
        assert "secret-token" not in repr(_cloud())

    @pytest.mark.parametrize(
        "url", ["https://acme.atlassian.net", "https://jira.acme.ch/jira", "http://localhost:8094", ""]
    )
    def test_a_plain_http_url_is_accepted(self, url: str):
        assert _cloud(base_url=url).base_url == url

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil.example/x?",
            "https://evil.example/#",
            "https://user:pass@jira.acme.ch",
            "jira.acme.ch",
            "ftp://jira.acme.ch",
        ],
    )
    def test_a_url_that_could_name_another_path_or_carry_credentials_is_refused(self, url: str):
        """A ``?`` or ``#`` would turn the API path appended to the URL into a query or fragment."""
        with pytest.raises(ValidationError, match="base_url"):
            _cloud(base_url=url)

    def test_an_unknown_edition_is_refused(self):
        with pytest.raises(ValidationError, match="deployment"):
            _cloud(deployment="server")

    @pytest.mark.parametrize(("field", "value"), [("page_size", 0), ("page_size", 101), ("max_tickets", 0)])
    def test_a_tuning_knob_out_of_bounds_is_refused(self, field: str, value: int):
        with pytest.raises(ValidationError, match=field):
            _cloud(**{field: value})


class TestProblems:
    def test_a_complete_cloud_connection_has_none(self):
        assert _cloud().problems() == []

    def test_an_unfilled_group_names_everything_missing(self):
        assert JiraConnectionConfig().problems() == [
            "the Jira URL is missing",
            "the token is missing",
            "Jira Cloud needs the e-mail of the account the API token belongs to",
        ]

    def test_data_center_needs_no_email(self):
        config = JiraConnectionConfig(base_url="https://jira.acme.ch/jira", deployment="data_center", api_token="pat")

        assert config.problems() == []

    def test_no_problem_quotes_the_token(self):
        assert not any("secret-token" in problem for problem in _cloud(email="").problems())


class TestForm:
    def test_the_edition_offers_cloud_and_data_center(self):
        deployment = JiraConnectionConfig.as_form().deployment

        assert isinstance(deployment, Select)
        assert [option["value"] for option in deployment.options] == ["cloud", "data_center"]
        assert deployment.ref == "jira_connection_deployment"

    def test_the_email_is_asked_for_cloud_only(self):
        assert JiraConnectionConfig.as_form().email.condition_if == "$get(jira_connection_deployment).value === 'cloud'"

    def test_the_token_is_the_only_secret(self):
        form = JiraConnectionConfig.as_form()

        assert isinstance(form.api_token, Password)
        assert SecretFieldWalker.secret_paths(form.to_formkit_form()) == {"api_token"}

    def test_the_tuning_knobs_are_not_editable_in_the_form(self):
        configurable = JiraConnectionConfig.as_form().get_configurable_fields()

        assert configurable == {"base_url", "deployment", "email", "api_token"}

    @pytest.mark.parametrize(("field", "bound"), [("page_size", "maximum"), ("max_tickets", "maximum")])
    def test_the_tuning_knobs_are_bounded_in_the_announced_schema(self, field: str, bound: str):
        """A direct API save can set them, so the schema the API validates against must refuse silly values."""
        schema = JiraConnectionConfig.to_form_submission_model().model_json_schema()

        assert bound in schema["properties"][field]
        assert schema["properties"][field]["minimum"] == 1

    @pytest.mark.parametrize(
        "path",
        [
            *(
                f"{field}.{part}"
                for field in ("base_url", "deployment", "email", "api_token")
                for part in ("label", "help")
            ),
            "deployment.cloud",
            "deployment.data_center",
        ],
    )
    def test_every_label_is_translated(self, path: str):
        """A missing key resolves to the path itself, so an untranslated label would reach the UI as raw text."""
        full_path = f"lib.jira.config.{path}"
        label = LocaleString.from_i18n_path(full_path)
        for locale in _LOCALES:
            value = getattr(label, locale)
            assert value, f"{full_path} is empty in {locale}"
            assert value != full_path, f"{full_path} is missing in {locale}"


class _ProfileWithJira(AgentConfig):
    jira: Annotated[JiraConnectionConfig, Field(description="Jira connection.")]


class TestInAnAgentProfile:
    def test_a_step_receives_the_group_by_its_type(self):
        """Steps get a StepConfig by the exact annotation, so one Jira group per profile is what reaches them."""
        name = LocaleString(en="Release notes")
        profile = _ProfileWithJira(agent_id="release-notes", name=name, description=name, jira=_cloud())

        assert profile.get_step_configs()[JiraConnectionConfig] is profile.jira
