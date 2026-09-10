import email
import logging
from email.message import EmailMessage
from email.policy import default as default_policy
from typing import TYPE_CHECKING, Any, ClassVar

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.imap.mail_parser import MailParser
from swiss_ai_hub.core.imap.parsed_message import ParsedMessage
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem

logger = logging.getLogger(__name__)

SUBJECT = "subject"

# Every other loader in this package returns markdown, so a mail has to as well or `.eml` becomes the one file type
# with a different contract. 1MB of decoded body is far past any real mail and still bounded.
_MAX_BODY_BYTES = 1_000_000

# Refuses every attachment at parse time. `MailParser` drops a part whose payload exceeds this, so the smallest
# possible value is what keeps base64 out of the extracted text entirely — the failure mode that makes
# `MarkItDownLoader` unusable for `.eml`. Attachment *names* are still listed; only the bytes are discarded.
_REFUSE_ALL_ATTACHMENTS = 1

# The inventory is attacker-controlled text sitting in the same untrimmed part of the prompt as the subject, which is
# bounded for exactly that reason. A filename can also carry newlines, which would let a sender forge markdown
# structure in what the model reads as the document.
MAX_ATTACHMENT_NAMES = 20
MAX_ATTACHMENT_NAME_CHARACTERS = 120


class EmlLoader(BaseReader):
    """Reads an RFC822 `.eml` file into markdown, with the subject as the title.

    `MarkItDownLoader` also claims `.eml`, but it emits the raw message source — MIME boundaries, transfer-encoding
    headers, unconverted HTML and base64 attachment payloads — which is neither markdown nor separable into a
    subject and a body. `MailParser` splits the message correctly but yields plain text. This composes the two: the
    parser does the MIME work, and an HTML-only body is converted by MarkItDown, whose standalone-HTML conversion is
    good. `.msg` (Outlook's binary format, which the stdlib `email` module cannot read) stays with MarkItDown.
    """

    SUPPORTED_EXTENSIONS: ClassVar[list[str]] = ["eml"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._html_converter = MarkItDownLoader()

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        *args,
        **kwargs,
    ) -> list[Document]:
        raise RuntimeError("EmlLoader reads bytes, not paths; use aload_data_from_bytes()")

    async def aload_data_from_bytes(
        self,
        content: bytes,
        filename: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
        embed_base64: bool = False,
    ) -> list[Document]:
        """Parse the message and render it as one markdown document."""
        message = email.message_from_bytes(content, policy=default_policy)
        parsed = MailParser.parse_message(
            message_id=filename,
            message=message,
            max_body_bytes=_MAX_BODY_BYTES,
            max_attachment_bytes=_REFUSE_ALL_ATTACHMENTS,
            raw=b"",
        )
        body = await self._body_as_markdown(parsed)
        attachment_names = self._attachment_names(message)

        # No NUMBER_OF_PAGES: a mail has no page count, and reporting 1 would be inventing one.
        metadata: dict[str, Any] = {SUBJECT: parsed.subject, "parser": "eml"}
        if extra_info:
            metadata.update(extra_info)

        return [Document(text=self._render(parsed, body, attachment_names), extra_info=metadata)]

    async def _body_as_markdown(self, parsed: ParsedMessage) -> str:
        """Prefer the plain-text part; convert the HTML alternative only when there is no other body.

        A `text/plain` part is already close to markdown and is what the sender wrote, so converting the HTML
        alternative instead would substitute a rendering for the original.
        """
        if parsed.body_text:
            return parsed.body_text.strip()
        if not parsed.body_html:
            return ""

        documents = await self._html_converter.aload_data_from_bytes(
            content=parsed.body_html.encode("utf-8"),
            filename="body.html",
            include_images=False,
        )
        return "\n\n".join(document.text for document in documents).strip()

    @staticmethod
    def _attachment_names(message: EmailMessage) -> list[str]:
        """Collect attachment filenames without decoding a single payload.

        `MailParser` is asked to discard attachment bytes outright, which also loses their names — and a classifier
        benefits from knowing an invoice PDF was attached. Reading `get_filename()` off each part costs nothing and
        cannot pull a base64 payload into the output, whereas raising the parser's limit to keep the names would
        decode every attachment just to throw it away.
        """
        names: list[str] = []
        for part in message.walk():
            if part.is_multipart():
                continue
            filename = part.get_filename()
            if filename or part.get_content_disposition() == "attachment":
                names.append(EmlLoader._safe_name(filename or "attachment"))
            if len(names) == MAX_ATTACHMENT_NAMES:
                break
        return names

    @staticmethod
    def _safe_name(filename: str) -> str:
        """Collapse whitespace and cap the length, so a filename cannot forge structure in the rendered markdown."""
        return " ".join(filename.split())[:MAX_ATTACHMENT_NAME_CHARACTERS]

    @staticmethod
    def _render(parsed: ParsedMessage, body: str, attachment_names: list[str]) -> str:
        """Subject as the H1, so a caller with no email-specific knowledge still finds the title where it expects."""
        lines = [f"# {parsed.subject}".rstrip(), ""]
        if parsed.sender:
            lines.append(f"**From:** {parsed.sender}")
        if parsed.date:
            lines.append(f"**Date:** {parsed.date:%Y-%m-%d}")
        if attachment_names:
            lines.append(f"**Attachments:** {', '.join(attachment_names)}")
        lines += ["", body]
        return "\n".join(lines).strip()
