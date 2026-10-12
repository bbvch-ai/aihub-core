import os

import pytest
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import IngestorType

from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import FakeStructuredSyncConfig
from swiss_ai_hub.pipeline.util.document_ingestion_definitions_util import document_ingestion_pipeline_definitions
from swiss_ai_hub.pipeline.util.rclone_pipeline_definitions_util import rclone_pipeline_definitions
from swiss_ai_hub.pipeline.util.structured_pipeline_definitions_util import structured_pipeline_definitions


def _names(definitions) -> dict[str, set[str]]:
    repo = definitions.get_repository_def()
    return {
        "assets": {key.to_user_string() for key in repo.asset_graph.get_all_asset_keys()},
        "jobs": {job.name for job in repo.get_all_jobs() if not job.name.startswith("__")},
        "sensors": {sensor.name for sensor in repo.sensor_defs},
        "schedules": {schedule.name for schedule in repo.schedule_defs},
        "partitions": {
            partitions_def.name
            for key in repo.asset_graph.get_all_asset_keys()
            if (partitions_def := repo.asset_graph.get(key).partitions_def) is not None
        },
    }


class TestEveryNameDerivesFromTheSource:
    def test_the_shipped_source_names_its_asset_and_its_daily_job_after_itself(self):
        names = _names(structured_pipeline_definitions())

        assert names["assets"] == {"structured_source_to_datalake/records"}
        assert names["jobs"] == {"structured_source_sync"}
        assert names["schedules"] == {"PerBucketObservationAt_22_00"}
        assert names["partitions"] == set(), "one run per database, not one per record"

    def test_it_shares_no_global_name_with_the_rclone_or_the_ingestion_pipeline(self):
        structured = _names(structured_pipeline_definitions(config=FakeStructuredSyncConfig.as_form()))
        rclone = _names(rclone_pipeline_definitions())
        ingestion = _names(document_ingestion_pipeline_definitions())

        for kind in ("assets", "jobs", "partitions", "sensors"):
            assert structured[kind].isdisjoint(rclone[kind]), kind
            assert structured[kind].isdisjoint(ingestion[kind]), kind


class TestRegistration:
    def test_a_pipeline_offering_no_kind_is_not_announced(self):
        """The create-database dialog would otherwise offer a source nothing can be configured for."""
        assert (
            "SourcePipelineRegistrationSensorFor_structured" not in _names(structured_pipeline_definitions())["sensors"]
        )

    def test_a_pipeline_offering_a_kind_is_announced(self):
        names = _names(structured_pipeline_definitions(config=FakeStructuredSyncConfig.as_form()))

        assert "SourcePipelineRegistrationSensorFor_structured" in names["sensors"]

    def test_a_reserved_id_is_refused_even_before_any_kind_is_offered(self):
        with pytest.raises(ValueError, match="reserved"):
            structured_pipeline_definitions(source=IngestorType.DOCUMENT_INGESTION.value)

    def test_a_custom_source_needs_labels(self):
        with pytest.raises(ValueError, match="display_name"):
            structured_pipeline_definitions(source="acme_records")

    def test_a_custom_source_with_labels_derives_its_names_from_its_own_id(self):
        names = _names(
            structured_pipeline_definitions(
                source="acme_records",
                display_name=LocaleString(en="Acme"),
                description=LocaleString(en="Acme records"),
                config=FakeStructuredSyncConfig.as_form(),
            )
        )

        assert names["jobs"] == {"acme_records_source_sync"}
        assert "SourcePipelineRegistrationSensorFor_acme_records" in names["sensors"]


class TestTelemetry:
    def test_building_the_pipeline_turns_dlt_telemetry_off(self, monkeypatch: pytest.MonkeyPatch):
        """The test session already sets it, so it is removed first to prove the pipeline sets it itself."""
        monkeypatch.delenv("RUNTIME__DLTHUB_TELEMETRY", raising=False)

        structured_pipeline_definitions()

        assert os.environ["RUNTIME__DLTHUB_TELEMETRY"] == "false"
