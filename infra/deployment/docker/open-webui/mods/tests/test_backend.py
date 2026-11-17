import hashlib
import hmac
import json
import tempfile
import unittest
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote
from zipfile import ZipFile

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from starlette.staticfiles import StaticFiles

from aihub_mods.frontend_archive import FrontendArchive
from aihub_mods.hub_client import HubClient
from aihub_mods.mod_host import ModHost
from aihub_mods.patch_startup import StartupAdapter


class BackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.view_id = "a" * 32
        self.compatibility = b'{"openwebui":"0.11.4","python":"3.11"}'
        self.bundle = self._bundle("first")
        self.revision = hashlib.sha256(self.bundle).hexdigest()
        self.bundles = {self.revision: self.bundle}
        self.selected_revision = self.revision
        self.calls: list[httpx.Request] = []
        self.allowed = True
        self.failure = 403
        self.configuration = {
            "revision": "c" * 64, "tenant_id": "customer.acme", "compatibility": json.loads(self.compatibility),
            "configuration": {"mods": []},
        }
        self.events: list[str] = []

        async def verified_user(request: Request) -> SimpleNamespace:
            cookie = request.cookies.get("token")
            if cookie not in {"reader", "another"}:
                raise HTTPException(401, "Sign in")
            return SimpleNamespace(name="Müller", email=cookie + "@example.test")

        @asynccontextmanager
        async def upstream_lifespan(app: FastAPI) -> AsyncIterator[dict[str, bool]]:
            self.events.append("start")
            yield {"upstream_state": True}
            self.events.append("stop")

        self.app = FastAPI(lifespan=upstream_lifespan)

        @self.app.get("/api/upstream")
        async def upstream(request: Request) -> bool:
            return request.state.upstream_state

        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        Path(self.temporary.name, "index.html").write_text("<html>Original frontend</html>")
        self.app.mount("/", StaticFiles(directory=self.temporary.name, html=True), name="spa-static-files")
        self.hub = HubClient("http://hub", "test-key", "test-secret", transport=httpx.MockTransport(self._hub_response))
        self.host = ModHost(self.hub, self.compatibility)
        self.host.install(self.app, verified_user)
        self.client = self.enterContext(TestClient(self.app))
        self.client.cookies.set("token", "reader")
        self.base = f"/_aihub/mods/tenants/customer.acme/views/{self.view_id}/publications/{self.revision}"

    def _bundle(self, label: str, compatibility: dict | None = None) -> bytes:
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr("publication.json", json.dumps({
                "format": 1, "frontend": "main.js.mjs", "compatibility": compatibility or json.loads(self.compatibility),
            }))
            archive.writestr("files/main.js.mjs", f"export const label = '{label}';")
            archive.writestr("files/icon.svg", "<svg/>")
        return output.getvalue()

    def _hub_response(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        self.assertEqual(request.headers["authorization"], "Bearer test-key")
        name = quote("Müller", safe="")
        email = request.headers["x-openwebui-user-email"]
        signature = hmac.new(b"test-secret", f"name:{name},email:{email}".encode(), hashlib.sha256).hexdigest()
        self.assertEqual(request.headers["x-openwebui-user-name"], name)
        self.assertEqual(request.headers["x-openwebui-signature"], signature)
        if not self.allowed or email != "reader@example.test":
            return httpx.Response(self.failure)
        self.assertTrue(request.url.path.startswith("/api/v1/customer.acme/openai/mods/"))
        if request.method == "POST":
            self.assertEqual(request.url.path, "/api/v1/customer.acme/openai/mods/configuration")
            self.assertEqual(request.content, self.compatibility)
            return httpx.Response(200, json=self.configuration)
        self.assertEqual(json.loads(request.headers["x-aihub-mod-compatibility"]), json.loads(self.compatibility))
        revision = request.url.path.split("/")[-2]
        if revision != self.selected_revision:
            return httpx.Response(403)
        if request.method == "HEAD":
            return httpx.Response(200)
        if request.url.path.endswith("/frontend"):
            return httpx.Response(200, content=self.bundles[revision], headers={"content-type": "application/zip"})
        return httpx.Response(404)

    def test_native_routes_precede_spa_and_preserve_upstream_lifespan(self) -> None:
        self.assertEqual(self.events, ["start"])
        self.assertTrue(self.client.get("/api/upstream").json())
        self.assertIn("Original frontend", self.client.get("/").text)
        self.client.__exit__(None, None, None)
        self.assertEqual(self.events, ["start", "stop"])
        self.assertTrue(self.hub.http.is_closed)

    def test_configuration_uses_only_the_verified_user_and_host_contract(self) -> None:
        response = self.client.post("/_aihub/mods/tenants/customer.acme/configuration", json={}, headers={
            "X-OpenWebUI-User-Email": "forged@example.test", "Origin": "http://testserver",
        })
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), self.configuration)
        self.assertEqual(response.headers["cache-control"], "no-store")
        again = self.client.post("/_aihub/mods/tenants/customer.acme/configuration", json={})
        self.assertEqual(again.json(), response.json())
        self.assertTrue({"id", "user_id", "expires_at"}.isdisjoint(response.json()))

    def test_files_and_manifest_are_private_and_have_correct_types(self) -> None:
        manifest = self.client.get(self.base + "/publication.json")
        self.assertEqual(manifest.json()["frontend"], "main.js.mjs")
        module = self.client.get(self.base + "/files/main.js.mjs")
        self.assertEqual(module.status_code, 200)
        self.assertIn("text/javascript", module.headers["content-type"])
        self.assertIn("'first'", module.text)
        self.assertEqual(module.headers["cross-origin-resource-policy"], "same-origin")
        self.assertEqual(module.headers["x-content-type-options"], "nosniff")
        self.assertEqual(module.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get(self.base + "/files/icon.svg").headers["content-type"], "image/svg+xml")
        self.assertEqual([call.method for call in self.calls], ["HEAD", "GET", "HEAD", "HEAD"])

    def test_cached_archive_still_requires_authorization(self) -> None:
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 200)
        self.allowed = False
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 403)
        self.allowed = True
        self.client.cookies.set("token", "another")
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 403)
        self.assertEqual(sum(call.method == "GET" for call in self.calls), 1)

    def test_view_nonce_does_not_select_or_authorize_a_publication(self) -> None:
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 200)
        other_view = self.base.replace(self.view_id, "b" * 32)
        self.assertEqual(self.client.get(other_view + "/files/main.js.mjs").status_code, 200)
        self.selected_revision = "f" * 64
        self.assertEqual(self.client.get(other_view + "/files/main.js.mjs").status_code, 403)
        self.assertEqual(sum(call.method == "GET" for call in self.calls), 1)

    def test_host_rejects_a_publication_with_different_compatibility(self) -> None:
        bundle = self._bundle("incompatible", {"openwebui": "changed", "python": "3.11"})
        revision = hashlib.sha256(bundle).hexdigest()
        self.bundles[revision] = bundle
        self.selected_revision = revision
        response = self.client.get(self.base.replace(self.revision, revision) + "/publication.json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(len(self.host.archives), 0)

    def test_cookie_is_required_before_contacting_hub(self) -> None:
        self.client.cookies.clear()
        for path in [self.base + "/publication.json", self.base + "/files/main.js.mjs"]:
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.calls, [])

    def test_cross_origin_and_form_requests_do_not_contact_hub(self) -> None:
        for headers in [{"Origin": "https://attacker.test"}, {"Sec-Fetch-Site": "cross-site"}, {"Origin": "null"}]:
            self.assertEqual(self.client.get(self.base + "/files/main.js.mjs", headers=headers).status_code, 403)
        self.assertEqual(self.client.post("/_aihub/mods/tenants/customer.acme/configuration", data="anything").status_code, 415)
        self.assertEqual(self.calls, [])

    def test_backend_source_and_traversal_are_not_served(self) -> None:
        for suffix in ["/source", "/files/backend.py", "/files/../backend.py", "/files/%2e%2e%2fbackend.py"]:
            self.assertEqual(self.client.get(self.base + suffix).status_code, 404)

    def test_missing_publication_and_hub_failure_are_propagated(self) -> None:
        self.allowed = False
        for status, expected in [(404, 404), (409, 409), (500, 503)]:
            self.failure = status
            self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, expected)

    def test_archive_integrity_and_response_limit_are_checked(self) -> None:
        self.bundles[self.revision] = b"tampered"
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 502)
        self.assertEqual(len(self.host.archives), 0)
        self.bundles[self.revision] = self.bundle
        self.hub.MAX_RESPONSE_BYTES = len(self.bundle) - 1
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 502)

    def test_concurrent_files_download_the_archive_once(self) -> None:
        with ThreadPoolExecutor(max_workers=8) as executor:
            responses = list(executor.map(lambda _: self.client.get(self.base + "/files/main.js.mjs"), range(8)))
        self.assertTrue(all(response.status_code == 200 for response in responses))
        self.assertEqual(sum(call.method == "HEAD" for call in self.calls), 8)
        self.assertEqual(sum(call.method == "GET" for call in self.calls), 1)

    def test_archive_cache_is_bounded(self) -> None:
        other = self._bundle("second")
        revision = hashlib.sha256(other).hexdigest()
        self.bundles[revision] = other
        self.host.CACHE_BYTES = len(self.bundle) + len(other) - 1
        self.assertEqual(self.client.get(self.base + "/files/main.js.mjs").status_code, 200)
        self.selected_revision = revision
        path = self.base.replace(self.revision, revision) + "/files/main.js.mjs"
        self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(list(self.host.archives), [revision])

    def test_invalid_zip_with_matching_hash_is_rejected(self) -> None:
        content = b"not a zip"
        with self.assertRaises(HTTPException) as raised:
            FrontendArchive(hashlib.sha256(content).hexdigest(), content)
        self.assertEqual(raised.exception.status_code, 502)

    def test_startup_patch_preserves_all_other_upstream_setup(self) -> None:
        path = Path(self.temporary.name, "start.sh")
        source = 'uvicorn open_webui.main:app --host "$HOST"\nARGS=(--workers "$UVICORN_WORKERS")\npython -m uvicorn open_webui.main:app "$@"\n'
        path.write_text(source)
        StartupAdapter.patch(path)
        self.assertEqual(path.read_text(), source.replace("open_webui.main:app", "aihub_mods.main:app"))
        with self.assertRaisesRegex(RuntimeError, "startup changed"):
            StartupAdapter.patch(path)


if __name__ == "__main__":
    unittest.main()
