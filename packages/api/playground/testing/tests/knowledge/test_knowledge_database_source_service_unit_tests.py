from typing import Annotated, Self
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from mongoengine import DoesNotExist
from pydantic import Field
from swiss_ai_hub.core.form import ChipsInput, Form, InputText, Password
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.ingestors import IngestorConfig
from swiss_ai_hub.core.persistence import ConfigSpecsEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import Ingestor, IngestorType, SourcePipeline
from swiss_ai_hub.core.secrets import SecretEncryptionService, SecretMasker
from swiss_ai_hub.core.source_pipelines import SourcePipelineConfig

from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.dto.update_database_source_request import UpdateDatabaseSourceRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"
DATABASE = "hrdocs"


class _Sftp(Form):
    host: Annotated[str | InputText, Field(description="Host")] = ""
    password: Annotated[str | Password, Field(description="Password")] = ""

    @classmethod
    def as_form(cls) -> Self:
        return cls(host=InputText(label=LocaleString(en="Host")), password=Password(label=LocaleString(en="Password")))


class _SyncConfig(SourcePipelineConfig):
    root_path: Annotated[str | InputText, Field(description="Root")] = ""
    include_patterns: Annotated[list[str] | ChipsInput, Field(description="Include")] = Field(default_factory=list)
    sftp: Annotated[_Sftp, Field(description="SFTP")] = Field(default_factory=_Sftp)

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            root_path=InputText(label=LocaleString(en="Root")),
            include_patterns=ChipsInput(label=LocaleString(en="Include")),
            sftp=_Sftp.as_form(),
        )


RCLONE = SourcePipeline.from_config("rclone", LocaleString(en="rclone"), LocaleString(en="sync"), _SyncConfig.as_form())
INGESTOR = Ingestor.from_config(
    IngestorType.DOCUMENT_INGESTION.value, LocaleString(en="rag"), LocaleString(en="pipeline"), IngestorConfig.as_form()
)


def _registered(form, config_specs, to_value) -> MagicMock:
    entity = MagicMock()
    entity.form = [element.model_dump() for element in form]
    entity.form_elements = form
    entity.config_specs = ConfigSpecsEntity.from_specs(config_specs)
    entity.to_ingestor.return_value = to_value
    entity.to_source_pipeline.return_value = to_value
    return entity


@pytest.fixture(autouse=True)
def registrations():
    with (
        patch(f"{_SERVICE_MODULE}.IngestorEntity") as ingestor_entity,
        patch(f"{_SERVICE_MODULE}.SourcePipelineEntity") as source_entity,
        patch(f"{_SERVICE_MODULE}.ConfigAuthorizationService.validate_for_user_or_raise", new_callable=AsyncMock),
    ):
        ingestor_entity.find.side_effect = lambda ingestor_id: (
            _registered(INGESTOR.form, INGESTOR.config_specs, INGESTOR) if ingestor_id == INGESTOR.id else None
        )
        source_entity.find.side_effect = lambda source_id: (
            _registered(RCLONE.form, RCLONE.config_specs, RCLONE) if source_id == RCLONE.id else None
        )
        source_entity.all.return_value = [RCLONE]
        yield source_entity


@pytest.fixture(autouse=True)
def encryption() -> SecretEncryptionService:
    service = SecretEncryptionService(Fernet.generate_key().decode())
    with patch(f"{_SERVICE_MODULE}.SecretEncryptionService.from_settings", return_value=service):
        yield service


@pytest.fixture
def locale_handler() -> MagicMock:
    t = MagicMock()
    t.locale = "en"
    t.extract.return_value = "HR Docs"
    return t


def _user() -> MagicMock:
    user = MagicMock()
    user.acting_within_tenant = None
    return user


