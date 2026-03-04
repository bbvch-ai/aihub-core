from typing import TYPE_CHECKING, ClassVar

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

if TYPE_CHECKING:
    from fsspec import AbstractFileSystem


class RawLoader(BaseReader):
    """Plaintext file loader — reads raw UTF-8 content without any conversion."""

    SUPPORTED_EXTENSIONS: ClassVar[list[str]] = [
        "txt",
        "md",
        "csv",
        "json",
        "xml",
        "yml",
        "yaml",
        "log",
        "ini",
        "cfg",
        "toml",
    ]

    @trace_fn
    def load_data(
        self,
        file: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        *args,
        **kwargs,
    ) -> list[Document]:
        """Parse file into string."""
        with fs.open(str(file), "r", encoding="utf-8") as f:
            content = f.read()
        metadata = extra_info or {}
        return [Document(text=content, metadata=metadata)]

    async def aload_data_from_bytes(
        self,
        content: bytes,
        filename: str,
        extra_info: dict | None = None,
        fs: "AbstractFileSystem | None" = None,
        include_images: bool = True,
        embed_base64: bool = False,
    ) -> list[Document]:
        """Load plaintext document from raw bytes."""
        text = content.decode("utf-8", errors="replace")
        metadata = extra_info or {}
        return [Document(text=text, metadata=metadata)]
