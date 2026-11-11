import pytest

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

    def test_empty_registry_has_no_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(OpenWebuiModBundles, "NAMES", ())
        monkeypatch.setattr(OpenWebuiModBundles, "DEFAULT_ENABLED", frozenset())
        assert OpenWebuiModBundles.packages() == {}
        assert OpenWebuiModDefaults.configuration().mods == []
