from unittest.mock import MagicMock, patch

import pytest
from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.testing import async_test

from swiss_ai_hub.agent.imap.entra_token_provider import EntraTokenProvider

_CREDENTIAL_PATH = "swiss_ai_hub.agent.imap.entra_token_provider.ClientSecretCredential"
_SECRET = "s3cr3t-value"


def _oauth_config(**overrides: str) -> ImapClientConfig:
    values = {
        "host": "outlook.office365.com",
        "username": "shared@contoso.com",
        "auth_method": "oauth2_client_credentials",
        "tenant_id": "tenant-guid",
        "client_id": "client-guid",
        "client_secret": _SECRET,
    }
    return ImapClientConfig(**(values | overrides))


def _credential(token: str = "access-token") -> MagicMock:
    credential = MagicMock()
    credential.get_token = MagicMock(return_value=AccessToken(token, 0))
    return credential


@async_test
async def test_get_token_requests_the_configured_scope_from_the_configured_authority():
    credential = _credential()

    with patch(_CREDENTIAL_PATH, return_value=credential) as credential_class:
        token = await EntraTokenProvider.from_config(_oauth_config()).get_token()

    assert token == "access-token"
    credential_class.assert_called_once_with(
        "tenant-guid", "client-guid", _SECRET, authority="login.microsoftonline.com"
    )
    credential.get_token.assert_called_once_with("https://outlook.office365.com/.default")


@async_test
async def test_get_token_closes_the_credential_even_when_entra_refuses():
    credential = _credential()
    credential.get_token.side_effect = ClientAuthenticationError("AADSTS7000215: Invalid client secret provided.")

    with patch(_CREDENTIAL_PATH, return_value=credential):
        with pytest.raises(ClientAuthenticationError, match="AADSTS7000215"):
            await EntraTokenProvider.from_config(_oauth_config()).get_token()

    credential.close.assert_called_once()


@pytest.mark.parametrize("field", ["tenant_id", "client_id", "client_secret"])
def test_from_config_names_the_empty_field(field: str):
    with pytest.raises(ValueError, match=field):
        EntraTokenProvider.from_config(_oauth_config(**{field: ""}))


def test_from_config_names_every_empty_field_at_once():
    with pytest.raises(ValueError, match="tenant_id, client_secret"):
        EntraTokenProvider.from_config(_oauth_config(tenant_id="", client_secret=""))


def test_from_config_never_puts_a_credential_value_in_the_message():
    """The message reaches the user's chat through the step's exception event."""
    with pytest.raises(ValueError) as raised:
        EntraTokenProvider.from_config(_oauth_config(tenant_id=""))

    assert _SECRET not in str(raised.value)
    assert "client-guid" not in str(raised.value)
