from typing import Annotated, ClassVar

import httpx


class OpenWebuiSessionLookup:
    """Asks OpenWebUI whose session a token is.

    OpenWebUI itself decides, so its expiry and sign-out apply without the Hub copying its token rules.
    """

    SESSION_PATH: ClassVar[str] = "/api/v1/auths/"
    TIMEOUT_SECONDS: ClassVar[float] = 5.0
    _REJECTED_STATUSES: ClassVar[frozenset[int]] = frozenset({401, 403})

    def __init__(
        self,
        base_url: Annotated[str, "OpenWebUI's in-cluster base URL"],
        transport: Annotated[httpx.AsyncBaseTransport | None, "Replaces the network in tests"] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def email_of(
        self, token: Annotated[str, "An OpenWebUI session token"]
    ) -> Annotated[str | None, "The session user's e-mail, or None when OpenWebUI rejects the token"]:
        async with httpx.AsyncClient(
            base_url=self._base_url, timeout=self.TIMEOUT_SECONDS, transport=self._transport
        ) as client:
            response = await client.get(self.SESSION_PATH, headers={"Authorization": f"Bearer {token}"})
        if response.status_code in self._REJECTED_STATUSES:
            return None
        response.raise_for_status()
        return response.json().get("email") or None
