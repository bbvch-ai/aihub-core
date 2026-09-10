import logging
import re

from swiss_ai_hub.core.events.agent import MailAttachmentRef
from swiss_ai_hub.core.generative_ai import DocumentLoaderSelector
from swiss_ai_hub.core.imap import DraftEmailSettings

from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.mail_store import MailStore

logger = logging.getLogger(__name__)

# A parse that yields only figure references produced no readable text. MinerU emits these for an image it could
# find no words in, so stripping them is what separates "a scanned invoice" from "a photo".
_MARKDOWN_ARTEFACTS = re.compile(r"!\[[^\]]*\]\([^)]*\)|<figure>.*?</figure>", re.DOTALL)

# Below this many characters an extraction carries nothing a reply could be grounded in — a stray page number, a
# watermark fragment. Treated as textless rather than fed to the model as if it were content.
_MINIMUM_USEFUL_CHARACTERS = 16


class AttachmentTextExtractor:
    """Reads the text out of a message's attachments so a drafted reply can be grounded in them.

    Bounded on purpose, in three ways, because every attachment read costs a document-parser round trip and the run
    holds the mailbox lease while it happens: attachments below `min_attachment_bytes` are never fetched, only the
    largest `max_attachments_per_message` are read, and each extraction is cut to `attachment_char_limit`.

    The size floor is not premature optimisation. `MailParser` collects every MIME part carrying a filename, so the
    logo in a corporate signature arrives here as an attachment; without the floor a routine business mail would
    spend a parser round trip on it and get nothing back.

    Never raises. An attachment that cannot be read is reported as unreadable and the reply is drafted without it —
    losing the whole run over one malformed PDF would be a far worse trade.
    """

    @staticmethod
    async def extract(
        attachments: list[MailAttachmentRef],
        draft: DraftEmailSettings,
        agent_class: str,
        agent_id: str,
    ) -> list[ExtractedAttachment]:
        """Read the eligible attachments, largest first, returning one outcome per attachment considered."""
        candidates = AttachmentTextExtractor._candidates(attachments, draft)
        return [
            await AttachmentTextExtractor._read(candidate, draft, agent_class, agent_id) for candidate in candidates
        ]

    @staticmethod
    def _candidates(attachments: list[MailAttachmentRef], draft: DraftEmailSettings) -> list[MailAttachmentRef]:
        """Pick which attachments are worth a round trip, from the reference alone — before any byte is fetched.

        Largest first, because when a message carries more attachments than the cap, size is the only signal
        available here about which one is the substantive document. The MIME disposition that would say so directly
        was discarded when the message was parsed, and the bytes are in S3 by now.
        """
        big_enough = [ref for ref in attachments if ref.size_bytes >= draft.min_attachment_bytes]
        for ref in attachments:
            if ref.size_bytes < draft.min_attachment_bytes:
                logger.info(
                    "[attachments] skipping %r (%d bytes) — below the %d-byte floor, most likely a signature image",
                    ref.filename,
                    ref.size_bytes,
                    draft.min_attachment_bytes,
                )

        ordered = sorted(big_enough, key=lambda ref: ref.size_bytes, reverse=True)
        selected = ordered[: draft.max_attachments_per_message]
        for ref in ordered[draft.max_attachments_per_message :]:
            logger.info(
                "[attachments] skipping %r — more than %d attachment(s) on one message",
                ref.filename,
                draft.max_attachments_per_message,
            )
        return selected

    @staticmethod
    async def _read(
        ref: MailAttachmentRef,
        draft: DraftEmailSettings,
        agent_class: str,
        agent_id: str,
    ) -> ExtractedAttachment:
        """Read one attachment, mapping every failure mode onto an outcome rather than an exception."""
        loader = DocumentLoaderSelector.for_file(ref.filename, ref.content_type)
        if loader is None:
            logger.info("[attachments] no loader handles %r (%s)", ref.filename, ref.content_type)
            return AttachmentTextExtractor._unreadable(ref, "this file type cannot be read")

        try:
            content = await MailStore.load_attachment(ref, agent_class=agent_class, agent_id=agent_id)
            # include_images=False keeps this to text: the loaders demand an fsspec filesystem to write extracted
            # images to, and a reply prompt has no use for them.
            documents = await loader.aload_data_from_bytes(
                content=content,
                filename=ref.filename,
                include_images=False,
            )
        except Exception:
            logger.warning("[attachments] could not read %r — drafting without it", ref.filename, exc_info=True)
            return AttachmentTextExtractor._unreadable(ref, "this attachment could not be read")

        text = AttachmentTextExtractor._meaningful_text("\n\n".join(document.text for document in documents))
        if not text:
            logger.info("[attachments] %r holds no readable text", ref.filename)
            return ExtractedAttachment(
                filename=ref.filename,
                content_type=ref.content_type,
                size_bytes=ref.size_bytes,
                outcome=AttachmentOutcome.NO_TEXT,
                detail="no text could be extracted",
            )

        return ExtractedAttachment(
            filename=ref.filename,
            content_type=ref.content_type,
            size_bytes=ref.size_bytes,
            outcome=AttachmentOutcome.TEXT,
            text=text[: draft.attachment_char_limit],
        )

    @staticmethod
    def _meaningful_text(raw: str) -> str:
        """Return the extraction if it holds actual prose, else empty.

        A parse of a textless image comes back either empty or as bare figure references, so both have to count as
        textless — otherwise `![](image.jpg)` would reach the prompt as if it were the document's content.
        """
        if not _MARKDOWN_ARTEFACTS.sub("", raw).strip():
            return ""
        stripped = raw.strip()
        return stripped if len(stripped) >= _MINIMUM_USEFUL_CHARACTERS else ""

    @staticmethod
    def _unreadable(ref: MailAttachmentRef, detail: str) -> ExtractedAttachment:
        return ExtractedAttachment(
            filename=ref.filename,
            content_type=ref.content_type,
            size_bytes=ref.size_bytes,
            outcome=AttachmentOutcome.UNREADABLE,
            detail=detail,
        )
