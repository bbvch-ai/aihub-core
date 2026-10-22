import pytest

from swiss_ai_hub.core.infrastructure.jira.jira_settings import JiraSettings


class TestAllowedPrivateHosts:
    def test_an_empty_setting_allows_no_internal_host(self, monkeypatch: pytest.MonkeyPatch):
        """Set explicitly, so a developer's own environment cannot make this pass or fail."""
        monkeypatch.setenv("JIRA_ALLOWED_PRIVATE_HOSTS", "")

        assert JiraSettings().private_host_allow_list() == frozenset()

    def test_hosts_are_read_comma_separated_trimmed_and_lower_cased(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("JIRA_ALLOWED_PRIVATE_HOSTS", " Jira.Intra.Acme.ch , localhost,, ")

        assert JiraSettings().private_host_allow_list() == frozenset({"jira.intra.acme.ch", "localhost"})

    def test_the_named_variable_is_the_one_read(self, monkeypatch: pytest.MonkeyPatch):
        """The guard's refusal tells the operator this name, so it must be the variable that actually applies."""
        monkeypatch.setenv(JiraSettings.ALLOW_LIST_VARIABLE, "jira.intra.acme.ch")

        assert JiraSettings().private_host_allow_list() == frozenset({"jira.intra.acme.ch"})
