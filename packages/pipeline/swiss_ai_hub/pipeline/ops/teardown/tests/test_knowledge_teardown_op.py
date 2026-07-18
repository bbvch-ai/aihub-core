from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.pipeline.ops.teardown.knowledge_teardown_op import (
    KnowledgeTeardownConfig,
    _dispatch_teardown,
    _teardown_database,
    _teardown_namespace,
)

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


def _patches():
    return (
        patch(f"{_MODULE}.build_vector_store"),
        patch(f"{_MODULE}.build_s3_file_access_service"),
        patch(f"{_MODULE}.RefDoc"),
        patch(f"{_MODULE}.BucketEntity"),
        patch(f"{_MODULE}.NamespaceEntity"),
        patch(f"{_MODULE}._ensure_docstore_alias"),
    )


class TestDatabaseTeardown:
    def test_runs_every_store_step_in_order_then_deletes_the_rows_last(self):
        context = MagicMock()
        context.instance.get_dynamic_partitions.return_value = [f"{BUCKET}|uri1", f"{BUCKET}|uri2", "other|x"]
        manager = MagicMock()

        p_vs, p_s3, p_ref, p_bucket, p_ns, p_alias = _patches()
        with (
            p_vs as build_vs,
            p_s3 as build_s3,
            p_ref as ref_doc,
            p_bucket as bucket_cls,
            p_ns as namespace_cls,
            p_alias,
        ):
            vector_store = build_vs.return_value
            s3 = build_s3.return_value
            manager.attach_mock(vector_store.drop_collection, "drop_collection")
            manager.attach_mock(ref_doc.drop_database, "drop_database")
            manager.attach_mock(s3.delete_container, "delete_container")
            manager.attach_mock(namespace_cls.delete_all_for_bucket, "delete_all_for_bucket")
            manager.attach_mock(bucket_cls.delete_bucket, "delete_bucket")

            _teardown_database(context, _database_config())

        assert [c[0] for c in manager.mock_calls] == [
            "drop_collection",
            "drop_database",
            "delete_container",
            "delete_all_for_bucket",
            "delete_bucket",
        ]
        build_vs.assert_called_once_with(DB)
        ref_doc.drop_database.assert_called_once_with(DB)
        s3.delete_container.assert_called_once_with(BUCKET)
        namespace_cls.delete_all_for_bucket.assert_called_once_with(BUCKET_ID)
        bucket_cls.delete_bucket.assert_called_once_with(BUCKET_ID)

    def test_purges_only_this_buckets_orphaned_partition_keys(self):
        context = MagicMock()
        context.instance.get_dynamic_partitions.return_value = [f"{BUCKET}|uri1", f"{BUCKET}|uri2", "other|x"]

        p_vs, p_s3, p_ref, p_bucket, p_ns, p_alias = _patches()
        with p_vs, p_s3, p_ref, p_bucket, p_ns, p_alias:
            _teardown_database(context, _database_config())

        deleted = {c.kwargs["partition_key"] for c in context.instance.delete_dynamic_partition.call_args_list}
        assert deleted == {f"{BUCKET}|uri1", f"{BUCKET}|uri2"}
        assert all(
            c.kwargs["partitions_def_name"] == REGISTRY
            for c in context.instance.delete_dynamic_partition.call_args_list
        )


class TestNamespaceTeardown:
    def test_runs_steps_in_order_and_never_touches_the_collection_or_bucket(self):
        context = MagicMock()
        manager = MagicMock()

        p_vs, p_s3, p_ref, p_bucket, p_ns, p_alias = _patches()
        with (
            p_vs as build_vs,
            p_s3 as build_s3,
            p_ref as ref_doc,
            p_bucket as bucket_cls,
            p_ns as namespace_cls,
            p_alias,
        ):
            vector_store = build_vs.return_value
            s3 = build_s3.return_value
            manager.attach_mock(s3.delete_prefix, "delete_prefix")
            manager.attach_mock(ref_doc.delete_by_namespace, "ref_delete_by_namespace")
            manager.attach_mock(vector_store.delete_by_namespace, "vector_delete_by_namespace")
            manager.attach_mock(namespace_cls.delete_namespace, "delete_namespace")

            _teardown_namespace(context, _namespace_config())

            assert [c[0] for c in manager.mock_calls] == [
                "delete_prefix",
                "ref_delete_by_namespace",
                "vector_delete_by_namespace",
                "delete_namespace",
            ]
            s3.delete_prefix.assert_called_once_with(BUCKET, "reports/")
            ref_doc.delete_by_namespace.assert_called_once_with(DB, "reports")
            vector_store.delete_by_namespace.assert_called_once_with("reports")
            namespace_cls.delete_namespace.assert_called_once_with("ns1")
            vector_store.drop_collection.assert_not_called()
            bucket_cls.delete_bucket.assert_not_called()
            context.instance.delete_dynamic_partition.assert_not_called()


class TestDispatch:
    def test_rejects_an_unknown_teardown_type(self):
        config = KnowledgeTeardownConfig(
            teardown_type="galaxy",
            bucket_id=BUCKET_ID,
            bucket_name=BUCKET,
            db_name=DB,
            partition_registry_name=REGISTRY,
        )
        with pytest.raises(ValueError, match="Unknown teardown_type"):
            _dispatch_teardown(MagicMock(), config)
