import pytest

from swiss_ai_hub.core.infrastructure.structured_pipeline.structured_pipeline_settings import (
    StructuredPipelineSettings,
)


class TestDefaults:
    def test_a_deployment_that_sets_nothing_syncs_before_the_midnight_ingestion_run(self):
        settings = StructuredPipelineSettings()

        assert settings.OBSERVE_JOB_HOUR == 22
        assert settings.OBSERVE_JOB_MINUTE == 0


class TestEnvironmentOverrides:
    def test_the_schedule_comes_from_the_environment(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("STRUCTURED_PIPELINE_OBSERVE_JOB_HOUR", "3")
        monkeypatch.setenv("STRUCTURED_PIPELINE_OBSERVE_JOB_MINUTE", "30")

        settings = StructuredPipelineSettings()

        assert settings.OBSERVE_JOB_HOUR == 3
        assert settings.OBSERVE_JOB_MINUTE == 30

    def test_the_rclone_pipelines_variables_do_not_leak_in(self, monkeypatch: pytest.MonkeyPatch):
        """Both source pipelines run on one stack; each must read only its own prefix."""
        monkeypatch.setenv("RCLONE_PIPELINE_OBSERVE_JOB_HOUR", "5")

        assert StructuredPipelineSettings().OBSERVE_JOB_HOUR == 22

    @pytest.mark.parametrize(("variable", "value"), [("OBSERVE_JOB_HOUR", "24"), ("OBSERVE_JOB_MINUTE", "60")])
    def test_an_out_of_range_schedule_is_rejected(self, monkeypatch: pytest.MonkeyPatch, variable: str, value: str):
        monkeypatch.setenv(f"STRUCTURED_PIPELINE_{variable}", value)

        with pytest.raises(ValueError):
            StructuredPipelineSettings()
