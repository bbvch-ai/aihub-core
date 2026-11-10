import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.persistence.rag.datalake.entities.source_pipeline_type import SourcePipelineType


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_buckets(mongo_connection):
    BucketEntity.objects.delete()
    yield
    BucketEntity.objects.delete()


class TestSourceAxis:
    def test_a_database_without_a_source_is_filled_by_manual_upload(self):
        bucket = BucketEntity.create_bucket("manualdb", ingestor=IngestorType.DOCUMENT_INGESTION.value)

        assert bucket.source is None
        assert bucket.source_configuration == {}

    def test_a_database_stores_its_source_and_configuration_next_to_its_ingestor(self):
        bucket = BucketEntity.create_bucket(
            "synceddb",
            ingestor=IngestorType.DOCUMENT_INGESTION.value,
            source=SourcePipelineType.RCLONE.value,
            source_configuration={"backend_type": "sftp", "sftp": {"host": "files.acme"}},
        )

        stored = BucketEntity.get_bucket_by_bucket_name("synceddb")
        assert stored.ingestor == IngestorType.DOCUMENT_INGESTION.value
        assert stored.source == SourcePipelineType.RCLONE.value
        assert stored.source_configuration["sftp"]["host"] == "files.acme"
        assert bucket.id == stored.id

    def test_the_source_pipeline_enumerates_only_its_live_databases(self):
        BucketEntity.create_bucket("synceda", source=SourcePipelineType.RCLONE.value)
        BucketEntity.create_bucket("syncedb", source=SourcePipelineType.RCLONE.value)
        BucketEntity.create_bucket("manualc")
        BucketEntity.create_bucket("otherd", source="acme_sync")
        deleting = BucketEntity.create_bucket("goinge", source=SourcePipelineType.RCLONE.value)
        deleting.deleting = True
        deleting.save()

        names = [bucket.bucket_name for bucket in BucketEntity.get_buckets_by_source(SourcePipelineType.RCLONE.value)]

        assert names == ["synceda", "syncedb"]

    def test_the_source_is_replaced_wholesale_and_can_return_to_manual_upload(self):
        BucketEntity.create_bucket("rotating", source=SourcePipelineType.RCLONE.value, source_configuration={"a": 1})

        BucketEntity.update_source("rotating", SourcePipelineType.RCLONE.value, {"b": 2})
        assert BucketEntity.get_bucket_by_bucket_name("rotating").source_configuration == {"b": 2}

        BucketEntity.update_source("rotating", None, None)
        stored = BucketEntity.get_bucket_by_bucket_name("rotating")
        assert stored.source is None
        assert stored.source_configuration == {}


_STORED = "enc:v1:stored"
_REFRESHED = "enc:v1:refreshed"


def _onedrive_source(**extra: str) -> dict:
    return {"backend_type": "onedrive", "onedrive": {"drive_id": "b!abc", "token": _STORED, **extra}}


def _replace(**overrides) -> bool:
    arguments = {
        "bucket_name": "tokendb",
        "source": SourcePipelineType.RCLONE.value,
        "backend_type": "onedrive",
        "path": "onedrive.token",
        "expected": _STORED,
        "replacement": _REFRESHED,
    } | overrides
    return BucketEntity.replace_source_secret(**arguments)


class TestReplaceSourceSecret:
    """The pipeline writes a refreshed OAuth token back only over exactly the value its run read, so a user's edit
    made in the meantime is never overwritten."""

    def test_the_secret_is_replaced_and_nothing_else_changes(self):
        BucketEntity.create_bucket(
            "tokendb",
            source=SourcePipelineType.RCLONE.value,
            source_configuration=_onedrive_source(client_id="c") | {"root_path": "Docs"},
        )

        assert _replace() is True

        stored = BucketEntity.get_bucket_by_bucket_name("tokendb").source_configuration
        assert stored == {
            "backend_type": "onedrive",
            "root_path": "Docs",
            "onedrive": {"drive_id": "b!abc", "token": _REFRESHED, "client_id": "c"},
        }

    def test_a_token_changed_since_the_run_read_it_is_kept(self):
        BucketEntity.create_bucket(
            "tokendb",
            source=SourcePipelineType.RCLONE.value,
            source_configuration=_onedrive_source() | {"onedrive": {"drive_id": "b!abc", "token": "enc:v1:user"}},
        )

        assert _replace() is False
        assert BucketEntity.get_bucket_by_bucket_name("tokendb").source_configuration["onedrive"]["token"] == (
            "enc:v1:user"
        )

    @pytest.mark.parametrize("source", ["acme_sync", None])
    def test_a_database_that_left_the_source_is_not_written(self, source: str | None):
        BucketEntity.create_bucket("tokendb", source=source, source_configuration=_onedrive_source())

        assert _replace() is False
        assert BucketEntity.get_bucket_by_bucket_name("tokendb").source_configuration["onedrive"]["token"] == _STORED

    def test_a_database_being_deleted_is_not_written(self):
        bucket = BucketEntity.create_bucket(
            "tokendb", source=SourcePipelineType.RCLONE.value, source_configuration=_onedrive_source()
        )
        bucket.deleting = True
        bucket.save()

        assert _replace() is False
        assert BucketEntity.get_bucket_by_bucket_name("tokendb").source_configuration["onedrive"]["token"] == _STORED

    def test_a_source_switched_to_another_backend_is_not_written(self):
        BucketEntity.create_bucket(
            "tokendb",
            source=SourcePipelineType.RCLONE.value,
            source_configuration=_onedrive_source() | {"backend_type": "s3"},
        )

        assert _replace() is False
        assert BucketEntity.get_bucket_by_bucket_name("tokendb").source_configuration["backend_type"] == "s3"

    def test_a_deleted_database_is_not_recreated(self):
        bucket = BucketEntity.create_bucket(
            "tokendb", source=SourcePipelineType.RCLONE.value, source_configuration=_onedrive_source()
        )
        BucketEntity.delete_bucket(str(bucket.id))

        assert _replace() is False
        assert BucketEntity.objects(bucket_name="tokendb").count() == 0

    def test_only_the_named_database_is_written(self):
        BucketEntity.create_bucket(
            "tokendb", source=SourcePipelineType.RCLONE.value, source_configuration=_onedrive_source()
        )
        BucketEntity.create_bucket(
            "otherdb", source=SourcePipelineType.RCLONE.value, source_configuration=_onedrive_source()
        )

        assert _replace() is True
        assert BucketEntity.get_bucket_by_bucket_name("otherdb").source_configuration["onedrive"]["token"] == _STORED
