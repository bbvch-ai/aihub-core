"""The classification request on a database's row is the backfill's work queue (#2483): the run clears only the request
it served, so one made while it ran is not lost."""

from datetime import timedelta

import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity


@pytest.fixture
def mongo_connection():
    client = connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_buckets(mongo_connection):
    BucketEntity.objects.delete()
    yield
    BucketEntity.objects.delete()


def test_a_new_database_owes_no_classification(mongo_connection):
    BucketEntity.create_bucket(bucket_name="freshbucket")

    assert BucketEntity.get_classification_requested_buckets() == []


def test_a_request_is_stored_as_it_is_read_back(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")

    requested_at = BucketEntity.request_classification(str(bucket.id))

    [requested] = BucketEntity.get_classification_requested_buckets()
    assert requested.bucket_name == "invoices"
    assert requested.classification_requested_at == requested_at


def test_a_database_being_deleted_owes_nothing(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="doomed")
    BucketEntity.request_classification(str(bucket.id))

    BucketEntity.mark_deleting(str(bucket.id))

    assert BucketEntity.get_classification_requested_buckets() == []


def test_the_served_request_is_cleared(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")
    requested_at = BucketEntity.request_classification(str(bucket.id))

    assert BucketEntity.clear_classification_request("invoices", requested_at) is True
    assert BucketEntity.get_classification_requested_buckets() == []


def test_a_request_made_while_the_run_ran_survives_it(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")
    served = BucketEntity.request_classification(str(bucket.id))
    newer = served + timedelta(seconds=5)
    BucketEntity.objects(id=bucket.id).update_one(set__classification_requested_at=newer)

    cleared = BucketEntity.clear_classification_request("invoices", served)

    assert cleared is False
    assert BucketEntity.get_bucket_by_bucket_name("invoices").classification_requested_at == newer


def test_a_request_given_up_on_leaves_the_queue_and_is_kept_as_failed(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")
    requested_at = BucketEntity.request_classification(str(bucket.id))

    assert BucketEntity.fail_classification_request("invoices", requested_at) is True

    stored = BucketEntity.get_bucket_by_id(str(bucket.id))
    assert stored.classification_requested_at is None
    assert stored.classification_failed_at == requested_at
    assert BucketEntity.get_classification_requested_buckets() == []


def test_giving_up_on_an_older_request_leaves_a_newer_one_queued(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")
    older = BucketEntity.request_classification(str(bucket.id))
    newer = older + timedelta(seconds=5)
    BucketEntity.objects(id=bucket.id).update_one(set__classification_requested_at=newer)

    assert BucketEntity.fail_classification_request("invoices", older) is False
    assert BucketEntity.get_bucket_by_id(str(bucket.id)).classification_requested_at == newer


def test_a_new_request_clears_the_failed_one(mongo_connection):
    bucket = BucketEntity.create_bucket(bucket_name="invoices")
    BucketEntity.fail_classification_request("invoices", BucketEntity.request_classification(str(bucket.id)))

    BucketEntity.request_classification(str(bucket.id))

    assert BucketEntity.get_bucket_by_id(str(bucket.id)).classification_failed_at is None
