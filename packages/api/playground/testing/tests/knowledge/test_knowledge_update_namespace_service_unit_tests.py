"""Covers how ``update_namespace`` finds the folder it writes to.

The route guard authorises ``aihub.admin.knowledge.{database}.{namespace}`` from the path, so the service must
resolve that same pair by name. It once took the path value as an ObjectId, which only the knowledge wildcard
could ever authorise and which ignored ``database`` entirely (aihub-core-private#290).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

from swiss_ai_hub.api.routes.knowledge.dto.update_namespace_request import UpdateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "research"
NAMESPACE = "reports"
BUCKET_ID = "6ab3763616f0bf3e684dd5b7"
NAMESPACE_ID = "6ab376716f0bf3e684dd5cc0"

REQUEST = UpdateNamespaceRequest(display_name="Quarterly reports", description="Finance only")


def _updated_namespace() -> MagicMock:
    return MagicMock(id=NAMESPACE_ID, bucket_id=BUCKET_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE)


async def _update() -> None:
    await KnowledgeService.update_namespace(
        database=DATABASE, namespace=NAMESPACE, request=REQUEST, t=MagicMock(), user=MagicMock()
    )


@pytest.fixture(autouse=True)
def _no_translation():
    with (
        patch.object(KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock),
        patch.object(KnowledgeService, "_safe_extract_locale_string", return_value=None),
    ):
        yield


@pytest.mark.asyncio
async def test_resolves_the_folder_by_database_and_folder_name():
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
    ):
        bucket_cls.get_bucket_by_db_name.return_value = MagicMock(id=BUCKET_ID)
        namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(id=NAMESPACE_ID)
        namespace_cls.update_namespace.return_value = _updated_namespace()

        await _update()

    bucket_cls.get_bucket_by_db_name.assert_called_once_with(DATABASE)
    namespace_cls.get_namespace_by_bucket_and_name.assert_called_once_with(BUCKET_ID, NAMESPACE)
    namespace_cls.get_namespace_by_id.assert_not_called()
    assert namespace_cls.update_namespace.call_args.kwargs["namespace_id"] == NAMESPACE_ID


@pytest.mark.asyncio
async def test_returns_404_when_the_database_does_not_exist():
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
    ):
        bucket_cls.get_bucket_by_db_name.side_effect = DoesNotExist

        with pytest.raises(HTTPException) as exc_info:
            await _update()

    assert exc_info.value.status_code == 404
    namespace_cls.update_namespace.assert_not_called()


@pytest.mark.asyncio
async def test_returns_404_when_the_folder_is_not_in_that_database():
    """The lookup is bucket-scoped, so a folder of the same name elsewhere is never the one written."""
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
    ):
        bucket_cls.get_bucket_by_db_name.return_value = MagicMock(id=BUCKET_ID)
        namespace_cls.get_namespace_by_bucket_and_name.side_effect = DoesNotExist

        with pytest.raises(HTTPException) as exc_info:
            await _update()

    assert exc_info.value.status_code == 404
    namespace_cls.update_namespace.assert_not_called()
