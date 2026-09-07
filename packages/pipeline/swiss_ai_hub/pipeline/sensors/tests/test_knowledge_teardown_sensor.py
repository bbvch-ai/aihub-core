from unittest.mock import MagicMock, patch

from dagster import DagsterInstance, RunRequest, SkipReason, build_sensor_context
from mongoengine import DoesNotExist

from swiss_ai_hub.pipeline.jobs.knowledge_teardown_job import knowledge_teardown_job
from swiss_ai_hub.pipeline.sensors.knowledge_teardown_sensor import TEARDOWN_TARGET_TAG, knowledge_teardown_sensor

SENSOR_MODULE = "swiss_ai_hub.pipeline.sensors.knowledge_teardown_sensor"

CONTAINER = "defaultknowledge"
BUCKET_ID = "6501f0000000000000000000"
NAMESPACE_ID = "6501f0000000000000000001"

TEARDOWN_JOB = knowledge_teardown_job(source_location_name=CONTAINER)


def _bucket() -> MagicMock:
    bucket = MagicMock()
    bucket.id = BUCKET_ID
    bucket.bucket_name = CONTAINER
    bucket.db_name = CONTAINER
    return bucket


def _namespace(namespace_id: str, *, deleting: bool, name: str = "reports") -> MagicMock:
    namespace = MagicMock()
    namespace.id = namespace_id
    namespace.namespace_name = name
    namespace.folder_name = name
    namespace.deleting = deleting
    return namespace


def _evaluate(instance: DagsterInstance, namespaces: list[MagicMock], bucket: MagicMock | None = None) -> list:
    bucket_entity = MagicMock()
    if bucket is None:
        bucket_entity.get_bucket_by_bucket_name.side_effect = DoesNotExist
    else:
        bucket_entity.get_bucket_by_bucket_name.return_value = bucket
    namespace_entity = MagicMock()
    namespace_entity.get_namespaces_by_bucket.return_value = namespaces

    sensor = knowledge_teardown_sensor(TEARDOWN_JOB, datalake_container_name=CONTAINER)
    with (
        patch(f"{SENSOR_MODULE}.ensure_main_db_connection"),
        patch(f"{SENSOR_MODULE}.BucketEntity", bucket_entity),
        patch(f"{SENSOR_MODULE}.NamespaceEntity", namespace_entity),
    ):
        return list(sensor(build_sensor_context(instance=instance)))


def _create_run(instance: DagsterInstance, target_id: str):
    return instance.create_run_for_job(
        TEARDOWN_JOB,
        tags={TEARDOWN_TARGET_TAG: target_id},
        run_config={
            "ops": {
                "knowledge_teardown_op": {
                    "config": {
                        "namespace_id": target_id,
                        "namespace_name": "reports",
                        "folder_name": "reports",
                        "db_name": CONTAINER,
                    }
                }
            }
        },
    )


class TestKnowledgeTeardownSensor:
    def test_requests_a_run_for_a_flagged_namespace(self) -> None:
        results = _evaluate(DagsterInstance.ephemeral(), [_namespace(NAMESPACE_ID, deleting=True)], _bucket())

        assert len(results) == 1
        request = results[0]
        assert isinstance(request, RunRequest)
        assert request.run_key == f"teardown_{NAMESPACE_ID}_0"
        config = request.run_config["ops"]["knowledge_teardown_op"]["config"]
        assert config["namespace_id"] == NAMESPACE_ID
        assert config["namespace_name"] == "reports"
        assert config["folder_name"] == "reports"
        assert config["db_name"] == CONTAINER

    def test_ignores_a_namespace_that_is_not_flagged(self) -> None:
        results = _evaluate(DagsterInstance.ephemeral(), [_namespace(NAMESPACE_ID, deleting=False)], _bucket())

        assert [isinstance(result, SkipReason) for result in results] == [True]

    def test_requests_one_run_per_flagged_namespace(self) -> None:
        namespaces = [
            _namespace(NAMESPACE_ID, deleting=True, name="reports"),
            _namespace("6501f0000000000000000002", deleting=True, name="minutes"),
            _namespace("6501f0000000000000000003", deleting=False, name="policies"),
        ]

        results = _evaluate(DagsterInstance.ephemeral(), namespaces, _bucket())

        assert {result.run_key for result in results} == {
            f"teardown_{NAMESPACE_ID}_0",
            "teardown_6501f0000000000000000002_0",
        }

    def test_skips_when_the_bucket_has_no_metadata_row(self) -> None:
        results = _evaluate(DagsterInstance.ephemeral(), [], bucket=None)

        assert [isinstance(result, SkipReason) for result in results] == [True]

    def test_does_not_re_request_while_an_attempt_is_pending(self) -> None:
        instance = DagsterInstance.ephemeral()
        _create_run(instance, NAMESPACE_ID)

        results = _evaluate(instance, [_namespace(NAMESPACE_ID, deleting=True)], _bucket())

        assert [isinstance(result, SkipReason) for result in results] == [True]

    def test_re_drives_a_failed_attempt_under_a_new_run_key(self) -> None:
        """Dagster deduplicates run keys forever, so a key derived from the id alone would make a failed
        teardown unretryable."""
        instance = DagsterInstance.ephemeral()
        instance.report_run_failed(_create_run(instance, NAMESPACE_ID))

        results = _evaluate(instance, [_namespace(NAMESPACE_ID, deleting=True)], _bucket())

        assert [result.run_key for result in results] == [f"teardown_{NAMESPACE_ID}_1"]
