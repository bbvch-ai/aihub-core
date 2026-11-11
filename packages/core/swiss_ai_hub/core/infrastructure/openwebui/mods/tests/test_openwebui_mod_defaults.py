import json
from pathlib import Path

import pytest
from pydantic_settings import SettingsError

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_defaults import OpenWebuiModDefaults

pytestmark = pytest.mark.unit


class TestOpenWebuiModDefaults:
    def test_defaults_follow_builtins_without_pinning_and_copy_settings(self, bundled_packages: None) -> None:
        first = OpenWebuiModDefaults.configuration()
        second = OpenWebuiModDefaults.configuration()
        assert all(mod.publication is None for mod in first.mods)
        assert [mod.mod_id for mod in first.mods if mod.enabled] == ['builtin-default']
        first.mods[0].settings['text']['en'] = 'Changed'
        assert second.mods[0].settings['text']['en'] != 'Changed'
        assert set(OpenWebuiModBundles.packages()) == {mod.mod_id for mod in first.mods}

    def test_empty_registry_has_no_defaults(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(OpenWebuiModBundles, "directory", staticmethod(lambda: tmp_path / "absent"))
        monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", "[]")
        assert OpenWebuiModBundles.packages() == {}
        assert OpenWebuiModDefaults.configuration().mods == []

    def test_unset_or_empty_defaults_leave_discovered_mods_disabled(
        self, bundled_packages: None, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("OPENWEBUI_MODS_DEFAULTS")
        assert all(not mod.enabled for mod in OpenWebuiModDefaults.configuration().mods)
        monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", "[]")
        assert all(not mod.enabled for mod in OpenWebuiModDefaults.configuration().mods)

    def test_default_ids_preserve_order_and_use_manifest_settings(
        self, bundled_packages: None, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", '["builtin-optional","builtin-default"]')
        mods = OpenWebuiModDefaults.configuration().mods
        assert [mod.mod_id for mod in mods] == ["builtin-optional", "builtin-default"]
        assert all(mod.enabled and mod.publication is None for mod in mods)
        assert all(mod.settings == {"text": {"en": "Default fixture text"}} for mod in mods)

    @pytest.mark.parametrize("value", [
        "not json", "{}", "[123]", "[null]",
        '["builtin-default","builtin-default"]',
        '["missing-mod"]',
        '[{"mod_id":"builtin-default"}]',
        json.dumps(["builtin-default"] * 65),
    ])
    def test_invalid_deployment_defaults_fail_explicitly(
        self, bundled_packages: None, monkeypatch: pytest.MonkeyPatch, value: str,
    ) -> None:
        monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", value)
        with pytest.raises((ValueError, SettingsError)):
            OpenWebuiModDefaults.configuration()

    def test_unknown_mod_error_identifies_the_setting_and_id(
        self, bundled_packages: None, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", '["uploaded-mod"]')
        with pytest.raises(ValueError, match="OPENWEBUI_MODS_DEFAULTS.*uploaded-mod"):
            OpenWebuiModDefaults.configuration()
