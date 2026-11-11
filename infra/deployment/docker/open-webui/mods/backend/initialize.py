import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx


class ModInitializer:
    """Compile with the host image, then reconcile through ordinary SysAdmin authorization."""

    def __init__(self, base_url: str, token: str) -> None:
        if not base_url or not token:
            raise ValueError("Mod initialization needs AIHUB_SYSADMIN_API_URL and AIHUB_SUPERUSER_API_KEY")
        self.http = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/", timeout=120,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        response = await self.http.request(method, "admin/openwebui-mods/" + path, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"Mod initialization {method} {path} failed: HTTP {response.status_code}: {response.text[:1000]}")
        return response

    async def run(self) -> None:
        async with self.http:
            host = (await self.request("GET", "host")).json()
            local = json.loads(Path(__file__).with_name("compatibility.json").read_bytes())
            if host["compatibility"] != local:
                raise RuntimeError("Initializer image differs from the running Open WebUI host")
            sources = (await self.request("GET", "builtins")).json()
            for source in sources:
                await self.publish(source, host["compatibility"])
            revisions = {source["manifest"]["id"]: source["revision"] for source in sources}
            await self.request("POST", "initialize", json=revisions)
            global_state = (await self.request("POST", "global/reconcile")).json()
            print(json.dumps({"status": "restart_required" if global_state["restart_required"] else "ready"}), flush=True)

    async def publish(self, source: dict[str, Any], compatibility: dict[str, Any]) -> None:
        revision = source["revision"]
        prefix = f"revisions/{revision}"
        publications = (await self.request("GET", prefix + "/publications")).json()
        if any(publication["manifest"]["compatibility"] == compatibility for publication in publications):
            print(f"Current: {source['manifest']['id']}", flush=True)
            return
        await self.request("POST", prefix + "/publications")
        print(f"Published: {source['manifest']['id']}", flush=True)


if __name__ == "__main__":
    asyncio.run(ModInitializer(os.environ.get("AIHUB_SYSADMIN_API_URL", ""),
                              os.environ.get("AIHUB_SUPERUSER_API_KEY", "")).run())
