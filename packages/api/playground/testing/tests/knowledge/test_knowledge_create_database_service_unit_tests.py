from typing import Annotated, Self
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist, NotUniqueError
from pydantic import Field
from swiss_ai_hub.core.form import Checkbox, Form, ModelSelect
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.ingestors import IngestorConfig
from swiss_ai_hub.core.persistence import ConfigSpecsEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import Ingestor, IngestorType

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService
from swiss_ai_hub.api.util.config_authorization_service import ConfigAuthorizationService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"


class _RagConfig(IngestorConfig):
    """The shape the shipped pipeline announces: identity fields plus a model picker and a flag."""

    embedding_model: Annotated[str | ModelSelect, Field(description="Embedding model")]
    with_summaries: Annotated[bool | Checkbox | None, Field(description="Summaries")] = None

    @classmethod
    def as_form(cls) -> Self:
        base = IngestorConfig.as_form()
        return cls(
            name=base.name,
            description=base.description,
            embedding_model=ModelSelect(
                label=LocaleString(en="Embedding"), mode="embedding", value="embedding/default"
            ),
            with_summaries=Checkbox(label=LocaleString(en="Summaries"), value=True),
        )


class _CrawlConfig(IngestorConfig):
    """A second, differently shaped ingestor."""

    crawl_depth: Annotated[int, Field(description="Depth")] = 2
    llm_model: Annotated[str | ModelSelect, Field(description="Text model")]

    @classmethod
    def as_form(cls) -> Self:
        base = IngestorConfig.as_form()
        return cls(
            name=base.name,
            description=base.description,
            llm_model=ModelSelect(label=LocaleString(en="Text"), mode="chat"),
        )


class _EnrichmentConfig(Form):
    model: Annotated[str | ModelSelect, Field(description="Enrichment model")]


class _SourceConfig(Form):
    model: Annotated[str | ModelSelect, Field(description="Per-source embedding model")]


class _NestedConfig(IngestorConfig):
    """Model pickers inside a group and a repeater, as a pipeline with structured knobs would declare them."""

    enrichment: Annotated[_EnrichmentConfig, Field(description="Enrichment")]
    sources: Annotated[list[_SourceConfig], Field(description="Sources")]

    @classmethod
    def as_form(cls) -> Self:
        base = IngestorConfig.as_form()
        return cls(
            name=base.name,
            description=base.description,
            enrichment=_EnrichmentConfig(model=ModelSelect(label=LocaleString(en="Model"), mode="chat")),
            sources=[_SourceConfig(model=ModelSelect(label=LocaleString(en="Embedding"), mode="embedding"))],
        )


def _ingestor(ingestor_id: str, config: IngestorConfig) -> Ingestor:
    return Ingestor.from_config(ingestor_id, LocaleString(en=ingestor_id), LocaleString(en="pipeline"), config)


def _registered(ingestor: Ingestor) -> MagicMock:
    """An ``IngestorEntity`` row as ``IngestorEntity.find`` returns it."""
    entity = MagicMock()
    entity.form = [element.model_dump() for element in ingestor.form]
    entity.form_elements = ingestor.form
    entity.config_specs = ConfigSpecsEntity.from_specs(ingestor.config_specs)
    entity.to_ingestor.return_value = ingestor
    return entity


RAG = _ingestor(IngestorType.DOCUMENT_INGESTION.value, _RagConfig.as_form())
CRAWLER = _ingestor("crawler", _CrawlConfig.as_form())
NESTED = _ingestor("nested", _NestedConfig.as_form())


@pytest.fixture(autouse=True)
def registered_ingestors():
    """The entity is Mongo-backed; stub it with two differently shaped ingestors so these tests need no database."""
    labels_only = MagicMock(form=[], config_specs=None)
    rows = {
        RAG.id: _registered(RAG),
        CRAWLER.id: _registered(CRAWLER),
        NESTED.id: _registered(NESTED),
        "stale": labels_only,
    }
    with patch(f"{_SERVICE_MODULE}.IngestorEntity") as ingestor_entity:
        ingestor_entity.find.side_effect = lambda ingestor_id: rows.get(ingestor_id)
        ingestor_entity.all.return_value = [RAG, CRAWLER]
        yield ingestor_entity