def _bucket(**overrides) -> MagicMock:
    defaults = dict(
        db_name=DATABASE,
        bucket_name=DATABASE,
        id="abc123",
        ingestor=INGESTOR.id,
        configuration={},
        source=None,
        source_configuration={},
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


def _sftp_configuration(password: str) -> dict:
    return {
        "root_path": "/srv/docs",
        "include_patterns": ["*.pdf"],
        "sftp": {"host": "files.acme", "password": password},
    }


class TestCreateWithSource:
    @pytest.mark.asyncio
    async def test_a_sourced_database_stores_its_encrypted_source_configuration_and_masks_it_in_the_response(
        self, locale_handler, encryption
    ):
        s3_service = MagicMock()
        s3_service.container_exists.return_value = False
        request = CreateDatabaseRequest(
            ingestor=INGESTOR.id,
            configuration={"name": {"en": "HR Docs"}, "description": {"en": "Policies"}},
            source=RCLONE.id,
            source_configuration=_sftp_configuration("pw"),
        )
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist

            def create_bucket(**kwargs):
                return _bucket(source=kwargs["source"], source_configuration=kwargs["source_configuration"])

            bucket_cls.create_bucket.side_effect = create_bucket
            response = await KnowledgeService.create_database(DATABASE, request, locale_handler, s3_service, _user())

        stored = bucket_cls.create_bucket.call_args.kwargs["source_configuration"]
        assert bucket_cls.create_bucket.call_args.kwargs["source"] == "rclone"
        assert stored["sftp"]["host"] == "files.acme"
        assert encryption.is_encrypted(stored["sftp"]["password"])
        assert encryption.decrypt(stored["sftp"]["password"]) == "pw"
        assert response.source == "rclone"
        assert response.source_configuration["sftp"] == {"host": "files.acme", "password": SecretMasker.MASK}

    @pytest.mark.asyncio
    async def test_an_unregistered_source_is_refused_before_anything_is_created(self, locale_handler):
        request = CreateDatabaseRequest(
            ingestor=INGESTOR.id,
            configuration={"name": {"en": "HR Docs"}, "description": {"en": "Policies"}},
            source="never_registered",
        )
        s3_service = MagicMock()
        s3_service.container_exists.return_value = False
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_bucket_name.side_effect = DoesNotExist
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_database(DATABASE, request, locale_handler, s3_service, _user())

        assert exc_info.value.status_code == 400
        assert "never_registered" in exc_info.value.detail
        bucket_cls.create_bucket.assert_not_called()


class TestUpdateSource:
    @pytest.mark.asyncio
    async def test_a_resubmitted_mask_keeps_the_stored_secret_while_other_fields_change(
        self, locale_handler, encryption
    ):
        stored = _sftp_configuration(encryption.encrypt("old-pw"))
        request = UpdateDatabaseSourceRequest(
            source=RCLONE.id,
            source_configuration={**_sftp_configuration(SecretMasker.MASK), "include_patterns": ["*.docx"]},
        )
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(source="rclone", source_configuration=stored)
            bucket_cls.update_source.side_effect = lambda name, source, configuration: _bucket(
                source=source, source_configuration=configuration
            )
            response = await KnowledgeService.update_database_source(DATABASE, request, locale_handler, _user())

        written = bucket_cls.update_source.call_args.args[2]
        assert written["include_patterns"] == ["*.docx"]
        assert encryption.decrypt(written["sftp"]["password"]) == "old-pw"
        assert response.source_configuration["sftp"]["password"] == SecretMasker.MASK

    @pytest.mark.asyncio
    async def test_a_new_secret_replaces_the_stored_one(self, locale_handler, encryption):
        stored = _sftp_configuration(encryption.encrypt("old-pw"))
        request = UpdateDatabaseSourceRequest(source=RCLONE.id, source_configuration=_sftp_configuration("new-pw"))
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(source="rclone", source_configuration=stored)
            bucket_cls.update_source.side_effect = lambda name, source, configuration: _bucket(
                source=source, source_configuration=configuration
            )
            await KnowledgeService.update_database_source(DATABASE, request, locale_handler, _user())

        assert encryption.decrypt(bucket_cls.update_source.call_args.args[2]["sftp"]["password"]) == "new-pw"

    @pytest.mark.asyncio
    async def test_clearing_the_source_returns_the_database_to_manual_upload(self, locale_handler):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(source="rclone", source_configuration={"a": 1})
            bucket_cls.update_source.return_value = _bucket()
            response = await KnowledgeService.update_database_source(
                DATABASE, UpdateDatabaseSourceRequest(source=None), locale_handler, _user()
            )

        bucket_cls.update_source.assert_called_once_with(DATABASE, None, None)
        assert response.source is None
        assert response.source_configuration == {}

    @pytest.mark.asyncio
    async def test_a_mask_with_nothing_stored_is_a_client_error(self, locale_handler):
        request = UpdateDatabaseSourceRequest(
            source=RCLONE.id, source_configuration=_sftp_configuration(SecretMasker.MASK)
        )
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(source="rclone", source_configuration={})
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.update_database_source(DATABASE, request, locale_handler, _user())

        assert exc_info.value.status_code == 400
        assert "sftp.password" in exc_info.value.detail


class TestSourcedDatabasesRefuseManualContentChanges:
    @pytest.mark.asyncio
    async def test_manual_namespace_creation_is_refused(self, locale_handler):
        from swiss_ai_hub.api.routes.knowledge.dto.create_namespace_request import CreateNamespaceRequest

        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(source="rclone")
            with pytest.raises(HTTPException) as exc_info:
                await KnowledgeService.create_namespace(
                    DATABASE, "policies", CreateNamespaceRequest(folder_name="policies"), locale_handler, _user()
                )

        assert exc_info.value.status_code == 403
        assert "rclone" in exc_info.value.detail


class TestSourcePipelines:
    def test_registered_source_pipelines_are_served_with_their_localized_form(self, locale_handler):
        pipelines = KnowledgeService.get_source_pipelines(locale_handler)

        assert [pipeline.name for pipeline in pipelines] == ["rclone"]
        assert {element.name for element in pipelines[0].form} == {"root_path", "include_patterns", "sftp"}
