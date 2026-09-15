from dagster import AssetKey, AssetSelection, DataVersion, observable_source_asset
from dagster._core.storage.tags import PRIORITY_TAG

from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job, observe_source_job


@observable_source_asset(name="a_source")
def _source() -> DataVersion:
    return DataVersion("v1")


class TestOrchestrationRunPriority:
    """The queue is priority-ordered but every run defaults to 0, so without an explicit tag these
    jobs land behind every per-document ingestion run a bulk upload queues."""

    def test_observation_runs_outrank_the_default(self) -> None:
        job = observe_source_job(observable_asset=_source, source_location_name="bucket")

        assert int(job.run_tags[PRIORITY_TAG]) > 0

    def test_removal_runs_outrank_the_default(self) -> None:
        job = materialize_asset_job(
            source_location_name="bucket",
            job_name="remove_documents",
            asset_selection=AssetSelection.keys(AssetKey(["removed"])),
        )

        assert int(job.run_tags[PRIORITY_TAG]) > 0
