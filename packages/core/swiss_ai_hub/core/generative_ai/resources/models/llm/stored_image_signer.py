from collections.abc import Sequence
from functools import cache

from llama_index.core.base.llms.types import ChatMessage, ImageBlock

from swiss_ai_hub.core.events.agent.user.stored_image import StoredImage
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.retrieval.rag_image_inline_settings import RagImageInlineSettings
from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_service


class StoredImageSigner:
    """Turns the stored image references in messages into URLs a model can read, just before the call.

    Signed at the call, not when the image is stored, because messages outlive a signature: events are persisted and
    sent again as history. The URL is signed against the internal endpoint when the gateway inlines images (it fetches
    them in-cluster), and against the public one otherwise, for the provider to fetch; the same choice RAG figures make.
    """

    LIFETIME_HOURS = 1

    @staticmethod
    def signed(messages: Sequence[ChatMessage]) -> Sequence[ChatMessage]:
        if not any(StoredImageSigner._is_stored(block) for message in messages for block in message.blocks):
            return messages
        internal = RagImageInlineSettings().ENABLED
        return [
            message.model_copy(
                update={"blocks": [StoredImageSigner._signed_block(block, internal) for block in message.blocks]}
            )
            for message in messages
        ]

    @staticmethod
    def _is_stored(block: object) -> bool:
        return isinstance(block, ImageBlock) and block.url is not None and StoredImage.is_reference(block.url)

    @staticmethod
    def _signed_block(block: object, internal: bool) -> object:
        if not StoredImageSigner._is_stored(block):
            return block
        bucket, key = StoredImage.location(str(block.url))
        url = StoredImageSigner._service().generate_sas_url(
            bucket, key, lifetime_hours=StoredImageSigner.LIFETIME_HOURS, internal=internal
        )
        return block.model_copy(update={"url": url})

    @staticmethod
    @cache
    def _service() -> S3AnonymousFileAccessService:
        return create_s3_service()
