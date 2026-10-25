import pytest

from swiss_ai_hub.core.mcp.mcp_settings import McpSettings


class TestAllowedPrivateHosts:
    def test_an_empty_setting_allows_no_internal_host(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MCP_ALLOWED_PRIVATE_HOSTS", "")

        assert McpSettings().private_host_allow_list() == frozenset()

    def test_hosts_are_read_comma_separated_trimmed_and_lower_cased(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("MCP_ALLOWED_PRIVATE_HOSTS", " API , Mcp.Intra.Acme.ch,, ")

        assert McpSettings().private_host_allow_list() == frozenset({"api", "mcp.intra.acme.ch"})
