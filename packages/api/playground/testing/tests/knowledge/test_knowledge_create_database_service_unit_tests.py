from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist, NotUniqueError
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence.rag.datalake.entities import Ingestor, IngestorType

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"


@pytest.fixture(autouse=True)
def _no_registered_custom_ingestors():
    """The entity is Mongo-backed; stub it so these unit tests need no database."""
    with patch(f"{_SERVICE_MODULE}.IngestorEntity") as ingestor_entity:
        ingestor_entity.custom.return_value = []
        ingestor_entity.is_selectable.side_effect = lambda ingestor_id: ingestor_id == IngestorType.RAG.value
        yield ingestor_entity


def _user() -> MagicMock:
    """Sysadmin-shaped identity: no tenant context, so the create-time grant is skipped."""
    user = MagicMock()
    user.acting_within_tenant = None
    return user


def _custom_ingestor() -> Ingestor:
    return Ingestor(
        id="acme_rag",
        display_name=LocaleString(en="Acme RAG"),
        description=LocaleString(en="Acme's custom ingestion pipeline"),
    )


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
                _user(),
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
                    _user(),
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
                    DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, _user(), llm_config=None
                )

        assert exc_info.value.status_code == 409
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()

    @pytest.mark.asyncio
    async def test_rolls_back_the_container_and_entity_when_storage_provisioning_fails(
        self, locale_handler, s3_service
    ):
        """A partially-provisioned container and its row must never outlive a failed create."""
        created_bucket = MagicMock(id="abc123")
        s3_service.ensure_bucket_with_cors.side_effect = RuntimeError("s3 down")

        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = created_bucket

            with pytest.raises(RuntimeError):
                await KnowledgeService.create_database(
                    DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, _user(), llm_config=None
                )

            s3_service.delete_container.assert_called_once_with(DATABASE)
            bucket_cls.delete_bucket.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_concurrent_create_loses_the_unique_index_race_with_409(self, locale_handler, s3_service):
        """Two admins passing the existence check before either saves: the unique index serialises them,
        and the loser must get a 409 without ever provisioning storage."""
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.side_effect = NotUniqueError

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, _user(), llm_config=None
                )

        assert exc_info.value.status_code == 409
        s3_service.ensure_bucket_with_cors.assert_not_called()
        bucket_cls.delete_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_accepts_a_custom_ingestor_registered_by_a_deployment(
        self, locale_handler, s3_service, _no_registered_custom_ingestors
    ):
        """A pipeline that registered itself in the DB is selectable, so create_database must accept it."""
        _no_registered_custom_ingestors.is_selectable.side_effect = lambda ingestor_id: ingestor_id == "acme_rag"
        created_bucket = MagicMock(db_name="acmedb", bucket_name="acmedb", ingestor="acme_rag")

        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = created_bucket

            await KnowledgeService.create_database(
                "acmedb",
                CreateDatabaseRequest(ingestor="acme_rag"),
                locale_handler,
                s3_service,
                _user(),
                llm_config=None,
            )

        assert bucket_cls.create_bucket.call_args.kwargs["ingestor"] == "acme_rag"

    @pytest.mark.asyncio
    async def test_rejects_an_unregistered_ingestor(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE,
                    CreateDatabaseRequest(ingestor="never_registered"),
                    locale_handler,
                    s3_service,
                    _user(),
                    None,
                )

        assert exc_info.value.status_code == 400
        bucket_cls.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_name_taken_by_an_existing_storage_container(self, locale_handler, s3_service):
        """Platform buckets (``dagster``, ``milvus``, …) have no BucketEntity row, so the entity duplicate
        check alone would bind a knowledge database — and the RAG pipeline — onto their contents."""
        s3_service.container_exists.return_value = True

        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    "dagster", CreateDatabaseRequest(), locale_handler, s3_service, _user(), llm_config=None
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

    def test_appends_registered_custom_ingestors_with_their_own_labels(self, _no_registered_custom_ingestors):
        _no_registered_custom_ingestors.custom.return_value = [_custom_ingestor()]
        t = ApiLocaleHandler("en")

        ingestors = KnowledgeService.get_ingestors(t)

        assert [ingestor.name for ingestor in ingestors] == [IngestorType.RAG.value, "acme_rag"]
        custom = ingestors[-1]
        assert custom.display_name == "Acme RAG"
        assert custom.description == "Acme's custom ingestion pipeline"


