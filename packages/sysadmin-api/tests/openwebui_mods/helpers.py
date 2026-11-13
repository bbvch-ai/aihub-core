import hashlib
import json
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModBundles
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService

BASE = "/api/v1/admin/openwebui-mods"


class ModTestAuth(TestAuthHandler):
    is_admin = True
    authenticated = True

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Authentication required")
        return fake_user(is_sys_admin=self.is_admin)


def install_mod(
    client: TestClient, source: bytes, publication: bytes, mod_id: str = "chat-tools", **changes: Any
) -> str:
    with ZipFile(BytesIO(source)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files["mod.json"])
    manifest.update(id=mod_id, **changes)
    files["mod.json"] = json.dumps(manifest).encode()
    source = OpenWebuiModBundles.zip(files)
    with ZipFile(BytesIO(publication)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    metadata = json.loads(files["publication.json"])
    metadata["source_revision"] = hashlib.sha256(source).hexdigest()
    files["publication.json"] = json.dumps(metadata).encode()
    with patch.object(OpenWebuiModService, "_compile", AsyncMock(return_value=OpenWebuiModBundles.zip(files))):
        response = client.post(
            BASE + "/install?replace=true", content=source, headers={"content-type": "application/zip"}
        )
    assert response.status_code == 200, response.text
    return OpenWebuiModEntity.find_mod(mod_id).publication
