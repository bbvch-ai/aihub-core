import logging
from datetime import datetime
from typing import Any
from urllib.parse import quote

import aiohttp
import httpx
from swiss_ai_hub.core.infrastructure.rclone import RcloneSettings, RcloneSourceConfig

from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile, RcloneFile

logger = logging.getLogger(__name__)

# `obscure`: rclone stores password-typed options obscured and refuses plain ones for them (SFTP `pass`).
# `nonInteractive`: an OAuth backend without a token returns a question instead of blocking the daemon.
_CREATE_OPTIONS = {"obscure": True, "nonInteractive": True}


class RcloneClient:
    """
    Stateless client for the rclone daemon's RC API.

    Remote management uses ``httpx`` (sync, called from ops); listing and downloading use ``aiohttp`` (async, large
    transfers). Credentials only ever travel in the body of ``config/create``; every later call names the remote,
    so neither URLs nor logs carry a secret.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        settings = RcloneSettings()
        self.base_url = (base_url or settings.URL).rstrip("/")
        self.timeout = timeout

        if settings.RC_USER and settings.RC_PASS:
            self._httpx_auth = httpx.BasicAuth(settings.RC_USER, settings.RC_PASS.get_secret_value())
            self._aiohttp_auth = aiohttp.BasicAuth(settings.RC_USER, settings.RC_PASS.get_secret_value())
        else:
            self._httpx_auth = None
            self._aiohttp_auth = None

    def upsert_remote(self, config: RcloneSourceConfig) -> None:
        """Creates the remote or replaces it wholesale.

        ``config/create`` drops an existing section before writing, unlike ``config/update`` which merges and
        would keep a stale option (an old key file after switching to password auth). The daemon runs without a
        config file, so this is also what re-creates every remote after a restart.
        """
        payload = {**config.to_rclone_params(), "opt": _CREATE_OPTIONS}
        logger.info(f"Configuring rclone remote '{config.name}' ({config.backend_type.value})")
        response = self._sync_post("config/create", payload)
        if response.get("State") or response.get("Option"):
            raise ValueError(
                f"rclone remote '{config.name}' needs an interactive step ({response.get('Option', {}).get('Name')}); "
                "supply a pre-obtained token instead."
            )

    def get_remote(self, name: str) -> dict[str, Any] | None:
        response = self._sync_post("config/get", {"name": name})
        return response or None

    def delete_remote(self, name: str) -> None:
        self._sync_post("config/delete", {"name": name})

    async def list_files(
        self, remote: str, include: list[str] | None = None, exclude: list[str] | None = None
    ) -> list[MinimalRcloneFile]:
        """Files below ``remote`` with metadata, filtered by rclone filter rules: excludes first, then includes,
        then everything else out when any include was given."""
        filter_rules = [f"- {pattern}" for pattern in exclude or []]
        filter_rules += [f"+ {pattern}" for pattern in include or []]
        if include:
            filter_rules.append("- **")

        params: dict[str, Any] = {
            "fs": remote,
            "remote": "",
            "opt": {"recurse": True, "filesOnly": True, "showHash": True},
        }
        if filter_rules:
            params["_filter"] = {"FilterRule": filter_rules}

        data = await self._async_post("operations/list", params)
        return [self._parse_minimal(item, remote) for item in data.get("list", []) if not item.get("IsDir")]

    async def download_bytes(self, remote: str, file_path: str) -> RcloneFile:
        """Download through the daemon's HTTP serve (``--rc-serve``), which streams without a temp file."""
        clean_path = file_path.lstrip("/")
        stat = await self._async_post("operations/stat", {"fs": remote, "remote": clean_path})
        item = stat.get("item", {})

        download_url = f"{self.base_url}/[{quote(remote, safe='')}]/{quote(clean_path, safe='/')}"
        timeout_config = aiohttp.ClientTimeout(total=None, sock_read=600, sock_connect=30)
        async with aiohttp.ClientSession(timeout=timeout_config, auth=self._aiohttp_auth) as session:
            async with session.get(download_url) as response:
                response.raise_for_status()
                content = await response.read()

        mod_time = self._to_unix_timestamp(item.get("ModTime"))
        return RcloneFile(
            name=item["Name"],
            path=item["Path"],
            content=content,
            size=item.get("Size", 0),
            modified=mod_time,
            created=self._to_unix_timestamp(item.get("BirthTime")) or mod_time,
            remote=remote,
            remote_path=item["Path"],
            mime_type=item.get("MimeType"),
            id=item.get("ID"),
        )

    def _sync_post(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout, auth=self._httpx_auth) as client:
            response = client.post(f"{self.base_url}/{endpoint}", json=params)
            if response.is_error:
                # httpx's own message would echo the request; the body is what rclone has to say and never
                # contains the credentials that were sent.
                raise RuntimeError(f"rclone {endpoint} failed with HTTP {response.status_code}: {response.text}")
            return response.json() if response.content else {}

    async def _async_post(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        timeout_config = aiohttp.ClientTimeout(total=None, sock_read=600, sock_connect=30)
        async with aiohttp.ClientSession(timeout=timeout_config, auth=self._aiohttp_auth) as session:
            async with session.post(f"{self.base_url}/{endpoint}", json=params) as response:
                response.raise_for_status()
                return await response.json()

    def _parse_minimal(self, item: dict[str, Any], remote: str) -> MinimalRcloneFile:
        mod_time = self._to_unix_timestamp(item.get("ModTime"))
        birth_time = self._to_unix_timestamp(item.get("Metadata", {}).get("btime")) or mod_time
        return MinimalRcloneFile(
            name=item["Name"],
            path=item["Path"],
            size=item.get("Size", 0),
            modified=mod_time,
            created=birth_time,
            remote=remote,
            is_dir=False,
            mime_type=item.get("MimeType"),
            id=item.get("ID"),
            hashes=item.get("Hashes"),
        )

    @staticmethod
    def _to_unix_timestamp(rfc3339_str: str | None) -> int:
        if not rfc3339_str:
            return 0
        try:
            return int(datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00")).timestamp())
        except ValueError:
            return 0
