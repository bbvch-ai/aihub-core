from unittest.mock import MagicMock, patch

from swiss_ai_hub.pipeline.services.knowledge_teardown_service import KnowledgeTeardownService

_MODULE = "swiss_ai_hub.pipeline.services.knowledge_teardown_service"

DB = "researchdocs"
BUCKET = "researchdocs"
BUCKET_ID = "b1"


def _patches():
    return (
        patch(f"{_MODULE}.build_vector_store"),
        patch(f"{_MODULE}.build_s3_file_access_service"),
        patch(f"{_MODULE}.RefDoc"),
        patch(f"{_MODULE}.BucketEntity"),
        patch(f"{_MODULE}.NamespaceEntity"),
        patch(f"{_MODULE}.MongoConnectionRegistry"),
    )


class TestDatabaseTeardown:
    def test_runs_every_store_step_in_order_then_deletes_the_rows_last(self):
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

            KnowledgeTeardownService.teardown_database(bucket_id=BUCKET_ID, bucket_name=BUCKET, db_name=DB)

        assert [call[0] for call in manager.mock_calls] == [
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


class TestNamespaceTeardown:
    def test_runs_steps_in_order_and_never_touches_the_collection_or_bucket(self):
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

            KnowledgeTeardownService.teardown_namespace(
                namespace_id="ns1",
                namespace_name="reports",
                folder_name="reports",
                bucket_name=BUCKET,
                db_name=DB,
            )

            assert [call[0] for call in manager.mock_calls] == [
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
