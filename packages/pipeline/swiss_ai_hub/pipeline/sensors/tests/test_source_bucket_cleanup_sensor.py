from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterInstance, build_sensor_context
from mongoengine import DoesNotExist

from swiss_ai_hub.pipeline.sensors.source_bucket_cleanup_sensor import source_bucket_cleanup_sensor

_MODULE = "swiss_ai_hub.pipeline.sensors.source_bucket_cleanup_sensor"
_REGISTRY = "rclone_source_partitions"


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral:
        yield ephemeral


def _lookup(rows: dict[str, MagicMock]):
    def get(bucket_name: str) -> MagicMock:
        if bucket_name not in rows:
            raise DoesNotExist()
        return rows[bucket_name]

    return get


class TestCleanup:
    def test_databases_that_left_the_source_lose_their_partitions_and_remote_and_live_ones_keep_them(self, instance):
        instance.add_dynamic_partitions(
            _REGISTRY, ["live|a.pdf", "live|b.pdf", "gone|a.pdf", "switched|a.pdf", "deleting|a.pdf"]
        )
        rows = {
            "live": MagicMock(source="rclone", deleting=False),
            "switched": MagicMock(source="acme_sync", deleting=False),
            "deleting": MagicMock(source="rclone", deleting=True),
        }
        client = MagicMock()
        sensor = source_bucket_cleanup_sensor(source="rclone", partition_registry_name=_REGISTRY)

        with (
            patch(f"{_MODULE}.ensure_main_db_connection"),
            patch(f"{_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_MODULE}.build_rclone_client", return_value=client),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = _lookup(rows)
            result = sensor.evaluate_tick(build_sensor_context(instance=instance))

        assert set(instance.get_dynamic_partitions(_REGISTRY)) == {"live|a.pdf", "live|b.pdf"}
        assert sorted(call.args[0] for call in client.delete_remote.call_args_list) == [
            "rclone_deleting",
            "rclone_gone",
            "rclone_switched",
        ]
        assert "3 stale" in str(result.skip_message)
