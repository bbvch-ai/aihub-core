from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from aihub_lib.infrastructure.s3.AgentFileUploadService import AgentFileUploadService


@pytest.fixture
def s3_client():
    return MagicMock()


@pytest.fixture
def s3_public_client():
    return MagicMock()


@pytest.fixture
def s3_settings():
    return MagicMock()


@pytest.fixture
def service(s3_client, s3_public_client, s3_settings):
    return AgentFileUploadService(s3_client, s3_public_client, s3_settings)


class TestEnsureBucketExists:
    def test_bucket_already_exists(self, service, s3_client):
        s3_client.head_bucket.return_value = {}

        service._ensure_bucket_exists("my-bucket")

        s3_client.head_bucket.assert_called_once_with(Bucket="my-bucket")
        s3_client.create_bucket.assert_not_called()

    def test_creates_bucket_when_not_found(self, service, s3_client):
        error_response = {"Error": {"Code": "404"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        service._ensure_bucket_exists("my-bucket")

        s3_client.create_bucket.assert_called_once_with(Bucket="my-bucket")

    def test_creates_bucket_nosuchbucket(self, service, s3_client):
        error_response = {"Error": {"Code": "NoSuchBucket"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        service._ensure_bucket_exists("my-bucket")

        s3_client.create_bucket.assert_called_once_with(Bucket="my-bucket")

    def test_propagates_unexpected_error(self, service, s3_client):
        error_response = {"Error": {"Code": "403"}}
        s3_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        with pytest.raises(ClientError):
            service._ensure_bucket_exists("my-bucket")

    def test_caches_known_buckets(self, service, s3_client):
        s3_client.head_bucket.return_value = {}

        service._ensure_bucket_exists("my-bucket")
        service._ensure_bucket_exists("my-bucket")

        s3_client.head_bucket.assert_called_once()


class TestS3Key:
    def test_constructs_key_with_filename(self):
        assert AgentFileUploadService.s3_key("abc-123", "report.pdf") == "abc-123/report.pdf"


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

    def test_uses_correct_bucket(self, service, s3_public_client, s3_client):
        s3_client.head_bucket.return_value = {}
        s3_public_client.generate_presigned_url.return_value = "https://s3/presigned"

        service.generate_upload_url("MyAgent", "inst-1", "text/plain", "notes.txt")

        params = s3_public_client.generate_presigned_url.call_args[1]["Params"]
        assert params["Bucket"] == "agent-files-myagent-inst-1"


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

    def test_uses_key_with_filename(self, service, s3_client):
        s3_client.head_object.return_value = {}

        service.verify_file_exists("MyAgent", "inst-1", "abc-123", "report.pdf")

        s3_client.head_object.assert_called_once_with(Bucket="agent-files-myagent-inst-1", Key="abc-123/report.pdf")


class TestDeleteFile:
    def test_deletes_object_from_correct_bucket_and_key(self, service, s3_client):
        service.delete_file("MyAgent", "inst-1", "abc-123", "report.pdf")

        s3_client.delete_object.assert_called_once_with(Bucket="agent-files-myagent-inst-1", Key="abc-123/report.pdf")

    def test_propagates_unexpected_error(self, service, s3_client):
        error_response = {"Error": {"Code": "403"}}
        s3_client.delete_object.side_effect = ClientError(error_response, "DeleteObject")

        with pytest.raises(ClientError):
            service.delete_file("MyAgent", "inst-1", "abc-123", "report.pdf")
