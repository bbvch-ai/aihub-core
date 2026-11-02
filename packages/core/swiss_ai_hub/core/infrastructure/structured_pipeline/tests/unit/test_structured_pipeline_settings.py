import pytest

from swiss_ai_hub.core.infrastructure.structured_pipeline.structured_pipeline_settings import (
    StructuredPipelineSettings,
)


class TestDefaults:
    def test_a_deployment_that_sets_nothing_syncs_before_the_midnight_ingestion_run(self):
        settings = StructuredPipelineSettings()

        assert settings.OBSERVE_JOB_HOUR == 22
        assert settings.OBSERVE_JOB_MINUTE == 0

    def test_an_empty_setting_allows_no_internal_host(self, monkeypatch: pytest.MonkeyPatch):
        """Set explicitly: a developer's environment, and CI's taken from .env.dev, allow localhost."""
        monkeypatch.setenv("STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS", "")

        assert StructuredPipelineSettings().private_host_allow_list() == frozenset()


class TestAllowedPrivateHosts:
    def test_hosts_are_read_comma_separated_trimmed_and_lower_cased(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS", " Jira.Intra.Acme.ch , localhost,, ")

        assert StructuredPipelineSettings().private_host_allow_list() == frozenset({"jira.intra.acme.ch", "localhost"})


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
