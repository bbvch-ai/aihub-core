import asyncio
from uuid import uuid4

from swiss_ai_hub.core.events.agent import MailAttachmentRef, MailMessageRef
from swiss_ai_hub.core.events.agent.imap.mail_message_ref import RFC822_CONTENT_TYPE
from swiss_ai_hub.core.infrastructure import create_s3_client

from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment

# Forces a download instead of an inline render. The archived message is stored verbatim, so its HTML is
# still attacker-controlled markup; a consumer that renders it must sanitize at render time (ADR
# 2026_07_05). This header is the transport-level guard that keeps a browser from doing so accidentally.
_DOWNLOAD_DISPOSITION = "attachment"


class MailStore:
    """Persists fetched mail — attachments and the original message — to the shared agent-files S3 bucket.

    Bytes never travel inside protocol events. Everything is stored under the agent's own path prefix
    (mirroring UserUploadedFile) and carried as a reference, keeping persisted and streamed events small.
    """

    @staticmethod
    async def store_attachments(
        attachments: list[ParsedAttachment],
        agent_class: str,
        agent_id: str,
    ) -> list[MailAttachmentRef]:
        if not attachments:
            return []

        client = create_s3_client()

        refs: list[MailAttachmentRef] = []
        for attachment in attachments:
            ref = MailAttachmentRef(
                filename=attachment.filename,
                content_type=attachment.content_type,
                file_id=str(uuid4()),
                size_bytes=len(attachment.content),
            )
            bucket, key = ref.resolve_s3_location(agent_class, agent_id)
            await asyncio.to_thread(
                client.put_object,
                Bucket=bucket,
                Key=key,
                Body=attachment.content,
                ContentType=attachment.content_type,
            )
            refs.append(ref)
        return refs

    @staticmethod
    async def store_message(
        raw: bytes,
        message_id: str,
        agent_class: str,
        agent_id: str,
    ) -> MailMessageRef | None:
        """Archive the message exactly as the server sent it, returning None when there is nothing to store.

        The raw RFC822 bytes are stored rather than a projection of the parsed fields: they are the original
        by definition, so they also preserve what the event omits (recipients, HTML body) and keep any DKIM
        signature verifiable. The attachments are therefore held twice — inline here and as their own objects
        — which is accepted so the existing attachment contract stays unchanged.
        """
        if not raw:
            return None

        # message_id is an IMAP UID, so the name is always digits; MailMessageRef's pattern rejects
        # anything else rather than silently sanitizing it.
        ref = MailMessageRef(
            filename=f"{message_id}.eml",
            content_type=RFC822_CONTENT_TYPE,
            file_id=str(uuid4()),
            size_bytes=len(raw),
        )
        bucket, key = ref.resolve_s3_location(agent_class, agent_id)
        await asyncio.to_thread(
            create_s3_client().put_object,
            Bucket=bucket,
            Key=key,
            Body=raw,
            ContentType=RFC822_CONTENT_TYPE,
            ContentDisposition=_DOWNLOAD_DISPOSITION,
        )
        return ref

    @staticmethod
    async def load_message(ref: MailMessageRef, agent_class: str, agent_id: str) -> bytes:
        """Read an archived message back as the raw RFC822 bytes that were stored.

        This is how a step running *after* the message has been filed still gets at its content: the IMAP UID died
        with the `MOVE`, but the archive is keyed by `file_id` and does not move. The bytes are the message verbatim,
        so a re-parse recovers everything the summary event omits — recipients, the HTML body, the attachments.
        """
        return await MailStore._load(*ref.resolve_s3_location(agent_class, agent_id))

    @staticmethod
    async def load_attachment(ref: MailAttachmentRef, agent_class: str, agent_id: str) -> bytes:
        """Read one archived attachment back as the bytes that were stored."""
        return await MailStore._load(*ref.resolve_s3_location(agent_class, agent_id))

    @staticmethod
    async def _load(bucket: str, key: str) -> bytes:
        response = await asyncio.to_thread(create_s3_client().get_object, Bucket=bucket, Key=key)
        return await asyncio.to_thread(response["Body"].read)
