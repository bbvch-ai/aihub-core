import json

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles


@pytest.fixture
def bundled_packages(monkeypatch: pytest.MonkeyPatch) -> None:
    names = ("default-example", "optional-example")
    sources = {}
    for name, mod_id in zip(names, ("builtin-default", "builtin-optional"), strict=True):
        manifest = {
            "format": 1, "id": mod_id, "name": name, "version": "1", "frontend": "frontend.js",
            "default_settings": {"text": {"en": "Default fixture text"}},
        }
        sources[name] = OpenWebuiModBundles.zip({
            "mod.json": json.dumps(manifest).encode(),
            "frontend.js": b"export function activate() {}",
        })
    monkeypatch.setattr(OpenWebuiModBundles, "NAMES", names)
    monkeypatch.setattr(OpenWebuiModBundles, "DEFAULT_ENABLED", frozenset({"builtin-default"}))
    monkeypatch.setattr(OpenWebuiModBundles, "source", staticmethod(lambda name: sources[name]))