@pytest.fixture(autouse=True)
def _no_keycloak():
    with patch(f"{_SERVICE_MODULE}.ConfigAuthorizationService.validate_for_user_or_raise", new_callable=AsyncMock):
        yield


@pytest.fixture(autouse=True)
def models():
    """LiteLLM as ``ModelService`` serves it: one chat and one embedding model."""
    chat = MagicMock(model_info=MagicMock(mode="chat", output_vector_size=None))
    embedding = MagicMock(model_info=MagicMock(mode="embedding", output_vector_size=1024))
    by_name = {"text-generation/pick": chat, "embedding/default": embedding, "embedding/pick": embedding}
    with patch(f"{_SERVICE_MODULE}.ModelService.get_model_by_name", new_callable=AsyncMock) as get_model:
        get_model.side_effect = lambda user, name: by_name[name]
        yield get_model


def _user() -> MagicMock:
    """Sysadmin-shaped identity: no tenant context, so the create-time grant is skipped."""
    user = MagicMock()
    user.acting_within_tenant = None
    return user


def _rag_request(**overrides) -> CreateDatabaseRequest:
    configuration = {
        "name": {"en": "Research Docs"},
        "description": {"en": "Papers"},
        "embedding_model": "embedding/default",
        **overrides,
    }
    return CreateDatabaseRequest(ingestor=RAG.id, configuration=configuration)


def _created_bucket(
    configuration: dict | None = None, ingestor: str = IngestorType.DOCUMENT_INGESTION.value
) -> MagicMock:
    return MagicMock(
        db_name=DATABASE, bucket_name=DATABASE, id="abc123", ingestor=ingestor, configuration=configuration or {}
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
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()

            response = await KnowledgeService.create_database(
                DATABASE, _rag_request(), locale_handler, s3_service, _user()
            )

        s3_service.ensure_bucket_with_cors.assert_called_once_with(DATABASE)
        bucket_cls.create_bucket.assert_called_once()
        assert bucket_cls.create_bucket.call_args.kwargs["ingestor"] == IngestorType.DOCUMENT_INGESTION.value
        assert bucket_cls.create_bucket.call_args.kwargs["bucket_name"] == DATABASE
        assert response.name == DATABASE
        assert response.ingestor == IngestorType.DOCUMENT_INGESTION.value

    @pytest.mark.asyncio
    async def test_rejects_an_unregistered_ingestor(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, CreateDatabaseRequest(ingestor="never_registered"), locale_handler, s3_service, _user()
                )

        assert exc_info.value.status_code == 400
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_duplicate_database(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.return_value = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, _user())

        assert exc_info.value.status_code == 409
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()

    @pytest.mark.asyncio
    async def test_rolls_back_the_container_and_entity_when_storage_provisioning_fails(
        self, locale_handler, s3_service
    ):
        """A partially-provisioned container and its row must never outlive a failed create."""
        s3_service.ensure_bucket_with_cors.side_effect = RuntimeError("s3 down")

        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()

            with pytest.raises(RuntimeError):
                await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, _user())

            s3_service.delete_container.assert_called_once_with(DATABASE)
            bucket_cls.delete_bucket.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_concurrent_create_loses_the_unique_index_race_with_409(self, locale_handler, s3_service):
        """Two admins passing the existence check before either saves: the unique index serialises them,
        and the loser must get a 409 without ever provisioning storage."""
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.side_effect = NotUniqueError

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, _user())

        assert exc_info.value.status_code == 409
        s3_service.ensure_bucket_with_cors.assert_not_called()
        bucket_cls.delete_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_name_taken_by_an_existing_storage_container(self, locale_handler, s3_service):
        """Platform buckets (``dagster``, ``milvus``, …) have no BucketEntity row, so the entity duplicate
        check alone would bind a knowledge database — and the document ingestion pipeline — onto their contents."""
        s3_service.container_exists.return_value = True

        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database("dagster", _rag_request(), locale_handler, s3_service, _user())

        assert exc_info.value.status_code == 409
        bucket_cls.create_bucket.assert_not_called()
        s3_service.ensure_bucket_with_cors.assert_not_called()


