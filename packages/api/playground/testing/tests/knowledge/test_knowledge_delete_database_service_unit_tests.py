from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.knowledge.knowledge_service"

DATABASE = "researchdocs"
BUCKET_ID = "bucket-1"
NAMESPACE = "reports"
NAMESPACE_ID = "ns-1"


def _bucket(**overrides) -> MagicMock:
    defaults = dict(
        id=BUCKET_ID,
        bucket_name=DATABASE,
        db_name=DATABASE,
        auto_sync=False,
        ingestor=IngestorType.RAG.value,
    )
    defaults.update(overrides)
    return MagicMock(**defaults)


class TestDeleteDatabase:
    def test_marks_the_bucket_and_all_its_namespaces_deleting(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()

            KnowledgeService.delete_database(database=DATABASE)

        bucket_cls.mark_deleting.assert_called_once_with(BUCKET_ID)
        namespace_cls.mark_all_deleting_for_bucket.assert_called_once_with(BUCKET_ID)

    def test_returns_404_when_the_database_does_not_exist(self):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                KnowledgeService.delete_database(database=DATABASE)

        assert exc_info.value.status_code == 404
        bucket_cls.mark_deleting.assert_not_called()

    def test_refuses_to_delete_an_auto_sync_database(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(auto_sync=True)

            with pytest.raises(HTTPException) as exc_info:
                KnowledgeService.delete_database(database=DATABASE)

        assert exc_info.value.status_code == 403
        bucket_cls.mark_deleting.assert_not_called()
        namespace_cls.mark_all_deleting_for_bucket.assert_not_called()

    @pytest.mark.parametrize("legacy_ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    def test_refuses_to_delete_a_legacy_database(self, legacy_ingestor):
        with patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls:
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(ingestor=legacy_ingestor)

            with pytest.raises(HTTPException) as exc_info:
                KnowledgeService.delete_database(database=DATABASE)

        assert exc_info.value.status_code == 403
        bucket_cls.mark_deleting.assert_not_called()


class TestDeleteNamespace:
    def test_marks_only_the_namespace_deleting(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(
                id=NAMESPACE_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE
            )

            KnowledgeService.delete_namespace(database=DATABASE, namespace=NAMESPACE)

        namespace_cls.mark_deleting.assert_called_once_with(NAMESPACE_ID)
        namespace_cls.mark_all_deleting_for_bucket.assert_not_called()
        bucket_cls.mark_deleting.assert_not_called()

    def test_returns_404_when_the_namespace_does_not_exist(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespace_by_bucket_and_name.side_effect = DoesNotExist

            with pytest.raises(HTTPException) as exc_info:
                KnowledgeService.delete_namespace(database=DATABASE, namespace=NAMESPACE)

        assert exc_info.value.status_code == 404
        namespace_cls.mark_deleting.assert_not_called()

    def test_refuses_a_namespace_delete_on_an_auto_sync_database(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(auto_sync=True)

            with pytest.raises(HTTPException) as exc_info:
                KnowledgeService.delete_namespace(database=DATABASE, namespace=NAMESPACE)

        assert exc_info.value.status_code == 403
        namespace_cls.mark_deleting.assert_not_called()

    @pytest.mark.parametrize("legacy_ingestor", [IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value])
    def test_allows_namespace_deletion_inside_a_legacy_database(self, legacy_ingestor):
        """The legacy default_rag/shared_rag databases must stay, but their namespaces remain deletable."""
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket(ingestor=legacy_ingestor)
            namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(
                id=NAMESPACE_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE
            )

            KnowledgeService.delete_namespace(database=DATABASE, namespace=NAMESPACE)

        namespace_cls.mark_deleting.assert_called_once_with(NAMESPACE_ID)


class TestDeleteRevokesAccess:
    def test_revokes_the_database_and_every_namespace_rule_and_role(self):
        """Grants outlive the rows they name unless delete revokes them, leaving inert rules to pile up."""
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.RoleEntity") as role_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespaces_by_bucket.return_value = [MagicMock(namespace_name=NAMESPACE)]

            KnowledgeService.delete_database(database=DATABASE)

        revoked = tenant_cls.revoke_access_rule_from_all_tenants.call_args.args[0]
        assert set(revoked) == {
            f"aihub.user.knowledge.{DATABASE}",
            f"aihub.admin.knowledge.{DATABASE}",
            f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}",
            f"aihub.admin.knowledge.{DATABASE}.{NAMESPACE}",
        }
        deleted_roles = {call.args[0] for call in role_cls.delete_role_from_all_tenants.call_args_list}
        assert deleted_roles == {"KnowledgeResearchdocsAdmin", "KnowledgeResearchdocsReportsAdmin"}

    def test_a_revoke_failure_does_not_block_the_teardown_flags(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.RoleEntity"),
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespaces_by_bucket.return_value = []
            tenant_cls.revoke_access_rule_from_all_tenants.side_effect = RuntimeError("tenant store unavailable")

            KnowledgeService.delete_database(database=DATABASE)

        bucket_cls.mark_deleting.assert_called_once_with(BUCKET_ID)

    def test_a_namespace_delete_revokes_only_that_namespace(self):
        with (
            patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_cls,
            patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_cls,
            patch(f"{_SERVICE_MODULE}.TenantMetadataEntity") as tenant_cls,
            patch(f"{_SERVICE_MODULE}.RoleEntity") as role_cls,
        ):
            bucket_cls.get_bucket_by_db_name.return_value = _bucket()
            namespace_cls.get_namespace_by_bucket_and_name.return_value = MagicMock(
                id=NAMESPACE_ID, namespace_name=NAMESPACE, folder_name=NAMESPACE
            )

            KnowledgeService.delete_namespace(database=DATABASE, namespace=NAMESPACE)

        assert set(tenant_cls.revoke_access_rule_from_all_tenants.call_args.args[0]) == {
            f"aihub.user.knowledge.{DATABASE}.{NAMESPACE}",
            f"aihub.admin.knowledge.{DATABASE}.{NAMESPACE}",
        }
        role_cls.delete_role_from_all_tenants.assert_called_once_with("KnowledgeResearchdocsReportsAdmin")
