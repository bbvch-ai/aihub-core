"""What a classification backfill reads and writes on the document record (#2483), against the dev Mongo."""

from typing import Any

import pytest
from mongoengine import connect, disconnect
from mongoengine.connection import get_db

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

DB_ALIAS = "docstore_classification_test"


@pytest.fixture
def docstore_connection():
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    client = connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME, alias=DB_ALIAS, host=MongoSettings().CONNECTION_STRING.get_secret_value()
    )
    yield client
    disconnect()
    disconnect(alias=DB_ALIAS)


@pytest.fixture(autouse=True)
def documents(docstore_connection):
    collection = get_db(DB_ALIAS)[RefDoc._meta["collection"]]
    collection.delete_many({})
    yield collection
    collection.delete_many({})


def _seed(collection: Any, doc_id: str, *, is_ingested: bool = True, **metadata: Any) -> None:
    collection.insert_one(
        {
            "_id": doc_id,
            "__type__": "1",
            "__data__": {
                "id_": doc_id,
                "text": f"Text of {doc_id}",
                "metadata": {
                    "source": f"s3://kb/finance/{doc_id}.pdf",
                    "namespace": "finance",
                    "content_hash": f"hash-{doc_id}",
                    "is_ingested": is_ingested,
                    **metadata,
                },
                "excluded_embed_metadata_keys": [],
                "excluded_llm_metadata_keys": [],
            },
        }
    )


def test_states_list_ingested_documents_with_their_metadata_in_source_order(documents):
    _seed(documents, "b", document_classification_version=1)
    _seed(documents, "a")
    _seed(documents, "pending", is_ingested=False)

    states = RefDoc.list_classification_states(DB_ALIAS)

    assert [str(state.id) for state in states] == ["a", "b"]
    assert states[1].data.metadata.document_classification_version == 1


def test_the_text_is_read_only_while_the_content_is_the_one_listed(documents):
    _seed(documents, "a")

    assert RefDoc.text_of(DB_ALIAS, "a", "hash-a") == "Text of a"
    assert RefDoc.text_of(DB_ALIAS, "a", "hash-changed") is None
    assert RefDoc.text_of(DB_ALIAS, "gone", "hash-gone") is None


def test_the_classification_is_written_beside_the_existing_metadata_and_kept_out_of_embedding(documents):
    _seed(documents, "a")

    written = RefDoc.set_classification(
        DB_ALIAS, "a", "hash-a", {"document_type": "invoice", "document_date": "2025-03-14"}, ["document_type"]
    )

    stored = documents.find_one({"_id": "a"})["__data__"]
    assert written is True
    assert stored["metadata"]["document_type"] == "invoice"
    assert stored["metadata"]["document_date"] == "2025-03-14"
    assert stored["metadata"]["source"] == "s3://kb/finance/a.pdf"
    assert stored["excluded_embed_metadata_keys"] == ["document_type"]
    assert stored["excluded_llm_metadata_keys"] == ["document_type"]


def test_a_document_whose_content_changed_is_not_written(documents):
    _seed(documents, "a")

    written = RefDoc.set_classification(DB_ALIAS, "a", "hash-old", {"document_type": "invoice"}, ["document_type"])

    assert written is False
    assert "document_type" not in documents.find_one({"_id": "a"})["__data__"]["metadata"]


def test_writing_twice_does_not_repeat_the_excluded_keys(documents):
    _seed(documents, "a")

    for _ in range(2):
        RefDoc.set_classification(DB_ALIAS, "a", "hash-a", {"document_type": "invoice"}, ["document_type"])

    assert documents.find_one({"_id": "a"})["__data__"]["excluded_embed_metadata_keys"] == ["document_type"]