class TestAnnouncedConfiguration:
    """The database's configuration is validated against the form its ingestor announced, like an agent instance."""

    @pytest.mark.asyncio
    async def test_identity_fields_land_on_the_row_and_the_knobs_in_the_configuration(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket({"embedding_model": "embedding/default"})

            response = await KnowledgeService.create_database(
                DATABASE, _rag_request(with_summaries=False), locale_handler, s3_service, _user()
            )

        kwargs = bucket_cls.create_bucket.call_args.kwargs
        assert kwargs["name"].en == "Research Docs"
        assert kwargs["configuration"] == {"embedding_model": "embedding/default", "with_summaries": False}
        assert response.configuration == {"embedding_model": "embedding/default"}

    @pytest.mark.asyncio
    async def test_a_configuration_that_does_not_match_the_form_is_rejected_naming_the_field(
        self, locale_handler, s3_service
    ):
        """Accepted-when #2 of #1822."""
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, _rag_request(with_summaries="sometimes"), locale_handler, s3_service, _user()
                )

        assert exc_info.value.status_code == 400
        assert "with_summaries" in exc_info.value.detail
        bucket_cls.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_blank_name_is_rejected(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, _rag_request(name={"en": ""}), locale_handler, s3_service, _user()
                )

        assert exc_info.value.status_code == 400
        assert "name" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_two_ingestors_with_different_forms_coexist(self, locale_handler, s3_service):
        """Accepted-when #4 of #1822: each database is held to its own ingestor's form, not a platform-wide one."""
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket(ingestor="crawler")

            await KnowledgeService.create_database(
                "sites",
                CreateDatabaseRequest(
                    ingestor="crawler",
                    configuration={
                        "name": {"en": "Sites"},
                        "description": {"en": "Crawled"},
                        "crawl_depth": 5,
                        "llm_model": "text-generation/pick",
                    },
                ),
                locale_handler,
                s3_service,
                _user(),
            )

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    "sites2",
                    CreateDatabaseRequest(
                        ingestor=RAG.id,
                        configuration={"name": {"en": "Sites"}, "description": {"en": "x"}, "crawl_depth": 5},
                    ),
                    locale_handler,
                    s3_service,
                    _user(),
                )

        assert bucket_cls.create_bucket.call_args.kwargs["configuration"]["crawl_depth"] == 5
        assert exc_info.value.status_code == 400
        assert "embedding_model" in exc_info.value.detail


class TestModelSelection:
    """Every announced model picker is checked against LiteLLM, whatever the pipeline named the field."""

    @pytest.mark.asyncio
    async def test_a_picker_inside_a_group_and_inside_a_repeater_is_checked_too(self, locale_handler, s3_service):
        """A ``ModelSelect`` nested in structured knobs must not bypass the mode and access checks."""
        identity = {"name": {"en": "Nested"}, "description": {"en": "x"}}
        wrong_group = {**identity, "enrichment": {"model": "embedding/pick"}, "sources": []}
        wrong_repeater = {
            **identity,
            "enrichment": {"model": "text-generation/pick"},
            "sources": [{"model": "text-generation/pick"}],
        }
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as group_error:
                await KnowledgeService.create_database(
                    "nested",
                    CreateDatabaseRequest(ingestor="nested", configuration=wrong_group),
                    locale_handler,
                    s3_service,
                    _user(),
                )
            with pytest.raises(HTTPException) as repeater_error:
                await KnowledgeService.create_database(
                    "nested",
                    CreateDatabaseRequest(ingestor="nested", configuration=wrong_repeater),
                    locale_handler,
                    s3_service,
                    _user(),
                )

        assert "enrichment.model" in group_error.value.detail
        assert "sources.0.model" in repeater_error.value.detail
        bucket_cls.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_chosen_model_is_checked_for_the_pickers_mode(self, models, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()

            await KnowledgeService.create_database(
                DATABASE, _rag_request(embedding_model="embedding/pick"), locale_handler, s3_service, _user()
            )

        models.assert_called_once()
        assert models.call_args.args[1] == "embedding/pick"

    @pytest.mark.asyncio
    async def test_rejects_a_chat_model_in_an_embedding_picker(self, locale_handler, s3_service):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE, _rag_request(embedding_model="text-generation/pick"), locale_handler, s3_service, _user()
                )

        assert exc_info.value.status_code == 400
        assert "embedding_model" in exc_info.value.detail
        bucket_cls.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_an_embedding_model_that_declares_no_output_width(self, models, locale_handler, s3_service):
        """The collection's dimension is derived from it, so an undeclared width cannot be guessed."""
        models.side_effect = lambda user, name: MagicMock(
            model_info=MagicMock(mode="embedding", output_vector_size=None)
        )
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, _user())

        assert exc_info.value.status_code == 400
        assert "output_vector_size" in exc_info.value.detail
        bucket_cls.create_bucket.assert_not_called()


