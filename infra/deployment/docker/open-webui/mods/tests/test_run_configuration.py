import json
import unittest

import httpx
from fastapi import HTTPException

from aihub_mods.hub_client import HubClient
from aihub_mods.mod_snapshot import ModSnapshot


class RunConfigurationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.compatibility = b'{"openwebui":"0.11.4","python":"3.11"}'
        self.active_tenant = "one"
        self.calls: list[httpx.Request] = []
        self.response = {
            "revision": "a" * 64, "tenant_id": "one",
            "compatibility": json.loads(self.compatibility),
            "configuration": {"version": 7, "mods": [{
                "mod_id": "tools", "publication": "b" * 64, "enabled": True, "settings": {"label": "Current"},
            }]},
        }
        self.client = HubClient("http://hub", "service-token", "secret", transport=httpx.MockTransport(self.respond))

    async def asyncTearDown(self) -> None:
        await self.client.http.aclose()

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        self.assertEqual(request.headers["x-openwebui-user-email"], "reader@example.test")
        if request.url.path.endswith("/source"):
            return httpx.Response(200, content=b"private archive", headers={"content-type": "application/zip"})
        self.assertEqual(request.url.path, "/api/v1/active/openai/mods/configuration")
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.content, self.compatibility)
        return httpx.Response(200, json={**self.response, "tenant_id": self.active_tenant})

    async def resolve(self) -> ModSnapshot:
        return await self.client.configuration(
            name="Reader", email="reader@example.test", compatibility=self.compatibility,
        )

    async def test_each_operation_resolves_the_authoritative_active_tenant_configuration(self) -> None:
        first = await self.resolve()
        self.assertEqual(first.tenant_id, "one")
        self.assertEqual(first.mods[0].settings, {"label": "Current"})
        self.active_tenant = "two"
        self.response["configuration"]["mods"][0]["settings"] = {"label": "Updated"}
        second = await self.resolve()
        self.assertEqual(second.tenant_id, "two")
        self.assertEqual(second.mods[0].settings, {"label": "Updated"})
        self.assertEqual(first.mods[0].settings, {"label": "Current"})
        self.assertFalse(hasattr(first, "expires_at"))
        self.assertFalse(hasattr(first, "user_id"))

    async def test_incompatible_and_malformed_configurations_are_rejected(self) -> None:
        original = self.response.copy()
        cases = [
            ({"compatibility": {"python": "3.12"}}, 409),
            ({"revision": "invalid"}, 502),
            ({"configuration": {"mods": [{"mod_id": "tools"}]}}, 502),
        ]
        for changes, expected in cases:
            self.response = original | changes
            with self.assertRaises(HTTPException) as raised:
                await self.resolve()
            self.assertEqual(raised.exception.status_code, expected)

    async def test_private_backend_source_uses_the_zip_transport(self) -> None:
        content = await self.client.request(
            "GET", "one", f'/publications/{"b" * 64}/source', name="Reader", email="reader@example.test",
            compatibility=self.compatibility,
        )
        self.assertEqual(json.loads(self.calls[-1].headers["X-AIHub-Mod-Compatibility"]), json.loads(self.compatibility))
        self.assertEqual(content, b"private archive")


if __name__ == "__main__":
    unittest.main()
