import pytest
from dagster._core.storage.tags import MAX_RETRIES_TAG
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import IngestorType

from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions
from swiss_ai_hub.pipeline.util.rclone_pipeline_definitions_util import rclone_pipeline_definitions


def _names(definitions) -> dict[str, set[str]]:
    repo = definitions.get_repository_def()
    return {
        "assets": {key.to_user_string() for key in repo.asset_graph.get_all_asset_keys()},
        "jobs": {job.name for job in repo.get_all_jobs() if not job.name.startswith("__")},
        "sensors": {sensor.name for sensor in repo.sensor_defs},
        "partitions": {
            partitions_def.name
            for key in repo.asset_graph.get_all_asset_keys()
            if (partitions_def := repo.asset_graph.get(key).partitions_def) is not None
        },
    }


class TestEveryNameDerivesFromTheSource:
    def test_the_shipped_source_registers_and_names_its_registry_and_jobs_after_itself(self):
        names = _names(rclone_pipeline_definitions())

        assert names["partitions"] == {"rclone_source_partitions"}
        assert names["jobs"] == {"rclone_source_observation", "rclone_remove_source_files"}
        assert "SourcePipelineRegistrationSensorFor_rclone" in names["sensors"]
        assert "SourceBucketCleanupSensorFor_rclone" in names["sensors"]
        assert names["assets"] == {
            "rclone_source_to_datalake/remote_files",
            "rclone_source_to_datalake/data_lake_files",
            "rclone_source_to_datalake/removed_data_lake_files",
        }

    def test_two_source_pipelines_and_the_ingestion_pipeline_share_no_global_name(self):
        rclone = _names(rclone_pipeline_definitions())
        acme = _names(
            rclone_pipeline_definitions(
                source="acme_sync", display_name=LocaleString(en="Acme"), description=LocaleString(en="Acme sync")
            )
        )
        ingestion = _names(document_ingestion_pipeline_definitions())

        for kind in ("assets", "jobs", "partitions"):
            assert rclone[kind].isdisjoint(acme[kind]), kind
            assert rclone[kind].isdisjoint(ingestion[kind]), kind


class TestRegistrationGate:
    def test_an_ingestor_token_cannot_be_claimed_as_a_source(self):
        labels = {"display_name": LocaleString(en="x"), "description": LocaleString(en="x")}
        with pytest.raises(ValueError, match="reserved"):
            rclone_pipeline_definitions(source=IngestorType.DOCUMENT_INGESTION.value, **labels)

    def test_a_custom_source_without_labels_is_rejected_at_build_time(self):
        with pytest.raises(ValueError, match="display_name"):
            rclone_pipeline_definitions(source="acme_sync")


def _automation_sensor(definitions):
    return definitions.get_repository_def().get_sensor_def("AutomaterializeSensor")


class TestOnlyTheSourcePipelineRetriesAutomationRuns:
    def test_the_rclone_automation_sensor_tags_its_runs_with_max_retries(self):
        assert _automation_sensor(rclone_pipeline_definitions()).run_tags == {MAX_RETRIES_TAG: "2"}

    def test_the_ingestion_automation_sensor_leaves_its_runs_untagged(self):
        """A file that fails to parse fails every time; retrying the run would only parse it three times (#1813)."""
        assert MAX_RETRIES_TAG not in _automation_sensor(document_ingestion_pipeline_definitions()).run_tags