class TestAnnouncedFormIsRequired:
    @pytest.mark.asyncio
    async def test_an_ingestor_that_announced_no_form_is_rejected_not_served_a_500(self, locale_handler, s3_service):
        """A row left by a pre-announcement pipeline image has labels but no schema to validate against."""
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(
                    DATABASE,
                    CreateDatabaseRequest(ingestor="stale", configuration={}),
                    locale_handler,
                    s3_service,
                    _user(),
                )

        assert exc_info.value.status_code == 400
        assert "configuration form" in exc_info.value.detail
        bucket_cls.create_bucket.assert_not_called()

    def test_the_stored_alias_free_form_dicts_drive_the_authorization_walk(self):
        """The entity stores elements without ``$``-aliases; the walk must rehydrate exactly those dicts."""
        ConfigAuthorizationService.validate_config_authorization_or_raise(
            form_elements=_registered(RAG).form,
            config={"name": {"en": "x"}, "embedding_model": "embedding/default", "with_summaries": True},
            access_checker=MagicMock(),
            accessible_tenant_ids=set(),
            t=MagicMock(),
        )


class TestGetIngestors:
    def test_offers_every_registered_ingestor_with_its_labels_and_localized_form(self, registered_ingestors):
        t = ApiLocaleHandler("en")

        ingestors = KnowledgeService.get_ingestors(t)

        assert [ingestor.name for ingestor in ingestors] == [IngestorType.DOCUMENT_INGESTION.value, "crawler"]
        assert ingestors[0].display_name == IngestorType.DOCUMENT_INGESTION.value
        assert [element.name for element in ingestors[0].form] == [
            "name",
            "description",
            "embedding_model",
            "with_summaries",
        ]
        assert ingestors[0].form[0].label == "Name *"

    def test_offers_nothing_while_no_pipeline_has_registered(self, registered_ingestors):
        """Without a running pipeline nothing would ingest the database, so nothing is offered."""
        registered_ingestors.all.return_value = []

        assert KnowledgeService.get_ingestors(ApiLocaleHandler("en")) == []


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
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()
            role_cls.objects.return_value.first.return_value = None

            await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, user)

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
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()
            role_cls.objects.return_value.first.return_value = None

            await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, user)

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
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()
            role_cls.objects.return_value.first.return_value = None
            tenant_cls.grant_access_rule.side_effect = RuntimeError("tenant store unavailable")

            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, user)

        assert exc_info.value.status_code == 500
        s3_service.delete_container.assert_called_once_with(DATABASE)
        bucket_cls.delete_bucket.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_a_sysadmin_without_tenant_context_creates_without_a_grant(self, locale_handler, s3_service):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.UserTenantRoleEntity") as user_role_cls,
        ):
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            bucket_cls.create_bucket.return_value = _created_bucket()

            await KnowledgeService.create_database(DATABASE, _rag_request(), locale_handler, s3_service, _user())

        tenant_cls.grant_access_rule.assert_not_called()
        user_role_cls.add_roles.assert_not_called()
