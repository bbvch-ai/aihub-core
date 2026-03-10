import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.nats.events.user.UserUploadedFile import UserUploadedFile

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

    def test_file_id_required(self):
        with pytest.raises(ValidationError):
            UserUploadedFile(filename="report.pdf", file_type="application/pdf")  # type: ignore[call-arg]

    def test_resolve_s3_location(self):
        f = UserUploadedFile(filename="report.pdf", file_type="application/pdf", file_id=VALID_UUID4)
        bucket, key = f.resolve_s3_location("MyAgent", "inst-1")
        assert bucket == "agent-files"
        assert key == f"MyAgent/inst-1/{VALID_UUID4}/report.pdf"

    def test_serialization_roundtrip(self):
        f = UserUploadedFile(filename="image.png", file_type="image/png", file_id=VALID_UUID4)
        data = f.model_dump()
        assert data == {"filename": "image.png", "file_type": "image/png", "file_id": VALID_UUID4}
        restored = UserUploadedFile.model_validate(data)
        assert restored == f

    def test_rejects_filename_with_forward_slash(self):
        with pytest.raises(ValidationError):
            UserUploadedFile(filename="../../etc/passwd", file_type="text/plain", file_id=VALID_UUID4)

    def test_rejects_filename_with_backslash(self):
        with pytest.raises(ValidationError):
            UserUploadedFile(filename="..\\..\\secret.pdf", file_type="application/pdf", file_id=VALID_UUID4)


class TestSanitizePathSegment:
    def test_replaces_forward_slashes(self):
        assert UserUploadedFile._sanitize_path_segment("a/b/c") == "a_b_c"

    def test_replaces_backslashes(self):
        assert UserUploadedFile._sanitize_path_segment("a\\b\\c") == "a_b_c"

    def test_replaces_dot_dot_traversal(self):
        assert UserUploadedFile._sanitize_path_segment("..") == "_"

    def test_replaces_embedded_dot_dot(self):
        assert UserUploadedFile._sanitize_path_segment("foo..bar") == "foo_bar"

    def test_leaves_clean_values_unchanged(self):
        assert UserUploadedFile._sanitize_path_segment("MyAgent") == "MyAgent"
        assert UserUploadedFile._sanitize_path_segment("inst-1") == "inst-1"
