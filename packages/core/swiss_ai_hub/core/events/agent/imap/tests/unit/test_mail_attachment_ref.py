import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.imap.mail_attachment_ref import MailAttachmentRef

VALID_UUID4 = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"


class TestMailAttachmentRef:
    def test_accepts_plain_filename(self):
        ref = MailAttachmentRef(
            filename="report.pdf", content_type="application/pdf", file_id=VALID_UUID4, size_bytes=8
        )
        assert ref.filename == "report.pdf"

    @pytest.mark.parametrize("filename", ["../secret", "..\\secret", "a/../b", "..", "a/b", "a\\b"])
    def test_rejects_path_traversal_and_separators(self, filename: str):
        with pytest.raises(ValidationError):
            MailAttachmentRef(filename=filename, content_type="application/pdf", file_id=VALID_UUID4, size_bytes=8)

    def test_resolve_s3_location_matches_uploaded_file_layout(self):
        ref = MailAttachmentRef(
            filename="report.pdf", content_type="application/pdf", file_id=VALID_UUID4, size_bytes=8
        )
        bucket, key = ref.resolve_s3_location("MyAgent", "inst-1")
        assert bucket == "agent-files"
        assert key == f"MyAgent/inst-1/{VALID_UUID4}/report.pdf"
