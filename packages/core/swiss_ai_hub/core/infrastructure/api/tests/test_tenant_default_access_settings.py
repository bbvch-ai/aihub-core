import pytest

from swiss_ai_hub.core.infrastructure.api.tenant_default_access_settings import TenantDefaultAccessSettings

ENV = "AIHUB_TENANT_DEFAULT_ACCESS_EXCLUDED_MODELS"
AGENTS_ENV = "AIHUB_TENANT_DEFAULT_ACCESS_AGENT_CLASSES"


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


class TestAgentClassesParsing:
    def test_unset_grants_the_three_standard_blueprints(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The default carries the policy, so a deployment that configures nothing still ships a curated
        catalog rather than every blueprint it happens to run."""
        monkeypatch.delenv(AGENTS_ENV, raising=False)
        assert TenantDefaultAccessSettings().agent_classes_list == [
            "LLMWrappingAgent",
            "FewShotAgent",
            "RAGAgent",
        ]

    def test_empty_string_grants_no_blueprints(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A deliberate lockout has to stay expressible, matching an explicitly empty tenant rule list."""
        monkeypatch.setenv(AGENTS_ENV, "")
        assert TenantDefaultAccessSettings().agent_classes_list == []

    def test_comma_separated_values_are_split(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(AGENTS_ENV, "RAGAgent,FewShotAgent")
        assert TenantDefaultAccessSettings().agent_classes_list == ["RAGAgent", "FewShotAgent"]

    def test_whitespace_and_empty_segments_are_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A trailing comma is the common hand-edit, and an empty segment would emit a malformed rule."""
        monkeypatch.setenv(AGENTS_ENV, " RAGAgent ,, FewShotAgent , ")
        assert TenantDefaultAccessSettings().agent_classes_list == ["RAGAgent", "FewShotAgent"]
