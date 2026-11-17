import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig


def _config(auth_mode: str, forward_tenant_id_header: str | None = "X-LCDM-Tenant") -> McpClientConfig:
    return McpClientConfig(
        name="lcdm", url="http://mcp:9000/mcp", auth_mode=auth_mode, forward_tenant_id_header=forward_tenant_id_header
    )


class TestForwardTenantHeaderRequiresUserToken:
    """Without the user token the MCP server cannot bind the header to a user, so any caller could pick a tenant."""

    @pytest.mark.parametrize("auth_mode", ["none", "api_key"])
    def test_rejects_the_header_without_user_token(self, auth_mode):
        with pytest.raises(ValidationError, match="requires auth_mode 'user_token'"):
            _config(auth_mode)

    def test_accepts_the_header_with_user_token(self):
        assert _config("user_token").forward_tenant_id_header == "X-LCDM-Tenant"

    @pytest.mark.parametrize("auth_mode", ["none", "api_key", "user_token"])
    def test_any_auth_mode_without_the_header(self, auth_mode):
        assert _config(auth_mode, forward_tenant_id_header=None).forward_tenant_id_header is None

    def test_form_mode_is_not_validated(self):
        assert McpClientConfig.as_form().forward_tenant_id_header is not None
