import asyncio
from uuid import uuid4

from swiss_ai_hub.core.events.agent import MailAttachmentRef
from swiss_ai_hub.core.infrastructure import create_s3_client

from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment


class MailAttachmentStore:
    """Persists mail attachment bytes to the shared agent-files S3 bucket and returns references.

    Attachment bytes never travel inside protocol events — they are stored under the agent's own
    path prefix (mirroring UserUploadedFile) and carried as MailAttachmentRef, keeping persisted and
    streamed events small.
    """

    @staticmethod
    async def store(
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
