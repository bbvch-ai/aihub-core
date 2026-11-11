import hashlib
import hmac
import json
from typing import Literal
from urllib.parse import quote

import httpx
from fastapi import HTTPException

from aihub_mods.mod_snapshot import ModSnapshot


class HubClient:
    MAX_RESPONSE_BYTES = 16 * 1024 * 1024

    def __init__(
        self, base_url: str, api_key: str, signing_secret: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.configured = bool(base_url and api_key and signing_secret)
        self.api_key = api_key
        self.signing_secret = signing_secret.encode()
        self.http = httpx.AsyncClient(base_url=base_url, timeout=30, transport=transport)

    def _headers(self, name: str, email: str) -> dict[str, str]:
        name = quote(name or "User", safe="")
        signature = hmac.new(self.signing_secret, f"name:{name},email:{email}".encode(), hashlib.sha256).hexdigest()
        return {
            "Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
            "X-OpenWebUI-User-Name": name, "X-OpenWebUI-User-Email": email, "X-OpenWebUI-Signature": signature,
        }

    async def request(
        self, method: Literal["GET", "POST", "HEAD"], tenant_id: str, suffix: str,
        *, name: str, email: str, content: bytes | None = None, compatibility: bytes | None = None,
    ) -> bytes:
        if not self.configured:
            raise HTTPException(503, "AI Hub mod delivery is not configured.")
        tenant = quote(tenant_id, safe="")
        if tenant in {".", ".."}:
            tenant = tenant.replace(".", "%2E")
        path = f"/api/v1/{tenant}/openai/mods{suffix}"
        headers = self._headers(name, email)
        if compatibility is not None:
            headers["X-AIHub-Mod-Compatibility"] = json.dumps(json.loads(compatibility), separators=(",", ":"))
        try:
            async with self.http.stream(method, path, headers=headers, content=content) as response:
                if response.status_code >= 500:
                    raise HTTPException(503, "AI Hub mod delivery is unavailable.")
                if response.status_code != 200:
                    raise HTTPException(response.status_code if response.is_client_error else 502, "AI Hub refused mod access.")
                expected = "application/zip" if suffix.endswith(("/frontend", "/source")) else "application/json"
                if method != "HEAD" and response.headers.get("content-type", "").split(";", 1)[0] != expected:
                    raise HTTPException(502, "Unexpected AI Hub mod response.")
                result = bytearray()
                async for chunk in response.aiter_bytes():
                    result.extend(chunk)
                    if len(result) > self.MAX_RESPONSE_BYTES:
                        raise HTTPException(502, "AI Hub mod response exceeds the size limit.")
                return bytes(result)
        except httpx.RequestError as error:
            raise HTTPException(503, "AI Hub mod delivery is unavailable.") from error

    async def configuration(
        self, *, name: str, email: str, compatibility: bytes,
    ) -> ModSnapshot:
        content = await self.request("POST", "active", "/configuration", name=name, email=email, content=compatibility)
        return ModSnapshot.from_response(content, compatibility)
