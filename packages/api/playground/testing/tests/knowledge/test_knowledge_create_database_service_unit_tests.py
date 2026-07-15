from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"


@pytest.fixture
def locale_handler():
    t = MagicMock()
    t.locale = "en"
    t.extract.return_value = "Research Docs"
    return t


@pytest.fixture
def s3_service():
    service = MagicMock()
    service.container_exists.return_value = False
    return service


class TestCreateDatabase:
    @pytest.mark.asyncio
    async def test_creates_bucket_with_rag_ingestor(self, locale_handler, s3_service):
        created_bucket = MagicMock(db_name=DATABASE, bucket_name=DATABASE, ingestor=IngestorType.RAG.value)
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = created_bucket

            response = await KnowledgeService.create_database(
                DATABASE,
                CreateDatabaseRequest(display_name="Research Docs"),
                locale_handler,
                s3_service,
                llm_config=None,
            )

        s3_service.ensure_bucket_with_cors.assert_called_once_with(DATABASE)
        bucket_cls.create_bucket.assert_called_once()
        assert bucket_cls.create_bucket.call_args.kwargs["ingestor"] == IngestorType.RAG.value
        assert bucket_cls.create_bucket.call_args.kwargs["bucket_name"] == DATABASE
        assert response.name == DATABASE
        assert response.ingestor == IngestorType.RAG.value

    @pytest.mark.asyncio
    async def test_rejects_ingestor_that_is_not_self_service_selectable(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE,
                    CreateDatabaseRequest(ingestor=IngestorType.DEFAULT_RAG),
                    locale_handler,
                    s3_service,
                    llm_config=None,
                )

        assert exc_info.value.status_code == 400
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_database(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.return_value = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, llm_config=None
                )

        assert exc_info.value.status_code == 409
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_name_taken_by_an_existing_storage_container(self, locale_handler, s3_service):
        """Platform buckets (``dagster``, ``milvus``, …) have no BucketEntity row, so the entity duplicate
        check alone would bind a knowledge database — and the RAG pipeline — onto their contents."""
        s3_service.container_exists.return_value = True

        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    "dagster", CreateDatabaseRequest(), locale_handler, s3_service, llm_config=None
                )

        assert exc_info.value.status_code == 409
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()


class TestGetIngestors:
    def test_offers_only_self_service_ingestors_with_localized_labels(self):
        t = ApiLocaleHandler("en")

        ingestors = KnowledgeService.get_ingestors(t)

        assert [ingestor.name for ingestor in ingestors] == [IngestorType.RAG.value]
        assert ingestors[0].display_name == "RAG Pipeline"
        assert ingestors[0].description
