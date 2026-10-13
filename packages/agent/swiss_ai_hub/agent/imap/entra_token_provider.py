import asyncio
from typing import Annotated, Self

from azure.identity import ClientSecretCredential
from swiss_ai_hub.core.imap import ImapClientConfig

_REQUIRED_OAUTH2_FIELDS = ("tenant_id", "client_id", "client_secret")


class EntraTokenProvider:
    """Acquires an app-only (client credentials) access token from Microsoft Entra ID for IMAP ``XOAUTH2`` login.

    The credential is synchronous and runs off the event loop via ``asyncio.to_thread``, like every imapclient call:
    the async variant needs aiohttp as its transport, which the agent does not otherwise depend on. A new credential
    per token is deliberate — steps open their own connection, and a run makes only a handful of them.
    """

    def __init__(
        self,
        tenant_id: Annotated[str, "Entra ID directory (tenant) id"],
        client_id: Annotated[str, "Application (client) id of the app registration"],
        client_secret: Annotated[str, "Client secret of the app registration"],
        authority: Annotated[str, "Entra ID authority host, e.g. login.microsoftonline.com"],
        scope: Annotated[str, "Scope the token is requested for"],
    ) -> None:
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._authority = authority
        self._scope = scope

    @classmethod
    def from_config(cls, config: ImapClientConfig) -> Self:
        """Build a provider, refusing a config with an empty Entra ID field.

        Checked here rather than in a config validator: an agent config is validated on every dispatched event, so a
        validator would take the whole profile down instead of failing only the step that logs in (ADR 2026_08_07).
        Only field names reach the message — it surfaces in the user's chat, and one of the fields is a secret.
        """
        missing = [field for field in _REQUIRED_OAUTH2_FIELDS if not getattr(config, field)]
        if missing:
            raise ValueError(
                f"Microsoft 365 (OAuth 2.0) login is selected but these fields are empty: {', '.join(missing)}. "
                "Fill in the Entra ID app registration details on the agent profile."
            )
        return cls(config.tenant_id, config.client_id, config.client_secret, config.oauth_authority, config.oauth_scope)

    async def get_token(self) -> str:
        credential = ClientSecretCredential(
            self._tenant_id, self._client_id, self._client_secret, authority=self._authority
        )
        try:
            access_token = await asyncio.to_thread(credential.get_token, self._scope)
        finally:
            credential.close()
        return access_token.token
