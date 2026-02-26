from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from aihub_api.routes.agent.AgentFileUploadService import AgentFileUploadService


@pytest.fixture
def s3_client():
    return MagicMock()


@pytest.fixture
def s3_public_client():
    return MagicMock()


@pytest.fixture
def service(s3_client, s3_public_client):
    return AgentFileUploadService(s3_client, s3_public_client)


class TestEnsureBucketExists:
    def test_bucket_already_exists(self, service, s3_client):
        s3_client.head_bucket.return_value = {}

        service.ensure_bucket_exists()

        s3_client.head_bucket.assert_called_once_with(Bucket="agent-files")
        s3_client.create_bucket.assert_not_called()

    def test_creates_bucket_when_not_found(self, service, s3_client):
        error_response = {"Error": {"Code": "404"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        service.ensure_bucket_exists()

        s3_client.create_bucket.assert_called_once_with(Bucket="agent-files")

    def test_sets_lifecycle_on_new_bucket(self, service, s3_client):
        error_response = {"Error": {"Code": "404"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        service.ensure_bucket_exists()

        s3_client.put_bucket_lifecycle_configuration.assert_called_once()
        lifecycle = s3_client.put_bucket_lifecycle_configuration.call_args[1]["LifecycleConfiguration"]
        rule = lifecycle["Rules"][0]
        assert rule["Status"] == "Enabled"
        assert rule["Expiration"]["Days"] == 7

    def test_skips_lifecycle_when_bucket_exists(self, service, s3_client):
        s3_client.head_bucket.return_value = {}

        service.ensure_bucket_exists()

        s3_client.put_bucket_lifecycle_configuration.assert_not_called()

    def test_creates_bucket_nosuchbucket(self, service, s3_client):
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        service.ensure_bucket_exists()

        s3_client.create_bucket.assert_called_once_with(Bucket="agent-files")

    def test_propagates_unexpected_error(self, service, s3_client):
        error_response = {"Error": {"Code": "403"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        with pytest.raises(ClientError):
            service.ensure_bucket_exists()


class TestS3Key:
    def test_constructs_key_with_path_isolation(self):
        assert (
            AgentFileUploadService.s3_key("MyAgent", "inst-1", "abc-123", "report.pdf")
            == "MyAgent/inst-1/abc-123/report.pdf"
        )

    def test_sanitizes_agent_class_with_traversal(self):
        assert (
            AgentFileUploadService.s3_key("../OtherAgent", "inst-1", "abc-123", "f.pdf")
            == "__OtherAgent/inst-1/abc-123/f.pdf"
        )


class TestGenerateUploadUrl:
    def test_returns_url_and_file_id(self, service, s3_public_client):
        s3_public_client.generate_presigned_url.return_value = "https://s3/presigned"

        url, file_id = service.generate_upload_url("MyAgent", "inst-1", "application/pdf", "report.pdf")

        assert url == "https://s3/presigned"
        assert len(file_id) == 36  # UUID4 format

    def test_presigned_url_uses_put_object(self, service, s3_public_client):
        s3_public_client.generate_presigned_url.return_value = "https://s3/presigned"

        service.generate_upload_url("MyAgent", "inst-1", "image/png", "image.png")

        call_args = s3_public_client.generate_presigned_url.call_args
        assert call_args[0][0] == "put_object"
        params = call_args[1]["Params"]
        assert params["ContentType"] == "image/png"
        assert params["Key"].endswith("/image.png")

    def test_key_includes_agent_path(self, service, s3_public_client):
        s3_public_client.generate_presigned_url.return_value = "https://s3/presigned"

        service.generate_upload_url("MyAgent", "inst-1", "text/plain", "notes.txt")

        params = s3_public_client.generate_presigned_url.call_args[1]["Params"]
        assert params["Key"].startswith("MyAgent/inst-1/")
        assert params["Key"].endswith("/notes.txt")


class TestVerifyFileExists:
    def test_returns_true_when_file_exists(self, service, s3_client):
        s3_client.head_object.return_value = {}

        assert service.verify_file_exists("MyAgent", "inst-1", "abc-123", "report.pdf") is True

    def test_returns_false_when_not_found(self, service, s3_client):
        error_response = {"Error": {"Code": "404"}}
        s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")

        assert service.verify_file_exists("MyAgent", "inst-1", "abc-123", "report.pdf") is False

    def test_returns_false_for_nosuchkey(self, service, s3_client):
        error_response = {"Error": {"Code": "NoSuchKey"}}
        s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")

        assert service.verify_file_exists("MyAgent", "inst-1", "abc-123", "report.pdf") is False

    def test_propagates_unexpected_error(self, service, s3_client):
        error_response = {"Error": {"Code": "403"}}
        s3_client.head_object.side_effect = ClientError(error_response, "HeadObject")

        with pytest.raises(ClientError):
            service.verify_file_exists("MyAgent", "inst-1", "abc-123", "report.pdf")
