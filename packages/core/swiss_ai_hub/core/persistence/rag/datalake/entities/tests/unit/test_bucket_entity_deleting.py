import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity


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


def test_new_buckets_are_not_deleting_by_default(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="freshbucket")

    assert bucket.deleting is False


def test_mark_deleting_flags_the_bucket(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="doomedbucket")

    BucketEntity.mark_deleting(str(bucket.id))

    assert BucketEntity.get_bucket_by_id(str(bucket.id)).deleting is True
