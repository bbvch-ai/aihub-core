import pytest

from swiss_ai_hub.core.infrastructure.rag_pipeline.rag_pipeline_settings import RagPipelineSettings


class TestDefaults:
    def test_a_deployment_that_sets_nothing_keeps_the_platform_models(self):
        settings = RagPipelineSettings()

        assert settings.EMBEDDING_MODEL == "embedding/bge-m3"
        assert settings.LLM_MODEL == "text-generation/gemma-4-31B-it"
        assert settings.WITH_SUMMARY_NODES


class TestEnvironmentOverrides:
    def test_models_and_flags_come_from_the_environment(self, monkeypatch: pytest.MonkeyPatch):
        """Editing the app module was the only way to point a stack at models it actually has."""
        monkeypatch.setenv("RAG_PIPELINE_EMBEDDING_MODEL", "embedding/other")
        monkeypatch.setenv("RAG_PIPELINE_LLM_MODEL", "text-generation/other")
        monkeypatch.setenv("RAG_PIPELINE_WITH_SUMMARY_NODES", "false")
        monkeypatch.setenv("RAG_PIPELINE_OBSERVE_JOB_HOUR", "3")

        settings = RagPipelineSettings()

        assert settings.EMBEDDING_MODEL == "embedding/other"
        assert settings.LLM_MODEL == "text-generation/other"
        assert settings.WITH_SUMMARY_NODES is False
        assert settings.OBSERVE_JOB_HOUR == 3

    def test_an_out_of_range_schedule_hour_is_rejected(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("RAG_PIPELINE_OBSERVE_JOB_HOUR", "24")

        with pytest.raises(ValueError):
            RagPipelineSettings()
