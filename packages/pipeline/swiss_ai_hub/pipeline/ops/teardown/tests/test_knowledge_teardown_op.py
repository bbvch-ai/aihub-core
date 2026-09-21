from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from dagster import DagsterInstance, build_op_context

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import KnowledgeTeardownConfig, knowledge_teardown_op

_MODULE = "swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op"

DB = "researchdocs"
BUCKET = "researchdocs"
BUCKET_ID = "b1"
REGISTRY = "rag_document_partitions"


def _database_config() -> KnowledgeTeardownConfig:
    return KnowledgeTeardownConfig(
        teardown_type="database",
        bucket_id=BUCKET_ID,
        bucket_name=BUCKET,
        db_name=DB,
        partition_registry_name=REGISTRY,
    )


def _namespace_config() -> KnowledgeTeardownConfig:
    return KnowledgeTeardownConfig(
        teardown_type="namespace",
        bucket_id=BUCKET_ID,
        bucket_name=BUCKET,
        db_name=DB,
        partition_registry_name=REGISTRY,
        namespace_id="ns1",
        namespace_name="reports",
        folder_name="reports",
    )


@pytest.fixture
def instance() -> Iterator[DagsterInstance]:
    with DagsterInstance.ephemeral() as ephemeral_instance:
        yield ephemeral_instance


def _run(config: KnowledgeTeardownConfig, instance: DagsterInstance) -> MagicMock:
    with (
        patch(f"{_MODULE}.ensure_main_db_connection"),
        patch(f"{_MODULE}.KnowledgeTeardownService") as service,
    ):
        knowledge_teardown_op(build_op_context(instance=instance), config)
    return service


class TestDatabaseTeardown:
    def test_delegates_to_the_service_and_purges_only_this_buckets_partition_keys(self, instance: DagsterInstance):
        instance.add_dynamic_partitions(REGISTRY, [f"{BUCKET}|uri1", f"{BUCKET}|uri2", "other|x"])

        service = _run(_database_config(), instance)

        service.teardown_database.assert_called_once_with(bucket_id=BUCKET_ID, bucket_name=BUCKET, db_name=DB)
        assert instance.get_dynamic_partitions(REGISTRY) == ["other|x"]


class TestNamespaceTeardown:
    def test_delegates_to_the_service_and_leaves_the_partition_registry_alone(self, instance: DagsterInstance):
        instance.add_dynamic_partitions(REGISTRY, [f"{BUCKET}|uri1"])

        service = _run(_namespace_config(), instance)

        service.teardown_namespace.assert_called_once_with(
            namespace_id="ns1", namespace_name="reports", folder_name="reports", bucket_name=BUCKET, db_name=DB
        )
        service.teardown_database.assert_not_called()
        assert instance.get_dynamic_partitions(REGISTRY) == [f"{BUCKET}|uri1"]


class TestDispatch:
    def test_rejects_an_unknown_teardown_type(self, instance: DagsterInstance):
        config = KnowledgeTeardownConfig(
            teardown_type="galaxy",
            bucket_id=BUCKET_ID,
            bucket_name=BUCKET,
            db_name=DB,
            partition_registry_name=REGISTRY,
        )
        with pytest.raises(ValueError, match="Unknown teardown_type"):
            _run(config, instance)
