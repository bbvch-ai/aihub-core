import logging
from datetime import datetime
from urllib.parse import quote

import aiohttp
import httpx
from aihub_lib.infrastructure.rclone import RcloneSettings, RcloneSourceConfig

from aihub_pipeline.types.RcloneFile import MinimalRcloneFile, RcloneFile

logger = logging.getLogger(__name__)


class RcloneClient:
    """
    Unified Rclone Client.

    - Uses `httpx` (Sync) for configuration management (create/check remotes).
    - Uses `aiohttp` (Async) for high-performance file operations (list/download).

    Authentication:
        When RCLONE_RC_USER and RCLONE_RC_PASS are set, all requests are
        authenticated using HTTP Basic Auth. This is required in non-dev
        environments where rclone is started with --rc-user and --rc-pass.
    """

    def __init__(self, base_url: str | None = None, default_remote: str | None = None, timeout: int = 30):
        settings = RcloneSettings()
        self.base_url = (base_url or settings.URL).rstrip("/")
        self.default_remote = default_remote
        self.timeout = timeout

        # Configure authentication if credentials are provided
        if settings.RC_USER and settings.RC_PASS:
            self._httpx_auth = httpx.BasicAuth(settings.RC_USER, settings.RC_PASS.get_secret_value())
            self._aiohttp_auth = aiohttp.BasicAuth(settings.RC_USER, settings.RC_PASS.get_secret_value())
        else:
            self._httpx_auth = None
            self._aiohttp_auth = None

    def upsert_remote(self, config: RcloneSourceConfig) -> None:
        """
        Creates or updates a remote configuration in Rclone.
        """
        url = f"{self.base_url}/config/create"
        payload = config.to_rclone_params()

        logger.info(f"Configuring remote: {config.name}")
        with httpx.Client(timeout=self.timeout, auth=self._httpx_auth) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()

    def remote_exists(self, name: str) -> bool:
        """
        Checks if a remote configuration exists.
        """
        url = f"{self.base_url}/config/get"
        try:
            with httpx.Client(timeout=self.timeout, auth=self._httpx_auth) as client:
                response = client.post(url, json={"name": name})

                if response.status_code != 200:
                    return False

                # Rclone returns empty object if not found or error
                data = response.json()
                return bool(data)
        except httpx.RequestError:
            return False

    def ensure_remote(self, config: RcloneSourceConfig) -> None:
        """
        Ensures the remote exists, but does NOT overwrite if it is already there.
        """
        if not self.remote_exists(config.name):
            self.upsert_remote(config)

    async def list_files(
        self, include: list[str] | None = None, exclude: list[str] | None = None, remote: str | None = None
    ) -> list[MinimalRcloneFile]:
        """
        List files with metadata using Rclone 'FilterRule'.
        """
        target_remote = self._resolve_remote(remote)
        filter_rules = []

        # 1. PRIORITY: Excludes (Noise)
        if exclude:
            filter_rules.extend([f"- {p}" for p in exclude])

        # 2. TARGETS: Includes (Scope)
        if include:
            filter_rules.extend([f"+ {p}" for p in include])

        # 3. CLEANUP: Implicit Exclude
        if include:
            filter_rules.append("- **")

        params = {
            "fs": target_remote,
            "remote": "",
            "opt": {"recurse": True, "filesOnly": True, "showHash": True},
        }

        if filter_rules:
            params["_filter"] = {"FilterRule": filter_rules}

        data = await self._async_post("operations/list", params)

        return [self._parse_minimal(item, target_remote) for item in data.get("list", []) if not item.get("IsDir")]

    async def download_bytes(self, file_path: str, remote: str | None = None) -> RcloneFile:
        """
        Download via native HTTP serve (Requires rclone started with --rc-serve).
        """
        target_remote = self._resolve_remote(remote)
        clean_path = file_path.lstrip("/")

        stat_params = {"fs": target_remote, "remote": clean_path}
        stat = await self._async_post("operations/stat", stat_params)
        item = stat.get("item", {})

        # Construct the download url: http://host:port/[remote]/path
        # URL-encode remote and path to handle special characters (spaces, etc.)
        remote_quoted = quote(target_remote, safe="")
        path_quoted = quote(clean_path, safe="/")
        download_url = f"{self.base_url}/[{remote_quoted}]/{path_quoted}"

        timeout_config = aiohttp.ClientTimeout(total=None, sock_read=600, sock_connect=30)

        async with aiohttp.ClientSession(timeout=timeout_config, auth=self._aiohttp_auth) as session:
            async with session.get(download_url) as resp:
                resp.raise_for_status()
                content = await resp.read()

        mod_time = self._to_unix_timestamp(item.get("ModTime"))

        return RcloneFile(
            name=item["Name"],
            path=item["Path"],
            content=content,
            size=item.get("Size", 0),
            modified=mod_time,
            created=self._to_unix_timestamp(item.get("BirthTime")) or mod_time,
            remote=target_remote,
            remote_path=item["Path"],
            mime_type=item.get("MimeType"),
            id=item.get("ID"),
        )

    def _resolve_remote(self, remote_arg: str | None) -> str:
        """Use the argument if provided, otherwise the default from __init__."""
        remote = remote_arg or self.default_remote
        if not remote:
            raise ValueError("Remote name must be provided either in __init__ or method call.")
        return remote

    async def _async_post(self, endpoint: str, params: dict) -> dict:
        """Helper for async JSON requests."""
        async with aiohttp.ClientSession(auth=self._aiohttp_auth) as session:
            async with session.post(f"{self.base_url}/{endpoint}", json=params) as resp:
                resp.raise_for_status()
                return await resp.json()

    def _parse_minimal(self, item: dict, remote: str) -> MinimalRcloneFile:
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
            dt = datetime.fromisoformat(rfc3339_str.replace("Z", "+00:00"))
            return int(dt.timestamp())
        except ValueError:
            return 0
