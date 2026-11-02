"""Covers the conflicts ``create_namespace`` must answer with 409 rather than a 500 or a broken database (#1927).

The entity stores a namespace under its sanitised name, and the pipeline resolves a namespace by its folder. A name
compared raw slips past the check and hits the unique index; a folder shared by two namespaces fails the pipeline's
lookup for every file of the database.
"""

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist, NotUniqueError
from swiss_ai_hub.core.persistence.rag.datalake.entities import NamespaceEntity

from swiss_ai_hub.api.routes.knowledge.dto.create_namespace_request import CreateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "research"
BUCKET_ID = "6ab3763616f0bf3e684dd5b7"


@pytest.fixture(autouse=True)
def _no_translation() -> Iterator[None]:
    with (
        patch.object(KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock),
        patch.object(KnowledgeService, "_safe_extract_locale_string", return_value=None),
    ):
        yield


@pytest.fixture
def namespaces() -> Iterator[MagicMock]:
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
        patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
    ):
        bucket_cls.get_bucket_by_db_name.return_value = MagicMock(id=BUCKET_ID, source=None)
        namespace_cls.sanitize_namespace_name.side_effect = NamespaceEntity.sanitize_namespace_name
        namespace_cls.get_namespace_by_bucket_and_name.side_effect = DoesNotExist
        namespace_cls.get_namespace_by_bucket_and_folder.side_effect = DoesNotExist
        yield namespace_cls


async def _create(namespace: str, folder_name: str) -> None:
    await KnowledgeService.create_namespace(
        DATABASE,
        namespace,
        CreateNamespaceRequest(folder_name=folder_name),
        MagicMock(),
        MagicMock(acting_within_tenant=None),
    )


@pytest.mark.asyncio
async def test_a_name_that_collides_after_sanitising_is_a_conflict(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_name.side_effect = None
    namespaces.get_namespace_by_bucket_and_name.return_value = MagicMock(namespace_name="hr_docs")

    with pytest.raises(HTTPException) as exc_info:
        await _create("hr docs", "hr docs")

    assert exc_info.value.status_code == 409
    namespaces.get_namespace_by_bucket_and_name.assert_called_once_with(BUCKET_ID, "hr_docs")
    namespaces.create_namespace.assert_not_called()


@pytest.mark.asyncio
async def test_a_folder_already_backing_another_namespace_is_a_conflict(namespaces: MagicMock) -> None:
    namespaces.get_namespace_by_bucket_and_folder.side_effect = None
    namespaces.get_namespace_by_bucket_and_folder.return_value = MagicMock(namespace_name="reports")

    with pytest.raises(HTTPException) as exc_info:
        await _create("quarterly", "reports")

    assert exc_info.value.status_code == 409
    assert "'reports'" in exc_info.value.detail
    namespaces.get_namespace_by_bucket_and_folder.assert_called_once_with(BUCKET_ID, "reports")
    namespaces.create_namespace.assert_not_called()


@pytest.mark.asyncio
async def test_losing_a_race_on_the_unique_index_is_a_conflict(namespaces: MagicMock) -> None:
    namespaces.create_namespace.side_effect = NotUniqueError

    with pytest.raises(HTTPException) as exc_info:
        await _create("reports", "reports")

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_a_free_name_and_folder_are_created(namespaces: MagicMock) -> None:
    namespaces.create_namespace.return_value = MagicMock(
        id="6ab376716f0bf3e684dd5cc0", bucket_id=BUCKET_ID, namespace_name="reports", folder_name="reports"
    )

    await _create("reports", "reports")

    assert namespaces.create_namespace.call_args.kwargs["folder_name"] == "reports"
