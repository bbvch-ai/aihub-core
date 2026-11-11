import json
from pathlib import Path

import pytest

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles

pytestmark = pytest.mark.unit


class TestOpenWebuiModBundles:
    @staticmethod
    def write_mod(directory: Path, mod_id: str) -> None:
        directory.mkdir()
        (directory / "mod.json").write_text(json.dumps({
            "format": 1, "id": mod_id, "name": mod_id, "version": "1", "frontend": "main.js",
        }))
        (directory / "main.js").write_text("export function activate() {}")

    def test_new_manifest_is_discovered_without_registration(
        self, bundled_packages: None,
    ) -> None:
        directory = OpenWebuiModBundles.directory()
        assert set(OpenWebuiModBundles.packages()) == {"builtin-default", "builtin-optional"}
        (directory / "not-a-mod").mkdir()
        self.write_mod(directory / "another-mod", "new-builtin")
        assert OpenWebuiModBundles.names() == ("another-mod", "default-example", "optional-example")
        assert set(OpenWebuiModBundles.packages()) == {"builtin-default", "builtin-optional", "new-builtin"}

    def test_duplicate_manifest_ids_are_rejected(self, bundled_packages: None) -> None:
        self.write_mod(OpenWebuiModBundles.directory() / "duplicate", "builtin-default")
        with pytest.raises(ValueError, match="Duplicate bundled mod ID: builtin-default"):
            OpenWebuiModBundles.packages()

    @pytest.mark.parametrize("name", ["../default-example", "/default-example", "not-installed"])
    def test_source_requires_a_discovered_directory(self, bundled_packages: None, name: str) -> None:
        with pytest.raises(ValueError, match="Unknown bundled mod"):
            OpenWebuiModBundles.source(name)
