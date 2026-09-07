import pytest
from mongoengine import connect, disconnect

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity

BUCKET_ID = "bucket-1"
OTHER_BUCKET_ID = "bucket-2"


@pytest.fixture
def mongo_connection():
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()


@pytest.fixture(autouse=True)
def clean_namespaces(mongo_connection):
    NamespaceEntity.objects.delete()
    yield
    NamespaceEntity.objects.delete()


def test_new_namespaces_are_not_deleting_by_default(mongo_connection):
    namespace = NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="reports")

    assert namespace.deleting is False


def test_mark_deleting_flags_a_single_namespace(mongo_connection):
    namespace = NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="reports")

    NamespaceEntity.mark_deleting(str(namespace.id))

    assert NamespaceEntity.get_namespace_by_id(str(namespace.id)).deleting is True


def test_mark_all_deleting_for_bucket_flags_only_that_buckets_namespaces(mongo_connection):
    ours = NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="reports")
    also_ours = NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="invoices")
    theirs = NamespaceEntity.create_namespace(bucket_id=OTHER_BUCKET_ID, namespace_name="reports")

    updated = NamespaceEntity.mark_all_deleting_for_bucket(BUCKET_ID)

    assert updated == 2
    assert NamespaceEntity.get_namespace_by_id(str(ours.id)).deleting is True
    assert NamespaceEntity.get_namespace_by_id(str(also_ours.id)).deleting is True
    assert NamespaceEntity.get_namespace_by_id(str(theirs.id)).deleting is False


def test_delete_all_for_bucket_removes_only_that_buckets_namespaces(mongo_connection):
    NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="reports")
    NamespaceEntity.create_namespace(bucket_id=BUCKET_ID, namespace_name="invoices")
    survivor = NamespaceEntity.create_namespace(bucket_id=OTHER_BUCKET_ID, namespace_name="reports")

    removed = NamespaceEntity.delete_all_for_bucket(BUCKET_ID)

    assert removed == 2
    assert list(NamespaceEntity.get_namespaces_by_bucket(BUCKET_ID)) == []
    assert [str(n.id) for n in NamespaceEntity.get_namespaces_by_bucket(OTHER_BUCKET_ID)] == [str(survivor.id)]
