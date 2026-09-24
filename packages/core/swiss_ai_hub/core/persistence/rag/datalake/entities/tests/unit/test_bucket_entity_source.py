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
