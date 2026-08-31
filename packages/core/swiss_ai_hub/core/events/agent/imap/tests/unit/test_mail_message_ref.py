import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.imap.mail_message_ref import MailMessageRef

VALID_UUID4 = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"


class TestMailMessageRef:
    def test_defaults_to_the_rfc822_content_type(self):
        ref = MailMessageRef(filename="42.eml", file_id=VALID_UUID4, size_bytes=64)
        assert ref.content_type == "message/rfc822"

    @pytest.mark.parametrize("filename", ["../secret", "..\\secret", "a/../b", "..", "a/b", "a\\b"])
    def test_rejects_path_traversal_and_separators(self, filename: str):
        """The filename is built from the IMAP UID, so it is always digits — the pattern is what makes that
        an enforced invariant rather than an assumption, since the name reaches an S3 key and a
        Content-Disposition header."""
        with pytest.raises(ValidationError):
            MailMessageRef(filename=filename, file_id=VALID_UUID4, size_bytes=64)

    def test_resolve_s3_location_shares_the_uploaded_file_layout(self):
        ref = MailMessageRef(filename="42.eml", file_id=VALID_UUID4, size_bytes=64)
        bucket, key = ref.resolve_s3_location("MyAgent", "inst-1")
        assert bucket == "agent-files"
        assert key == f"MyAgent/inst-1/{VALID_UUID4}/42.eml"
