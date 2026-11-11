import json
from pathlib import Path

import pytest

from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModBundles


@pytest.fixture(autouse=True)
def bundled_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "bundled"
    for name, mod_id in (("default-example", "builtin-default"), ("optional-example", "builtin-optional")):
        manifest = {
            "format": 1, "id": mod_id, "name": name, "version": "1", "frontend": "frontend.js",
            "default_settings": {"text": {"en": "Default fixture text"}},
        }
        package = directory / name
        package.mkdir(parents=True)
        (package / "mod.json").write_text(json.dumps(manifest))
        (package / "frontend.js").write_text("export function activate() {}")
    monkeypatch.setattr(OpenWebuiModBundles, "directory", staticmethod(lambda: directory))
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", '["builtin-default"]')
