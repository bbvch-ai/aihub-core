from unittest.mock import MagicMock, patch

from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_partition_manager import (
    MAX_PARTITIONS,
    get_partition_name_for_namespace,
)

from swiss_ai_hub.pipeline.services.knowledge_teardown_service import KnowledgeTeardownService

SERVICE_MODULE = "swiss_ai_hub.pipeline.services.knowledge_teardown_service"

NAMESPACE = "reports"
FOLDER = "reports"
DB_NAME = "defaultknowledge"
NAMESPACE_ID = "6501f0000000000000000001"


def _milvus_client(*, has_collection: bool = True, manual_partitions: bool = True) -> MagicMock:
    client = MagicMock()
    client.has_collection.return_value = has_collection
    partition_names = [f"partition_{index}" for index in range(MAX_PARTITIONS)] if manual_partitions else ["_default"]
    client.list_partitions.return_value = partition_names
    return client


def _teardown(milvus: MagicMock, data_lake_client: MagicMock, ref_doc: MagicMock, namespace_entity: MagicMock) -> None:
    with (
        patch(f"{SERVICE_MODULE}.build_milvus_client", return_value=milvus),
        patch(f"{SERVICE_MODULE}.ensure_connection"),
        patch(f"{SERVICE_MODULE}.RefDoc", ref_doc),
        patch(f"{SERVICE_MODULE}.NamespaceEntity", namespace_entity),
    ):
        KnowledgeTeardownService.teardown_namespace(
            namespace_id=NAMESPACE_ID,
            namespace_name=NAMESPACE,
            folder_name=FOLDER,
            db_name=DB_NAME,
            data_lake_client=data_lake_client,
        )


class TestTeardownNamespace:
    def test_purges_every_store_in_order(self) -> None:
        """S3 first: the source files are what an observation would re-enumerate, and the row goes last so a
        failed run stays flagged and is re-driven."""
        manager = MagicMock()
        milvus = _milvus_client()
        data_lake_client = MagicMock()
        ref_doc = MagicMock()
        namespace_entity = MagicMock()
        manager.attach_mock(data_lake_client.delete_directory, "delete_directory")
        manager.attach_mock(ref_doc.delete_by_namespace, "delete_by_namespace")
        manager.attach_mock(milvus.delete, "milvus_delete")
        manager.attach_mock(namespace_entity.delete_namespace, "delete_namespace")

        _teardown(milvus, data_lake_client, ref_doc, namespace_entity)

        expected = ["delete_directory", "delete_by_namespace", "milvus_delete", "delete_namespace"]
        # Only the attached names: logging the delete count also records a ``__str__`` on the mock.
        assert [call[0] for call in manager.mock_calls if call[0] in expected] == expected

    def test_deletes_the_namespace_folder_only(self) -> None:
        data_lake_client = MagicMock()

        _teardown(_milvus_client(), data_lake_client, MagicMock(), MagicMock())

        data_lake_client.delete_directory.assert_called_once_with(directory_path=FOLDER)

    def test_deletes_doc_store_rows_of_that_namespace_only(self) -> None:
        ref_doc = MagicMock()

        _teardown(_milvus_client(), MagicMock(), ref_doc, MagicMock())

        ref_doc.delete_by_namespace.assert_called_once_with(db_alias=DB_NAME, namespace=NAMESPACE)

    def test_deletes_vectors_by_filter_and_never_drops_a_partition(self) -> None:
        """Namespaces hash into shared partitions, so a partition drop would also wipe the vectors of any
        other namespace that hashed to the same one."""
        milvus = _milvus_client()

        _teardown(milvus, MagicMock(), MagicMock(), MagicMock())

        milvus.delete.assert_called_once_with(
            collection_name=DB_NAME,
            filter=f'namespace == "{NAMESPACE}"',
            partition_name=get_partition_name_for_namespace(NAMESPACE),
        )
        milvus.drop_partition.assert_not_called()
        milvus.drop_collection.assert_not_called()

    def test_loads_only_the_namespace_partition(self) -> None:
        milvus = _milvus_client()

        _teardown(milvus, MagicMock(), MagicMock(), MagicMock())

        milvus.load_partitions.assert_called_once_with(
            collection_name=DB_NAME, partition_names=[get_partition_name_for_namespace(NAMESPACE)]
        )
        milvus.load_collection.assert_not_called()

    def test_falls_back_to_the_whole_collection_without_manual_partitions(self) -> None:
        milvus = _milvus_client(manual_partitions=False)

        _teardown(milvus, MagicMock(), MagicMock(), MagicMock())

        milvus.load_collection.assert_called_once_with(collection_name=DB_NAME)
        assert milvus.delete.call_args.kwargs["partition_name"] is None

    def test_a_missing_collection_is_not_an_error(self) -> None:
        """Idempotence: a re-driven teardown finds the vectors already gone and must still remove the row."""
        milvus = _milvus_client(has_collection=False)
        namespace_entity = MagicMock()

        _teardown(milvus, MagicMock(), MagicMock(), namespace_entity)

        milvus.delete.assert_not_called()
        namespace_entity.delete_namespace.assert_called_once_with(NAMESPACE_ID)
