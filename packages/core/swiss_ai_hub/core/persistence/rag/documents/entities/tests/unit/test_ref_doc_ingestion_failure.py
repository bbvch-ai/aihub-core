"""How the retry sensor's failure reports land on a document record, against the dev Mongo."""

from typing import Any

import pytest
from mongoengine import NotUniqueError, connect, disconnect
from mongoengine.connection import get_db

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

pytestmark = pytest.mark.integration

DB_ALIAS = "docstore_ingestion_failure_test"
SOURCE = "s3://kb/finance/q3.pdf"
DOC_ID = source_to_doc_id(SOURCE)
RUN_STARTED = 1_700_000_000
RUN_FAILED = RUN_STARTED + 120


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


def _seed(collection: Any, *, updated_at: int, text: str = "", is_ingested: bool = False) -> None:
    collection.insert_one(
        {
            "_id": DOC_ID,
            "__type__": "1",
            "__data__": {
                "id_": DOC_ID,
                "text": text,
                "metadata": {
                    "source": SOURCE,
                    "namespace": "finance",
                    "version": "1",
                    "is_ingested": is_ingested,
                    "created_at": updated_at,
                    "updated_at": updated_at,
                    "inserted_at": updated_at,
                },
                "excluded_embed_metadata_keys": [],
                "excluded_llm_metadata_keys": [],
            },
        }
    )


def _report(*, gave_up: bool = True) -> bool:
    return RefDoc.record_ingestion_failure(
        db_alias=DB_ALIAS,
        doc_id=DOC_ID,
        failed_attempts=4,
        gave_up=gave_up,
        failed_at=RUN_FAILED,
        attempt_started_at=RUN_STARTED,
    )


def _metadata(documents: Any) -> dict:
    return documents.find_one({"_id": DOC_ID})["__data__"]["metadata"]


class TestStaleFailures:
    """A failure is reported only on a record the failed attempt could have seen."""

    def test_a_record_from_before_the_attempt_started_is_reported_failed(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED - 60)

        assert _report() is True

        metadata = _metadata(documents)
        assert (metadata["ingestion_failed_attempts"], metadata["ingestion_gave_up"]) == (4, True)
        assert metadata["ingestion_failed_at"] == RUN_FAILED

    def test_a_re_upload_while_the_attempt_was_running_is_left_processing(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED + 30)

        assert _report() is False

        assert "ingestion_failed_attempts" not in _metadata(documents)

    def test_a_re_upload_in_the_second_the_attempt_started_is_left_processing(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED)

        assert _report() is False

        assert "ingestion_failed_attempts" not in _metadata(documents)

    def test_an_ingested_record_is_left_alone(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED - 60, is_ingested=True)

        assert _report() is False


class TestPlaceholdersNeverOverwrite:
    """MongoEngine's save() of a document with an id replaces the record holding it; placeholders must not."""

    def test_a_placeholder_does_not_replace_a_parsed_record(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED, text="Parsed text")

        with pytest.raises(NotUniqueError):
            RefDoc.create_placeholder(DB_ALIAS, SOURCE, namespace="finance")

        assert documents.find_one({"_id": DOC_ID})["__data__"]["text"] == "Parsed text"

    def test_a_failed_placeholder_does_not_replace_a_parsed_record(self, documents) -> None:
        _seed(documents, updated_at=RUN_STARTED, text="Parsed text")

        created = RefDoc.create_failed_placeholder(
            DB_ALIAS, SOURCE, namespace="finance", failed_attempts=1, gave_up=False, failed_at=RUN_FAILED
        )

        assert created is False
        assert documents.find_one({"_id": DOC_ID})["__data__"]["text"] == "Parsed text"

    def test_a_failed_placeholder_takes_the_failure_of_a_later_attempt(self, documents) -> None:
        RefDoc.create_failed_placeholder(
            DB_ALIAS, SOURCE, namespace="finance", failed_attempts=1, gave_up=False, failed_at=RUN_STARTED - 600
        )

        assert _report() is True

        assert _metadata(documents)["ingestion_gave_up"] is True


def test_a_fresh_run_clears_a_reported_failure(documents) -> None:
    _seed(documents, updated_at=RUN_STARTED - 60)
    _report()

    assert RefDoc.clear_ingestion_failures(DB_ALIAS, [DOC_ID]) == 1

    metadata = _metadata(documents)
    assert not {"ingestion_failed_attempts", "ingestion_gave_up", "ingestion_failed_at"} & metadata.keys()
    assert RefDoc.clear_ingestion_failures(DB_ALIAS, [DOC_ID]) == 0
