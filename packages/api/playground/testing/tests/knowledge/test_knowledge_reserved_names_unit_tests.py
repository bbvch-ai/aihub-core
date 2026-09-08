import pytest

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

MONGO_SYSTEM_DATABASES = ("admin", "local", "config")
LEGACY_DATABASES = ("defaultknowledge", "sharedknowledge")


@pytest.fixture
def show_legacy_knowledge(monkeypatch):
    def _set(shown: bool) -> None:
        monkeypatch.setenv("AIHUB_SHOW_LEGACY_KNOWLEDGE", str(shown))
        monkeypatch.setenv("AIHUB_DEFAULT_BUCKET_NAME", LEGACY_DATABASES[0])
        monkeypatch.setenv("AIHUB_SHARED_BUCKET_NAME", LEGACY_DATABASES[1])

    return _set


class TestReservedForCreation:
    @pytest.mark.parametrize("shown", [True, False])
    @pytest.mark.parametrize("database", MONGO_SYSTEM_DATABASES + LEGACY_DATABASES)
    def test_a_name_holding_a_store_can_never_be_created_on(self, database, shown, show_legacy_knowledge):
        """The legacy corpora are frozen with no migration path, so a new database bound to one would be
        ingested on top of it — reserving them does not depend on whether they are shown."""
        show_legacy_knowledge(shown)

        assert database in KnowledgeService.reserved_database_names()

    def test_the_applications_own_main_database_is_reserved(self, monkeypatch):
        monkeypatch.setenv("AIHUB_MONGO_MAIN_DB_NAME", "aihubmain")

        assert "aihubmain" in KnowledgeService.reserved_database_names()

    def test_an_ordinary_name_is_free(self, show_legacy_knowledge):
        show_legacy_knowledge(False)

        assert "researchdocs" not in KnowledgeService.reserved_database_names()


class TestNonBrowsable:
    @pytest.mark.parametrize("shown", [True, False])
    @pytest.mark.parametrize("database", MONGO_SYSTEM_DATABASES)
    def test_mongo_system_databases_are_never_readable(self, database, shown, show_legacy_knowledge):
        show_legacy_knowledge(shown)

        assert database in KnowledgeService.non_browsable_database_names()

    @pytest.mark.parametrize("database", LEGACY_DATABASES)
    def test_legacy_databases_are_readable_when_shown(self, database, show_legacy_knowledge):
        """Reserving a name for creation is no reason to refuse reads of the database already on it: the
        frozen pipelines still serve those corpora, so the per-resource rules govern them like any other."""
        show_legacy_knowledge(True)

        assert database not in KnowledgeService.non_browsable_database_names()

    @pytest.mark.parametrize("database", LEGACY_DATABASES)
    def test_legacy_databases_are_unreadable_when_hidden(self, database, show_legacy_knowledge):
        """Hidden must mean unreadable, not merely unlisted, or the name alone reaches the documents."""
        show_legacy_knowledge(False)

        assert database in KnowledgeService.non_browsable_database_names()
