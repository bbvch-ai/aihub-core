import asyncio
import base64
import binascii
import hashlib
import math
import mimetypes
from typing import ClassVar

from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from llama_index.core.base.llms.types import ChatMessage, ImageBlock
from pydantic import BaseModel, ConfigDict

from swiss_ai_hub.core.events.agent.user.inline_image_settings import InlineImageSettings
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.events.api_payload_context import ApiPayloadContext


class StoredImage(BaseModel):
    """An image sent inside a message, checked and decoded, waiting to be stored in the agent's file bucket.

    The message keeps the image in its place, as an `s3://agent-files/…` reference the agent signs when it calls its
    model. The bytes never travel in an event. The key is the content's digest, so history resent on every turn stores
    each image once, and a reference can only be named by someone who holds the image.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    block: ImageBlock
    data: bytes
    media_type: str

    SCHEME: ClassVar[str] = "s3://"
    # Raster types only: the types models read, and none that a browser would run as a document (an SVG can carry
    # script, and the API serves stored images from its own origin).
    MEDIA_TYPES: ClassVar[frozenset[str]] = frozenset({"image/png", "image/jpeg", "image/gif", "image/webp"})
    FOLDER: ClassVar[str] = "images"

    @staticmethod
    def is_reference(url: object) -> bool:
        return str(url).startswith(f"{StoredImage.SCHEME}{UserUploadedFile.AGENT_FILES_BUCKET}/")

    @staticmethod
    def location(reference: str) -> tuple[str, str]:
        """The bucket and key a reference names."""
        bucket, _, key = reference.removeprefix(StoredImage.SCHEME).partition("/")
        return bucket, key

    @staticmethod
    def folder(agent_class: str, agent_id: str) -> str:
        safe = UserUploadedFile.sanitize_path_segment
        return f"{safe(agent_class)}/{safe(agent_id)}/{StoredImage.FOLDER}"

    @staticmethod
    def checked_all(messages: list[ChatMessage], context: ApiPayloadContext) -> list["StoredImage"]:
        """Every image of the messages that still has to be stored, checked before any is: a request with one bad
        image leaves nothing behind."""
        settings = InlineImageSettings()
        blocks = [block for message in messages for block in message.blocks if isinstance(block, ImageBlock)]
        return [image for block in blocks if (image := StoredImage._checked(block, context, settings)) is not None]

    @staticmethod
    async def store_all(images: list["StoredImage"], context: ApiPayloadContext) -> None:
        for image in images:
            await image._store(context)

    @staticmethod
    def _checked(block: ImageBlock, context: ApiPayloadContext, settings: InlineImageSettings) -> "StoredImage | None":
        if block.path is not None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "An image cannot name a file path; send its content.")
        if block.image is not None:
            return StoredImage._decoded(block, block.image.decode(), block.image_mimetype, settings)
        url = str(block.url or "")
        if url.startswith("data:"):
            header, _, content = url.partition(",")
            media_type = header.removeprefix("data:").split(";")[0]
            return StoredImage._decoded(block, content, media_type, settings)
        if StoredImage.is_reference(url) and not StoredImage.location(url)[1].startswith(
            f"{StoredImage.folder(context.agent_class, context.agent_id)}/"
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "An image may only reference images of the called agent.")
        return None

    @staticmethod
    def _decoded(
        block: ImageBlock, content: str, media_type: str | None, settings: InlineImageSettings
    ) -> "StoredImage":
        if media_type not in StoredImage.MEDIA_TYPES:
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"An image has the type {media_type!r}; send PNG, JPEG, GIF or WebP.",
            )
        too_large = HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE, f"An image is larger than the {settings.MAX_BYTES} bytes allowed."
        )
        if len(content) > 4 * math.ceil(settings.MAX_BYTES / 3):
            raise too_large
        try:
            data = base64.b64decode(content, validate=True)
        except binascii.Error as decode_error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "An image is not valid base64."
            ) from decode_error
        if len(data) > settings.MAX_BYTES:
            raise too_large
        return StoredImage(block=block, data=data, media_type=media_type)

    async def _store(self, context: ApiPayloadContext) -> None:
        extension = mimetypes.guess_extension(self.media_type) or ""
        key = f"{StoredImage.folder(context.agent_class, context.agent_id)}/{hashlib.sha256(self.data).hexdigest()}"
        key += extension
        bucket = UserUploadedFile.AGENT_FILES_BUCKET
        if not await asyncio.to_thread(StoredImage._exists, context, bucket, key):
            await asyncio.to_thread(
                context.s3_client.put_object, Bucket=bucket, Key=key, Body=self.data, ContentType=self.media_type
            )
        self.block.url = f"{StoredImage.SCHEME}{bucket}/{key}"
        self.block.image = None
        self.block.image_mimetype = self.media_type

    @staticmethod
    def _exists(context: ApiPayloadContext, bucket: str, key: str) -> bool:
        try:
            context.s3_client.head_object(Bucket=bucket, Key=key)
        except ClientError as missing:
            if missing.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True
