import pytest
from bson import ObjectId
from mongoengine import ValidationError, connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType


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


def _insert_pre_upgrade_row(mongo_connection, bucket_name: str) -> None:
    """Write a bucket row exactly as a release predating the ``ingestor`` field would have: no such key."""
    mongo_connection[AIHubSettings().MONGO_MAIN_DB_NAME]["buckets"].insert_one(
        {
            "_id": ObjectId(),
            "bucket_name": bucket_name,
            "db_name": bucket_name,
            "name": {"en": bucket_name},
            "description": {"en": bucket_name},
            "auto_sync": False,
            "datalake_type": "s3",
        }
    )


class TestIngestorDefault:
    def test_row_predating_the_field_is_not_claimed_by_the_document_ingestion_pipeline(self, mongo_connection):
        """Upgrade guard: a bucket written before the field existed must not be re-ingested.

        MongoEngine applies the field default when the key is absent, so an unsafe default would hand every
        pre-existing knowledge database to the document ingestion pipeline on upgrade — double-ingesting corpora
        that a deploy-bound pipeline already owns.
        """
        _insert_pre_upgrade_row(mongo_connection, "legacyknowledge")

        bucket = BucketEntity.get_bucket_by_bucket_name("legacyknowledge")

        assert bucket.ingestor == IngestorType.UNASSIGNED.value
        assert bucket.ingestor != IngestorType.DOCUMENT_INGESTION.value

    def test_document_ingestion_pipeline_only_claims_buckets_explicitly_assigned_to_it(self, mongo_connection):
        _insert_pre_upgrade_row(mongo_connection, "legacyknowledge")
        BucketEntity.create_bucket(bucket_name="defaultknowledge", ingestor=IngestorType.DEFAULT_RAG.value)
        BucketEntity.create_bucket(bucket_name="selfservicedb", ingestor=IngestorType.DOCUMENT_INGESTION.value)

        owned = [
            bucket.bucket_name
            for bucket in BucketEntity.get_all_buckets()
            if bucket.ingestor == IngestorType.DOCUMENT_INGESTION.value
        ]

        assert owned == ["selfservicedb"]

    def test_create_bucket_does_not_hand_a_bucket_to_a_pipeline_by_default(self):
        bucket = BucketEntity.create_bucket(bucket_name="unclaimeddb")

        assert bucket.ingestor == IngestorType.UNASSIGNED.value

    def test_unassigned_is_a_legacy_routing_token_not_a_registrable_ingestor(self):
        assert IngestorType.UNASSIGNED in IngestorType.legacy()
        assert IngestorType.DOCUMENT_INGESTION not in IngestorType.legacy()

    def test_the_ingestor_configuration_is_stored_and_read_back_as_given(self):
        bucket = BucketEntity.create_bucket(
            bucket_name="configureddb", configuration={"embedding_model": "embedding/bge-m3", "with_summaries": False}
        )

        stored = BucketEntity.get_bucket_by_bucket_name("configureddb")

        assert stored.configuration == {"embedding_model": "embedding/bge-m3", "with_summaries": False}
        assert bucket.configuration == stored.configuration

    def test_a_row_predating_the_configuration_field_reads_as_empty(self, mongo_connection):
        _insert_pre_upgrade_row(mongo_connection, "legacyknowledge")

        assert BucketEntity.get_bucket_by_bucket_name("legacyknowledge").configuration == {}


class TestCarryOverRetiredModelColumns:
    def _insert_pre_announcement_row(self, mongo_connection, bucket_name: str, **columns) -> None:
        mongo_connection[AIHubSettings().MONGO_MAIN_DB_NAME]["buckets"].insert_one(
            {
                "_id": ObjectId(),
                "bucket_name": bucket_name,
                "db_name": bucket_name,
                "name": {"en": bucket_name},
                "description": {"en": ""},
                "ingestor": IngestorType.DOCUMENT_INGESTION.value,
                **columns,
            }
        )

    def test_the_retired_columns_become_configuration_keys_and_are_removed(self, mongo_connection):
        self._insert_pre_announcement_row(
            mongo_connection, "olddb", llm_model="text-generation/old", embedding_model="embedding/old"
        )

        carried = BucketEntity.carry_over_retired_model_columns()

        raw = mongo_connection[AIHubSettings().MONGO_MAIN_DB_NAME]["buckets"].find_one({"bucket_name": "olddb"})
        assert carried == 1
        assert raw["configuration"] == {"llm_model": "text-generation/old", "embedding_model": "embedding/old"}
        assert "llm_model" not in raw and "embedding_model" not in raw
        assert BucketEntity.get_bucket_by_bucket_name("olddb").configuration["embedding_model"] == "embedding/old"

    def test_a_null_column_is_dropped_without_writing_a_key(self, mongo_connection):
        """``None`` meant "deployment default"; a missing key means the same, so nothing is carried."""
        self._insert_pre_announcement_row(mongo_connection, "defaultsdb", llm_model=None, embedding_model=None)

        BucketEntity.carry_over_retired_model_columns()

        assert BucketEntity.get_bucket_by_bucket_name("defaultsdb").configuration == {}

    def test_running_twice_is_a_no_op(self, mongo_connection):
        self._insert_pre_announcement_row(mongo_connection, "olddb", embedding_model="embedding/old")
        BucketEntity.carry_over_retired_model_columns()

        assert BucketEntity.carry_over_retired_model_columns() == 0


class TestUpdateBucket:
    def test_auto_sync_can_be_toggled_off(self):
        """A truthy check would swallow ``auto_sync=False`` and make the flag impossible to turn off."""
        bucket = BucketEntity.create_bucket(bucket_name="syncingdb", auto_sync=True)

        updated = BucketEntity.update_bucket(str(bucket.id), auto_sync=False)

        assert updated.auto_sync is False

    def test_omitting_auto_sync_leaves_it_unchanged(self):
        bucket = BucketEntity.create_bucket(bucket_name="syncingdb", auto_sync=True)

        updated = BucketEntity.update_bucket(str(bucket.id), ingestor=IngestorType.DOCUMENT_INGESTION.value)

        assert updated.auto_sync is True


class TestBucketNameValidation:
    def test_rejects_a_name_that_does_not_start_with_a_letter(self):
        """The name doubles as a Milvus collection, which must start with a letter or underscore."""
        with pytest.raises(ValidationError):
            BucketEntity.create_bucket(bucket_name="001")

    def test_accepts_a_letter_led_alphanumeric_name(self):
        bucket = BucketEntity.create_bucket(bucket_name="db001")

        assert bucket.bucket_name == "db001"
