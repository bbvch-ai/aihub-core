import pytest
from pydantic import ValidationError

from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile

VALID_UUID4 = "550e8400-e29b-41d4-a716-446655440000"


class TestUserUploadedFile:
    def test_create_with_file_id(self):
        f = UserUploadedFile(filename="report.pdf", file_type="application/pdf", file_id=VALID_UUID4)
        assert f.filename == "report.pdf"
        assert f.file_type == "application/pdf"
        assert f.file_id == VALID_UUID4

    def test_rejects_non_uuid4_file_id(self):
        with pytest.raises(ValidationError):
            UserUploadedFile(filename="report.pdf", file_type="application/pdf", file_id="not-a-uuid")

    def test_rejects_s3_bucket_field(self):
        """The old s3_bucket field must not be accepted — this is the IDOR fix."""
        f = UserUploadedFile(
            filename="report.pdf",
            file_type="application/pdf",
            file_id=VALID_UUID4,
            s3_bucket="evil-bucket",  # type: ignore[call-arg]
        )
        assert not hasattr(f, "s3_bucket") or "s3_bucket" not in f.model_fields

    def test_rejects_s3_key_field(self):
        """The old s3_key field must not be accepted — this is the IDOR fix."""
        f = UserUploadedFile(
            filename="report.pdf",
            file_type="application/pdf",
            file_id=VALID_UUID4,
            s3_key="secret/file.pdf",  # type: ignore[call-arg]
        )
        assert not hasattr(f, "s3_key") or "s3_key" not in f.model_fields

    def test_file_id_required(self):
        with pytest.raises(ValidationError):
            UserUploadedFile(filename="report.pdf", file_type="application/pdf")  # type: ignore[call-arg]

    def test_resolve_s3_location(self):
        f = UserUploadedFile(filename="report.pdf", file_type="application/pdf", file_id=VALID_UUID4)
        bucket, key = f.resolve_s3_location("MyAgent", "inst-1")
        assert bucket == "agent-files-myagent-inst-1"
        assert key == f"{VALID_UUID4}/report.pdf"

    def test_serialization_roundtrip(self):
        f = UserUploadedFile(filename="image.png", file_type="image/png", file_id=VALID_UUID4)
        data = f.model_dump()
        assert data == {"filename": "image.png", "file_type": "image/png", "file_id": VALID_UUID4}
        restored = UserUploadedFile.model_validate(data)
        assert restored == f