def _tenant_user() -> MagicMock:
    """Identity acting inside a tenant, so the create-time grant runs."""
    user = MagicMock(id="user-1")
    user.acting_within_tenant = MagicMock(id="tenant-1", access_rules=[])
    return user


class TestCreateGrantsAccess:
    @pytest.mark.asyncio
    async def test_grants_the_creator_and_the_tenant_admin_on_the_new_database(self, locale_handler, s3_service):
        """Without this the creator cannot see the database they just made: only a holder of the global
        ``aihub.admin.knowledge.>`` wildcard could."""
        user = _tenant_user()
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.UserTenantRoleEntity") as user_role_cls,
            patch(f"{_SERVICE_MODULE}.RoleEntity") as role_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = MagicMock(
                db_name=DATABASE, bucket_name=DATABASE, id="abc123", ingestor=IngestorType.RAG.value
            )
            role_cls.objects.return_value.first.return_value = None

            await KnowledgeService.create_database(
                DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, user, llm_config=None
            )

        tenant_cls.grant_access_rule.assert_called_once_with("tenant-1", f"aihub.admin.knowledge.{DATABASE}")
        role_cls.create_tenant_role.assert_called_once()
        assert role_cls.create_tenant_role.call_args.kwargs["access_rules"] == [f"aihub.admin.knowledge.{DATABASE}"]
        user_role_cls.add_roles.assert_called_once_with("user-1", "tenant-1", ["KnowledgeResearchdocsAdmin"])

    @pytest.mark.asyncio
    async def test_skips_the_tenant_rule_when_a_broader_one_already_covers_it(self, locale_handler, s3_service):
        user = _tenant_user()
        user.acting_within_tenant.access_rules = ["aihub.admin.knowledge.>"]
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.UserTenantRoleEntity"),
            patch(f"{_SERVICE_MODULE}.RoleEntity") as role_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = MagicMock(
                db_name=DATABASE, bucket_name=DATABASE, id="abc123", ingestor=IngestorType.RAG.value
            )
            role_cls.objects.return_value.first.return_value = None

            await KnowledgeService.create_database(
                DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, user, llm_config=None
            )

        tenant_cls.grant_access_rule.assert_not_called()

    @pytest.mark.asyncio
    async def test_rolls_back_the_whole_creation_when_the_grant_fails(self, locale_handler, s3_service):
        """A database nobody can administer is worse than no database, so the provisioning is undone."""
        user = _tenant_user()
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.UserTenantRoleEntity"),
            patch(f"{_SERVICE_MODULE}.RoleEntity") as role_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = MagicMock(
                db_name=DATABASE, bucket_name=DATABASE, id="abc123", ingestor=IngestorType.RAG.value
            )
            role_cls.objects.return_value.first.return_value = None
            tenant_cls.grant_access_rule.side_effect = RuntimeError("tenant store unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, user, llm_config=None
                )

        assert exc_info.value.status_code == 500
        s3_service.delete_container.assert_called_once_with(DATABASE)
        bucket_cls.delete_bucket.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_a_sysadmin_without_tenant_context_creates_without_a_grant(self, locale_handler, s3_service):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.UserTenantRoleEntity") as user_role_cls,
            patch.object(
                KnowledgeService, "_create_and_translate_locale_entity", new_callable=AsyncMock, return_value=None
            ),
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = MagicMock(
                db_name=DATABASE, bucket_name=DATABASE, id="abc123", ingestor=IngestorType.RAG.value
            )

            await KnowledgeService.create_database(
                DATABASE, CreateDatabaseRequest(), locale_handler, s3_service, _user(), llm_config=None
            )

        tenant_cls.grant_access_rule.assert_not_called()
        user_role_cls.add_roles.assert_not_called()
