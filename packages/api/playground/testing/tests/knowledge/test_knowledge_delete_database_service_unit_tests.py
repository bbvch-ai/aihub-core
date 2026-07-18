from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"
BUCKET_ID = "bucket-1"
NAMESPACE = "reports"
NAMESPACE_ID = "ns-1"


def _bucket(**overrides) -> MagicMock:
    defaults = dict(
        id=BUCKET_ID,
        bucket_name=DATABASE,
        db_name=DATABASE,
        auto_sync=False,
        ingestor=IngestorType.RAG.value,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


@pytest.fixture
def publish_mock():
    with patch.object(KnowledgeService, "_publish_teardown_event", new_callable=AsyncMock) as mock:
        yield mock


class TestDeleteDatabase:
    @pytest.mark.asyncio
    async def test_marks_bucket_and_namespaces_deleting_then_publishes_a_database_teardown(self, publish_mock):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()

            await KnowledgeService.delete_database(nc=MagicMock(), database=DATABASE)

        bucket_cls.mark_deleting.assert_called_once_with(BUCKET_ID)
        namespace_cls.mark_all_deleting_for_bucket.assert_called_once_with(BUCKET_ID)
        event = publish_mock.call_args.kwargs["event"]
        assert event.teardown_type == "database"
        assert event.bucket_id == BUCKET_ID
        assert event.db_name == DATABASE
        assert event.namespace_id is None

    @pytest.mark.asyncio
    async def test_returns_404_when_the_database_does_not_exist(self, publish_mock):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.delete_database(nc=MagicMock(), database=DATABASE)

        assert exc_info.value.status_code == 404
        bucket_cls.mark_deleting.assert_not_called()
        publish_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_refuses_to_delete_an_auto_sync_database(self, publish_mock):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(auto_sync=True)

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.delete_database(nc=MagicMock(), database=DATABASE)

        assert exc_info.value.status_code == 403
        bucket_cls.mark_deleting.assert_not_called()
        namespace_cls.mark_all_deleting_for_bucket.assert_not_called()
        publish_mock.assert_not_called()

    @pytest.mark.parametrize("legacy_ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    @pytest.mark.asyncio
    async def test_refuses_to_delete_a_legacy_database(self, publish_mock, legacy_ingestor):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(ingestor=legacy_ingestor)

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.delete_database(nc=MagicMock(), database=DATABASE)

        assert exc_info.value.status_code == 403
        bucket_cls.mark_deleting.assert_not_called()
        publish_mock.assert_not_called()


class TestDeleteNamespace:
    @pytest.mark.asyncio
    async def test_marks_only_the_namespace_deleting_then_publishes_a_namespace_teardown(self, publish_mock):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(
                id=NAMESPACE_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE
            )

            await KnowledgeService.delete_namespace(nc=MagicMock(), database=DATABASE, namespace=NAMESPACE)

        namespace_cls.mark_deleting.assert_called_once_with(NAMESPACE_ID)
        namespace_cls.mark_all_deleting_for_bucket.assert_not_called()
        bucket_cls.mark_deleting.assert_not_called()
        event = publish_mock.call_args.kwargs["event"]
        assert event.teardown_type == "namespace"
        assert event.namespace_id == NAMESPACE_ID
        assert event.namespace_name == NAMESPACE
        assert event.folder_name == NAMESPACE

    @pytest.mark.asyncio
    async def test_returns_404_when_the_namespace_does_not_exist(self, publish_mock):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespace_by_bucket_and_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.delete_namespace(nc=MagicMock(), database=DATABASE, namespace=NAMESPACE)

        assert exc_info.value.status_code == 404
        namespace_cls.mark_deleting.assert_not_called()
        publish_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_refuses_a_namespace_delete_on_an_auto_sync_database(self, publish_mock):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(auto_sync=True)

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.delete_namespace(nc=MagicMock(), database=DATABASE, namespace=NAMESPACE)

        assert exc_info.value.status_code == 403
        namespace_cls.mark_deleting.assert_not_called()
        publish_mock.assert_not_called()

    @pytest.mark.parametrize("legacy_ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    @pytest.mark.asyncio
    async def test_allows_namespace_deletion_inside_a_legacy_database(self, publish_mock, legacy_ingestor):
        """The legacy default_rag/shared_rag databases must stay, but their namespaces remain deletable."""
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(ingestor=legacy_ingestor)
            namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(
                id=NAMESPACE_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE
            )

            await KnowledgeService.delete_namespace(nc=MagicMock(), database=DATABASE, namespace=NAMESPACE)

        namespace_cls.mark_deleting.assert_called_once_with(NAMESPACE_ID)
        assert publish_mock.call_args.kwargs["event"].teardown_type == "namespace"
