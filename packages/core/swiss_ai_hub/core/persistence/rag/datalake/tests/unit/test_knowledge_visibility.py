"""Which knowledge databases are offered to anyone at all: hidden means neither listed nor readable, wherever the
database is asked for."""

from unittest.mock import MagicMock, patch

import pytest
from mongoengine import DoesNotExist

from swiss_ai_hub.core.persistence.rag.datalake.entities.ingestor_type import IngestorType
from swiss_ai_hub.core.persistence.rag.datalake.knowledge_visibility import KnowledgeVisibility

MODULE = "swiss_ai_hub.core.persistence.rag.datalake.knowledge_visibility"
MONGO_SYSTEM_DATABASES = ("admin", "local", "config")
LEGACY_DATABASES = ("defaultknowledge", "sharedknowledge")


@pytest.fixture
def show_legacy_knowledge(monkeypatch):
    def _set(shown: bool) -> None:
        monkeypatch.setenv("AIHUB_SHOW_LEGACY_KNOWLEDGE", str(shown))
        monkeypatch.setenv("AIHUB_DEFAULT_BUCKET_NAME", LEGACY_DATABASES[0])
        monkeypatch.setenv("AIHUB_SHARED_BUCKET_NAME", LEGACY_DATABASES[1])

    return _set


def _bucket(db_name: str, ingestor: str = "document_ingestion") -> MagicMock:
    return MagicMock(db_name=db_name, ingestor=ingestor)


class TestNonBrowsableNames:
    @pytest.mark.parametrize("shown", [True, False])
    @pytest.mark.parametrize("database", MONGO_SYSTEM_DATABASES)
    def test_mongo_system_databases_are_never_readable(self, database, shown, show_legacy_knowledge):
        show_legacy_knowledge(shown)

        assert database in KnowledgeVisibility.non_browsable_database_names()

    @pytest.mark.parametrize("database", LEGACY_DATABASES)
    def test_legacy_databases_are_readable_when_shown(self, database, show_legacy_knowledge):
        """Reserving a name for creation is no reason to refuse reads of the database already on it: the
        frozen pipelines still serve those corpora, so the per-resource rules govern them like any other."""
        show_legacy_knowledge(True)

        assert database not in KnowledgeVisibility.non_browsable_database_names()

    @pytest.mark.parametrize("database", LEGACY_DATABASES)
    def test_legacy_databases_are_unreadable_when_hidden(self, database, show_legacy_knowledge):
        """Hidden must mean unreadable, not merely unlisted, or the name alone reaches the documents."""
        show_legacy_knowledge(False)

        assert database in KnowledgeVisibility.non_browsable_database_names()


class TestBrowsable:
    @pytest.mark.parametrize("ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    def test_a_legacy_bucket_is_hidden_while_legacy_knowledge_is(self, ingestor, show_legacy_knowledge):
        """Matched by ingestor too, so a legacy bucket renamed after seeding stays hidden."""
        show_legacy_knowledge(False)

        assert KnowledgeVisibility.is_browsable(_bucket("renamedlegacy", ingestor)) is False

    def test_a_legacy_bucket_is_offered_where_the_deployment_still_runs_it(self, show_legacy_knowledge):
        show_legacy_knowledge(True)

        assert KnowledgeVisibility.is_browsable(_bucket(LEGACY_DATABASES[1], IngestorType.SHARED_RAG.value)) is True

    def test_an_ordinary_database_is_offered(self, show_legacy_knowledge):
        show_legacy_knowledge(False)

        assert KnowledgeVisibility.is_browsable(_bucket("alpenwerkhandbook")) is True

    def test_a_database_that_no_longer_exists_is_offered_to_nobody(self):
        with patch(f"{MODULE}.BucketEntity.get_bucket_by_db_name", side_effect=DoesNotExist):
            assert KnowledgeVisibility.is_browsable_database("vanished") is False
