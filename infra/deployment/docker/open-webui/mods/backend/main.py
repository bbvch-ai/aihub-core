import json
import os
import sys
from pathlib import Path

from aihub_mods.callable_imports import CallableImports

CallableImports.install()

from open_webui.env import VERSION
from open_webui.main import app
from open_webui.utils.auth import get_verified_user

from aihub_mods.hub_client import HubClient
from aihub_mods.mod_host import ModHost
from aihub_mods.mod_authentication import ModAuthentication

compatibility = Path(__file__).with_name("compatibility.json").read_bytes()
expected = json.loads(compatibility)
if VERSION != expected["openwebui"] or f"{sys.version_info.major}.{sys.version_info.minor}" != expected["python"]:
    raise RuntimeError("Open WebUI mod backend does not match its declared compatibility. Rebuild the host.")

host = ModHost(HubClient(
    os.environ.get("AIHUB_BASE_URL", ""), os.environ.get("AIHUB_SUPERUSER_API_KEY", ""),
    os.environ.get("OPEN_WEBUI_SIGNING_SECRET", ""),
), compatibility, Path(os.environ.get("DATA_DIR", "/app/backend/data")) / "aihub-mods")
CallableImports.bind_routes(app)
host.install(app, get_verified_user)
ModAuthentication(host.runtime).install(app)
