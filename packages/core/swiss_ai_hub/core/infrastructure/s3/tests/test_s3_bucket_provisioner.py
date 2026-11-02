from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from swiss_ai_hub.core.infrastructure.s3.s3_bucket_provisioner import S3BucketProvisioner

BUCKET = "researchdocs"


def _missing_bucket_error(code: str = "404") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "not found"}}, "HeadBucket")


class TestBucketExists:
    def test_reports_an_existing_bucket(self):
        assert S3BucketProvisioner.bucket_exists(MagicMock(), BUCKET) is True

    @pytest.mark.parametrize("code", ["404", "NoSuchBucket"])
    def test_reports_a_missing_bucket(self, code):
        client = MagicMock()
        client.head_bucket.side_effect = _missing_bucket_error(code)

        assert S3BucketProvisioner.bucket_exists(client, BUCKET) is False

    def test_propagates_any_other_error_rather_than_calling_it_missing(self):
        """A 403 means the bucket is there but unreachable; treating it as free would create over it."""
        client = MagicMock()
        client.head_bucket.side_effect = _missing_bucket_error("403")

        with pytest.raises(ClientError):
            S3BucketProvisioner.bucket_exists(client, BUCKET)


class TestEnsureBucketWithCors:
    def test_creates_the_bucket_when_missing_and_writes_the_shared_ruleset(self):
        client = MagicMock()
        client.head_bucket.side_effect = _missing_bucket_error()

        S3BucketProvisioner.ensure_bucket_with_cors(client, BUCKET)

        client.create_bucket.assert_called_once_with(Bucket=BUCKET)
        client.put_bucket_cors.assert_called_once_with(
            Bucket=BUCKET, CORSConfiguration={"CORSRules": S3BucketProvisioner.CORS_RULES}
        )

    def test_reapplies_cors_without_recreating_an_existing_bucket(self):
        """put_bucket_cors replaces the whole config, so whoever writes last must write the full ruleset."""
        client = MagicMock()

        S3BucketProvisioner.ensure_bucket_with_cors(client, BUCKET)

        client.create_bucket.assert_not_called()
        client.put_bucket_cors.assert_called_once()

    def test_the_ruleset_carries_what_a_presigned_browser_upload_needs(self):
        rule = S3BucketProvisioner.CORS_RULES[0]

        assert "x-amz-content-sha256" in rule["AllowedHeaders"]
        assert {"GET", "PUT", "POST", "DELETE", "HEAD"} <= set(rule["AllowedMethods"])
        assert "ETag" in rule["ExposeHeaders"]
