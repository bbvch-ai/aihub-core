import pytest

from swiss_ai_hub.core.infrastructure.api.tenant_default_access_settings import TenantDefaultAccessSettings

ENV = "AIHUB_TENANT_DEFAULT_ACCESS_EXCLUDED_MODELS"


class TestExcludedModelsParsing:
    def test_unset_still_withholds_the_model_qc_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The default carries the policy, so a deployment that configures nothing still gets it."""
        monkeypatch.delenv(ENV, raising=False)
        assert TenantDefaultAccessSettings().excluded_models_list == ["text-generation/Apertus-70B-Instruct-2509"]

    def test_empty_string_excludes_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV, "")
        assert TenantDefaultAccessSettings().excluded_models_list == []

    def test_comma_separated_values_are_split(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV, "text-generation/a,embedding/b")
        assert TenantDefaultAccessSettings().excluded_models_list == ["text-generation/a", "embedding/b"]

    def test_whitespace_and_empty_segments_are_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(ENV, " text-generation/a ,, embedding/b , ")
        assert TenantDefaultAccessSettings().excluded_models_list == ["text-generation/a", "embedding/b"]
