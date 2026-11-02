import pytest
from mongoengine import connect, disconnect
from mongoengine.context_managers import switch_db

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

DB_ALIAS = "docstore_delete_test"
NS_A = "alpha"
NS_B = "beta"


@pytest.fixture
def docstore_connection():
    # switch_db resolves the default alias before switching, so both must be connected — mirrors the
    # app, where a default connection exists at startup and the per-database docstore alias is registered lazily.
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        alias=DB_ALIAS,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield client
    disconnect()
    disconnect(alias=DB_ALIAS)


@pytest.fixture(autouse=True)
def clean_documents(docstore_connection):
    with switch_db(RefDoc, DB_ALIAS) as SwitchedRefDoc:
        SwitchedRefDoc.objects.delete()
    yield
    with switch_db(RefDoc, DB_ALIAS) as SwitchedRefDoc:
        SwitchedRefDoc.objects.delete()


def _seed(namespace: str, name: str) -> None:
    RefDoc.create_placeholder(db_alias=DB_ALIAS, source=f"s3://bucket/{namespace}/{name}", namespace=namespace)


def test_delete_by_namespace_removes_only_the_target_namespace(docstore_connection):
    _seed(NS_A, "a1.pdf")
    _seed(NS_A, "a2.pdf")
    _seed(NS_B, "b1.pdf")

    removed = RefDoc.delete_by_namespace(db_alias=DB_ALIAS, namespace=NS_A)

    assert removed == 2
    assert RefDoc.count_by_namespace(db_alias=DB_ALIAS, namespace=NS_A) == 0
    assert RefDoc.count_by_namespace(db_alias=DB_ALIAS, namespace=NS_B) == 1


def test_delete_by_namespace_is_a_noop_for_an_empty_namespace(docstore_connection):
    _seed(NS_B, "b1.pdf")

    removed = RefDoc.delete_by_namespace(db_alias=DB_ALIAS, namespace=NS_A)

    assert removed == 0
    assert RefDoc.count_by_namespace(db_alias=DB_ALIAS, namespace=NS_B) == 1
