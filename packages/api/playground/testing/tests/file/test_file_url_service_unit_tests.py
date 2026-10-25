from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker

from swiss_ai_hub.api.routes.file.file_service import FileService

_SERVICE_MODULE = "swiss_ai_hub.api.routes.file.file_service"

BUCKET = "contracts"
DB = "contracts-db"
FOLDER = "legal-folder"
NAMESPACE = "legal"
AGENT_FILE = "rag/my-agent/0b6c9a52-3f7e-4d8a-9c1e-2f4b5a6d7e8f/report.pdf"


def _access(*rules: str) -> AccessChecker:
    return AccessChecker(user_access_rules=list(rules), tenant_access_rules=["aihub.user.>", "aihub.admin.>"])


@pytest.fixture
def s3_service() -> MagicMock:
    service = MagicMock()
    service.generate_sas_url.return_value = "https://public/signed"
    return service


@pytest.fixture
def knowledge() -> MagicMock:
    bucket = MagicMock(id="bucket-id", db_name=DB, deleting=False)
    namespace = MagicMock(namespace_name=NAMESPACE, deleting=False)
    with (
        patch(f"{_SERVICE_MODULE}.BucketEntity") as bucket_entity,
        patch(f"{_SERVICE_MODULE}.NamespaceEntity") as namespace_entity,
        patch(f"{_SERVICE_MODULE}.KnowledgeService.non_browsable_database_names", return_value=frozenset({"aihub"})),
    ):
        bucket_entity.get_bucket_by_bucket_name.return_value = bucket
        namespace_entity.get_namespace_by_bucket_and_folder.return_value = namespace
        yield MagicMock(
            bucket=bucket, namespace=namespace, bucket_entity=bucket_entity, namespace_entity=namespace_entity
        )


def _assert_forbidden(access: AccessChecker, container: str, file_path: str, s3_service: MagicMock) -> None:
    with pytest.raises(HTTPException) as raised:
        FileService.get_file_url(access, container, file_path, s3_service)
    assert raised.value.status_code == 403
    s3_service.generate_sas_url.assert_not_called()


class TestKnowledgeFiles:
    @pytest.mark.parametrize(
        "file_path",
        [f"{FOLDER}/report.pdf", f"{FOLDER}/sub/__figures__/report_pdf/figure_ab12.png"],
        ids=["source", "figure"],
    )
    def test_namespace_reader_gets_a_url(self, knowledge, s3_service, file_path):
        url = FileService.get_file_url(_access(f"aihub.user.knowledge.{DB}.{NAMESPACE}"), BUCKET, file_path, s3_service)

        assert url == "https://public/signed"
        s3_service.generate_sas_url.assert_called_once_with(BUCKET, file_path)
        knowledge.namespace_entity.get_namespace_by_bucket_and_folder.assert_called_once_with("bucket-id", FOLDER)

    def test_reader_of_another_namespace_is_refused(self, knowledge, s3_service):
        _assert_forbidden(_access(f"aihub.user.knowledge.{DB}.other"), BUCKET, f"{FOLDER}/report.pdf", s3_service)

    def test_reader_of_another_database_is_refused(self, knowledge, s3_service):
        _assert_forbidden(_access("aihub.user.knowledge.other-db.>"), BUCKET, f"{FOLDER}/report.pdf", s3_service)

    @pytest.mark.parametrize("container", ["backups", "dagster", "langfuse", "other-tenant-bucket"])
    def test_bucket_without_knowledge_database_is_refused(self, knowledge, s3_service, container):
        knowledge.bucket_entity.get_bucket_by_bucket_name.side_effect = DoesNotExist
        _assert_forbidden(_access("aihub.user.>"), container, f"{FOLDER}/report.pdf", s3_service)

    def test_folder_without_namespace_is_refused(self, knowledge, s3_service):
        knowledge.namespace_entity.get_namespace_by_bucket_and_folder.side_effect = DoesNotExist
        _assert_forbidden(_access("aihub.user.>"), BUCKET, "unknown/report.pdf", s3_service)

    def test_non_browsable_database_is_refused(self, knowledge, s3_service):
        knowledge.bucket.db_name = "aihub"
        _assert_forbidden(_access("aihub.user.>"), BUCKET, f"{FOLDER}/report.pdf", s3_service)

    def test_database_being_deleted_is_refused(self, knowledge, s3_service):
        knowledge.bucket.deleting = True
        _assert_forbidden(_access("aihub.user.>"), BUCKET, f"{FOLDER}/report.pdf", s3_service)

    def test_object_outside_any_folder_is_refused(self, knowledge, s3_service):
        _assert_forbidden(_access("aihub.user.>"), BUCKET, "report.pdf", s3_service)

    @pytest.mark.parametrize(
        "file_path",
        [f"{FOLDER}/../secret/report.pdf", f"{FOLDER}//report.pdf", f"{FOLDER}/./report.pdf", f"{FOLDER}/"],
    )
    def test_path_with_traversal_or_empty_segment_is_refused(self, knowledge, s3_service, file_path):
        _assert_forbidden(_access("aihub.user.>"), BUCKET, file_path, s3_service)


class TestAgentFiles:
    def test_agent_user_gets_a_url(self, s3_service):
        url = FileService.get_file_url(_access("aihub.user.agent.rag.my-agent"), "agent-files", AGENT_FILE, s3_service)

        assert url == "https://public/signed"
        s3_service.generate_sas_url.assert_called_once_with("agent-files", AGENT_FILE)

    def test_user_of_another_agent_is_refused(self, s3_service):
        _assert_forbidden(_access("aihub.user.agent.rag.other-agent"), "agent-files", AGENT_FILE, s3_service)

    @pytest.mark.parametrize("file_path", ["rag/my-agent/report.pdf", f"{AGENT_FILE}/extra"])
    def test_key_outside_the_agent_file_layout_is_refused(self, s3_service, file_path):
        _assert_forbidden(_access("aihub.user.>"), "agent-files", file_path, s3_service)


class TestAnonymousLinkSignature:
    @pytest.fixture
    def signing_s3_service(self, s3_service) -> MagicMock:
        s3_service.get_url_signing_secret.return_value = "link-key"
        return s3_service

    def test_signed_link_verifies(self, signing_s3_service):
        link = FileService.create_anonymous_url("https://api/redirect", BUCKET, "a/b.pdf", signing_s3_service)
        expires = int(link.split("expires=")[1].split("&")[0])
        signature = link.split("signature=")[1]

        FileService.get_anonymous_file_url(BUCKET, "a/b.pdf", expires, signature, signing_s3_service)

        signing_s3_service.generate_sas_url.assert_called_once()

    def test_field_boundaries_are_part_of_the_signature(self, signing_s3_service):
        expires = 4_102_444_800
        signature = FileService._generate_internal_signature("ab", "c/d.pdf", expires, signing_s3_service)

        assert signature != FileService._generate_internal_signature("a", "bc/d.pdf", expires, signing_s3_service)
        with pytest.raises(HTTPException) as raised:
            FileService.get_anonymous_file_url("a", "bc/d.pdf", expires, signature, signing_s3_service)
        assert raised.value.status_code == 401
