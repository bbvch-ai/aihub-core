from unittest.mock import MagicMock, patch

from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"


def _bucket(
    bucket_id: str,
    db_name: str,
    deleting: bool = False,
    ingestor: str = IngestorType.DOCUMENT_INGESTION.value,
    auto_sync: bool = False,
) -> MagicMock:
    return MagicMock(
        id=bucket_id,
        db_name=db_name,
        bucket_name=db_name,
        auto_sync=auto_sync,
        ingestor=ingestor,
        deleting=deleting,
        name=None,
    )


def _namespace(namespace_name: str, deleting: bool = False) -> MagicMock:
    return MagicMock(namespace_name=namespace_name, deleting=deleting)


def _locale_handler() -> MagicMock:
    t = MagicMock()
    t.locale = "en"
    t.extract.return_value = None
    return t


def _settings(show_legacy: bool) -> MagicMock:
    settings_cls = MagicMock()
    settings_cls.return_value.SHOW_LEGACY_KNOWLEDGE = show_legacy
    return settings_cls


class TestGetDatabasesExcludesDeletingRows:
    def test_a_bucket_flagged_deleting_is_hidden(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
            patch.object(KnowledgeService, "_ensure_db_exists"),
            patch(f"{_SERVICE_MODULE}.NamespaceDTO"),
        ):
            bucket_cls.get_all_buckets.return_value = [
                _bucket("b1", "alive"),
                _bucket("b2", "doomed", deleting=True),
            ]
            namespace_cls.get_namespaces_by_bucket.return_value = []
            ref_doc_cls.count_by_namespace.return_value = 0

            databases = KnowledgeService.get_databases(_locale_handler())

        assert [db.name for db in databases] == ["alive"]

    def test_deletable_flag_is_false_for_legacy_and_auto_sync_databases(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
            patch(f"{_SERVICE_MODULE}.AIHubSettings", _settings(show_legacy=True)),
            patch.object(KnowledgeService, "_ensure_db_exists"),
            patch(f"{_SERVICE_MODULE}.NamespaceDTO"),
        ):
            bucket_cls.get_all_buckets.return_value = [
                _bucket("b1", "selfservice", ingestor=IngestorType.DOCUMENT_INGESTION.value),
                _bucket("b2", "defaultknowledge", ingestor=IngestorType.DEFAULT_RAG.value),
                _bucket("b3", "sharedknowledge", ingestor=IngestorType.SHARED_RAG.value),
                _bucket("b4", "synced", auto_sync=True),
            ]
            namespace_cls.get_namespaces_by_bucket.return_value = []
            ref_doc_cls.count_by_namespace.return_value = 0

            databases = KnowledgeService.get_databases(_locale_handler())

        deletable_by_name = {db.name: db.deletable for db in databases}
        assert deletable_by_name == {
            "selfservice": True,
            "defaultknowledge": False,
            "sharedknowledge": False,
            "synced": False,
        }


class TestGetDatabasesHidesLegacyDatabases:
    @staticmethod
    def _run(show_legacy: bool) -> list[str]:
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
            patch(f"{_SERVICE_MODULE}.AIHubSettings", _settings(show_legacy=show_legacy)),
            patch.object(KnowledgeService, "_ensure_db_exists"),
            patch(f"{_SERVICE_MODULE}.NamespaceDTO"),
        ):
            bucket_cls.get_all_buckets.return_value = [
                _bucket("b1", "selfservice", ingestor=IngestorType.DOCUMENT_INGESTION.value),
                _bucket("b2", "defaultknowledge", ingestor=IngestorType.DEFAULT_RAG.value),
                _bucket("b3", "sharedknowledge", ingestor=IngestorType.SHARED_RAG.value),
            ]
            namespace_cls.get_namespaces_by_bucket.return_value = []
            ref_doc_cls.count_by_namespace.return_value = 0

            return [db.name for db in KnowledgeService.get_databases(_locale_handler())]

    def test_legacy_databases_are_hidden_by_default(self):
        assert self._run(show_legacy=False) == ["selfservice"]

    def test_legacy_databases_are_shown_when_opted_in(self):
        assert self._run(show_legacy=True) == ["selfservice", "defaultknowledge", "sharedknowledge"]

    def test_a_namespace_flagged_deleting_is_hidden_while_its_bucket_survives(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.RefDoc") as ref_doc_cls,
            patch.object(KnowledgeService, "_ensure_db_exists"),
            patch(f"{_SERVICE_MODULE}.NamespaceDTO") as namespace_dto_cls,
            patch(f"{_SERVICE_MODULE}.DatabaseDTO") as database_dto_cls,
        ):
            bucket_cls.get_all_buckets.return_value = [_bucket("b1", "alive")]
            namespace_cls.get_namespaces_by_bucket.return_value = [
                _namespace("keep"),
                _namespace("drop", deleting=True),
            ]
            ref_doc_cls.count_by_namespace.return_value = 0

            KnowledgeService.get_databases(_locale_handler())

        # Only the surviving namespace is counted and converted; the deleting one is skipped entirely.
        assert ref_doc_cls.count_by_namespace.call_count == 1
        assert namespace_dto_cls.from_entity.call_count == 1
        assert namespace_dto_cls.from_entity.call_args.kwargs["entity"].namespace_name == "keep"
        assert database_dto_cls.call_args.kwargs["namespaces"] == [namespace_dto_cls.from_entity.return_value]
