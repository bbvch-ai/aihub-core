import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from aihub_mods.frontend_cache import FrontendCache


class FrontendCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        app = FastAPI()

        @app.get("/private")
        async def private(policy: str = "private, no-store") -> HTMLResponse:
            return HTMLResponse("Private page", headers={"Cache-Control": policy})

        @app.websocket("/ws")
        async def websocket(socket: WebSocket) -> None:
            await socket.accept()
            await socket.send_text("connected")
            await socket.close()

        @app.get("/api/native")
        async def native() -> JSONResponse:
            return JSONResponse({"ok": True}, headers={"Cache-Control": "private, max-age=60"})

        temporary = self.enterContext(tempfile.TemporaryDirectory())
        files = {"index.html": "<html>Chat</html>", "_app/immutable/chunk.js": "export const native = 1;"}
        files.update({path.lstrip("/"): "export const host = 1;" for path in FrontendCache.ENTRIES})
        for path, content in files.items():
            target = Path(temporary, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        app.mount("/", StaticFiles(directory=temporary, html=True))
        app.add_middleware(FrontendCache)
        self.client = self.enterContext(TestClient(app))

    def test_stable_entries_and_documents_revalidate_including_not_modified(self) -> None:
        for path in ["/", *FrontendCache.ENTRIES]:
            with self.subTest(path=path):
                response = self.client.get(path, headers={"Sec-Fetch-Dest": "iframe" if path == "/" else "script"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers["cache-control"], "no-cache")
                cached = self.client.get(path, headers={
                    "If-None-Match": response.headers["etag"], "Sec-Fetch-Dest": "iframe" if path == "/" else "script",
                })
                self.assertEqual(cached.status_code, 304)
                self.assertEqual(cached.headers["cache-control"], "no-cache")

    def test_preserves_private_data_and_content_hashed_asset_policies(self) -> None:
        self.assertEqual(self.client.get("/private").headers["cache-control"], "private, no-store")
        self.assertEqual(self.client.get("/api/native").headers["cache-control"], "private, max-age=60")
        self.assertNotIn("cache-control", self.client.get("/_app/immutable/chunk.js").headers)

    def test_revalidation_preserves_existing_restrictions(self) -> None:
        for policy in ["private", "private, max-age=60", 'private="Set-Cookie"', 'private, no-cache="Set-Cookie"']:
            with self.subTest(policy=policy):
                response = self.client.get("/private", params={"policy": policy})
                self.assertEqual(response.headers["cache-control"], policy + ", no-cache")
        for policy in ["private, no-store", "private, No-Store", "private, no-cache", "private, No-Cache"]:
            with self.subTest(policy=policy):
                response = self.client.get("/private", params={"policy": policy})
                self.assertEqual(response.headers["cache-control"], policy)

    def test_websocket_passes_through(self) -> None:
        with self.client.websocket_connect("/ws") as socket:
            self.assertEqual(socket.receive_text(), "connected")
