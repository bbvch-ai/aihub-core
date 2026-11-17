import asyncio
import io
from typing import Annotated, ClassVar, Self

from botocore.exceptions import ClientError
from fastapi import HTTPException, Response, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)


class FigureImage(BaseModel):
    """A stored figure decoded and encoded again before it is served.

    The response comes from OpenWebUI's origin, where a script would run with the user's session, so only what Pillow
    decodes as a raster image ever leaves, in a format chosen here and never the bytes as stored. Anyone who can write
    to a synced folder can plant bytes at a figure key, so size and pixels are bounded before anything is decoded.
    """

    MAX_STORED_BYTES: ClassVar[int] = 20 * 1024 * 1024
    MAX_PIXELS: ClassVar[int] = 25_000_000
    MAX_SIDE: ClassVar[int] = 2048
    JPEG_QUALITY: ClassVar[int] = 85
    MAX_CONCURRENT_DECODES: ClassVar[int] = 4
    READABLE_FORMATS: ClassVar[tuple[str, ...]] = ("BMP", "GIF", "JPEG", "PNG", "WEBP")
    RESPONSE_HEADERS: ClassVar[dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'; sandbox",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cache-Control": "private, max-age=300",
    }
    _decoding: ClassVar[asyncio.Semaphore] = asyncio.Semaphore(MAX_CONCURRENT_DECODES)
    _MISSING_OBJECT_CODES: ClassVar[frozenset[str]] = frozenset({"404", "NoSuchKey", "NotFound"})

    content: Annotated[bytes, "The encoded image"]
    media_type: Annotated[str, "Its MIME type"]

    @classmethod
    async def from_storage(
        cls,
        s3_service: S3AnonymousFileAccessService,
        container: Annotated[str, "Knowledge bucket"],
        file_path: Annotated[str, "Key of the figure"],
    ) -> Self:
        """Read and re-encoded off the event loop, a few at a time, since decoding holds the whole image in memory."""
        async with cls._decoding:
            return await asyncio.to_thread(cls._load, s3_service, container, file_path)

    @classmethod
    def from_stored(cls, stored: Annotated[bytes, "The figure's bytes as stored"]) -> Self:
        if len(stored) > cls.MAX_STORED_BYTES:
            raise cls._unsupported("Figure is too large")
        image = cls._open(stored)
        image.thumbnail((cls.MAX_SIDE, cls.MAX_SIDE))
        if cls._has_transparency(image):
            return cls._encoded(image.convert("RGBA"), "PNG", "image/png")
        return cls._encoded(image.convert("RGB"), "JPEG", "image/jpeg", quality=cls.JPEG_QUALITY)

    def to_response(self) -> Response:
        """Served with headers that keep a browser from treating it as anything but this image, or sharing it."""
        return Response(content=self.content, media_type=self.media_type, headers=self.RESPONSE_HEADERS)

    @classmethod
    def _load(cls, s3_service: S3AnonymousFileAccessService, container: str, file_path: str) -> Self:
        """A chat keeps its figure links after the document is removed, so a missing figure is expected, not a fault."""
        try:
            size = s3_service.file_size(container, file_path)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in cls._MISSING_OBJECT_CODES:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This figure no longer exists.")
            raise
        if size > cls.MAX_STORED_BYTES:
            raise cls._unsupported("Figure is too large")
        return cls.from_stored(s3_service.download_file(container, file_path))

    @classmethod
    def _open(cls, stored: bytes) -> Image.Image:
        """Pixels are counted from the header, before `load()` decodes them."""
        try:
            image = Image.open(io.BytesIO(stored), formats=list(cls.READABLE_FORMATS))
        except UnidentifiedImageError:
            raise cls._unsupported("Figure is not a supported raster image")
        except Image.DecompressionBombError:
            raise cls._unsupported("Figure has too many pixels")
        if image.width * image.height > cls.MAX_PIXELS:
            raise cls._unsupported("Figure has too many pixels")
        image.load()
        return image

    @staticmethod
    def _has_transparency(image: Image.Image) -> bool:
        return image.mode in {"RGBA", "LA", "PA"} or (image.mode == "P" and "transparency" in image.info)

    @classmethod
    def _encoded(cls, image: Image.Image, image_format: str, media_type: str, **options: int) -> Self:
        buffer = io.BytesIO()
        image.save(buffer, format=image_format, **options)
        return cls(content=buffer.getvalue(), media_type=media_type)

    @staticmethod
    def _unsupported(detail: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail)
