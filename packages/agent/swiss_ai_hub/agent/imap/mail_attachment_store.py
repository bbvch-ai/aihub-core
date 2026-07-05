import asyncio
from uuid import uuid4

import boto3
from botocore.config import Config
from swiss_ai_hub.core.events.agent import MailAttachmentRef, UserUploadedFile
from swiss_ai_hub.core.infrastructure.s3.s3_storage_settings import S3StorageSettings

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

        settings = S3StorageSettings()
        client = boto3.client(
            "s3",
            endpoint_url=settings.ENDPOINT,
            aws_access_key_id=settings.ACCESS_KEY,
            aws_secret_access_key=settings.SECRET_KEY.get_secret_value(),
            region_name=settings.REGION,
            config=Config(signature_version="s3v4"),
        )

        refs: list[MailAttachmentRef] = []
        for attachment in attachments:
            file_id = str(uuid4())
            uploaded = UserUploadedFile(
                filename=attachment.filename,
                file_type=attachment.content_type,
                file_id=file_id,
            )
            bucket, key = uploaded.resolve_s3_location(agent_class, agent_id)
            await asyncio.to_thread(
                client.put_object,
                Bucket=bucket,
                Key=key,
                Body=attachment.content,
                ContentType=attachment.content_type,
            )
            refs.append(
                MailAttachmentRef(
                    filename=attachment.filename,
                    content_type=attachment.content_type,
                    file_id=file_id,
                    size_bytes=len(attachment.content),
                )
            )
        return refs
