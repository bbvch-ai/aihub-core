import asyncio
import mimetypes

from swiss_ai_hub.core.generative_ai.document.extraction.extracted_document import ExtractedDocument
from swiss_ai_hub.core.generative_ai.document.extraction.unsupported_document_type_error import (
    UnsupportedDocumentTypeError,
)
from swiss_ai_hub.core.generative_ai.document.loaders.document_loader_selector import DocumentLoaderSelector
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_filesystem, create_s3_service

S3_URI_SCHEME = "s3://"


class DocumentExtractor:
    """Turns a document into a title and a body, whatever its type and however it was delivered.

    Transport-agnostic on purpose: it takes a bucket and a key, so it does not care whether the bytes arrived as a
    webhook upload, a knowledge-base file or an agent attachment. Routing is delegated wholesale to
    `DocumentLoaderSelector`, so this holds no per-format branch of its own.
    """

    @staticmethod
    @trace_fn
    async def extract_from_uri(
        uri: str,
        content_type: str = "",
        include_images: bool = False,
    ) -> ExtractedDocument:
        """Read from an `s3://bucket/key` URI, the form the platform stores document sources in."""
        bucket, key = DocumentExtractor.split_s3_uri(uri)
        return await DocumentExtractor.extract_from_s3(bucket, key, content_type, include_images)

    @staticmethod
    @trace_fn
    async def extract_from_s3(
        bucket: str,
        key: str,
        content_type: str = "",
        include_images: bool = False,
    ) -> ExtractedDocument:
        """Read the object's bytes and extract.

        The whole call is off-loaded, not just the download: `create_s3_service` builds three boto3 clients, and
        each one loads botocore's service models and reads local AWS config — tens of milliseconds of blocking work
        that would otherwise sit on the event loop once per extraction.
        """
        content = await asyncio.to_thread(lambda: create_s3_service().download_file(bucket, key))
        return await DocumentExtractor.extract_from_bytes(
            content=content,
            filename=key.rsplit("/", 1)[-1],
            content_type=content_type,
            source=f"{S3_URI_SCHEME}{bucket}/{key}",
            include_images=include_images,
        )

    @staticmethod
    @trace_fn
    async def extract_from_bytes(
        content: bytes,
        filename: str,
        content_type: str = "",
        source: str | None = None,
        include_images: bool = False,
    ) -> ExtractedDocument:
        """Extract from bytes already in hand, for a caller whose document never reached S3."""
        # `for_file` rather than `extension_for` + `for_extension`: it is the selector's own one-call entry point
        # for a caller holding a filename and a MIME type, and it is the seam existing callers patch in tests.
        loader = DocumentLoaderSelector.for_file(filename, content_type)
        if loader is None:
            raise UnsupportedDocumentTypeError(filename, DocumentLoaderSelector.extension_for(filename, content_type))

        # include_images defaults off: a classifier prompt has no use for figures, and it is what lets the loaders
        # run without an fsspec filesystem to write them to.
        documents = await loader.aload_data_from_bytes(
            content=content,
            filename=filename,
            fs=create_s3_filesystem() if include_images else None,
            include_images=include_images,
        )
        return ExtractedDocument.from_documents(
            documents=documents,
            filename=filename,
            content_type=content_type or DocumentExtractor.guess_content_type(filename),
            document_parser=type(loader).__name__,
            source=source,
        )

    @staticmethod
    def can_extract(filename: str, content_type: str = "") -> bool:
        """Whether any loader can read this file, decided from the name and MIME type alone.

        Exists so a caller holding only a reference can skip a file before paying to fetch its bytes — the mail
        attachment reader would otherwise spend an S3 round trip on every `.zip` just to be told it is unreadable.
        """
        return DocumentLoaderSelector.for_file(filename, content_type) is not None

    @staticmethod
    def split_s3_uri(uri: str) -> tuple[str, str]:
        """Split `s3://bucket/key` into its two parts, rejecting anything that is not one."""
        if not uri.startswith(S3_URI_SCHEME):
            raise ValueError(f"Not an S3 URI: {uri!r}")
        bucket, _, key = uri.removeprefix(S3_URI_SCHEME).partition("/")
        if not bucket or not key:
            raise ValueError(f"S3 URI is missing a bucket or a key: {uri!r}")
        return bucket, key

    @staticmethod
    def guess_content_type(filename: str) -> str:
        """`download_file` returns bytes only and drops the object's stored ContentType, so the name is what is left."""
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or "application/octet-stream"
