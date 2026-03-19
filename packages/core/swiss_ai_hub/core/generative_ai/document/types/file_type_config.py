import mimetypes
from functools import cached_property
from typing import Annotated

from pydantic import BaseModel, Field


class FileTypeConfig(BaseModel):
    supported_extensions: Annotated[
        list[str], Field(description="List of supported file extensions including the dot")
    ] = [
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".html",
        ".htm",
        ".xhtml",
        ".adoc",
        ".asciidoc",
        ".asc",
        ".pdf",
        ".docx",
        ".dotx",
        ".docm",
        ".dotm",
        ".pptx",
        ".potx",
        ".ppsx",
        ".pptm",
        ".potm",
        ".ppsm",
        ".xlsx",
        ".xlsm",
        ".json",
        ".xml",
        ".nxml",
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
        ".bmp",
        ".webp",
        ".wav",
        ".mp3",
    ]

    @cached_property
    def _extension_to_mime_map(self) -> dict[str, str]:
        mapping = {}
        for ext in self.supported_extensions:
            mime_type, _ = mimetypes.guess_type(f"file{ext}")
            if mime_type:
                mapping[ext] = mime_type
            elif ext == ".md" or ext == ".markdown":
                mapping[ext] = "text/markdown"
            elif ext == ".adoc" or ext == ".asciidoc":
                mapping[ext] = "text/asciidoc"
        return mapping

    @cached_property
    def _mime_to_extensions_map(self) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for ext, mime_type in self._extension_to_mime_map.items():
            if mime_type not in mapping:
                mapping[mime_type] = []
            mapping[mime_type].append(ext)
        return mapping

    def get_unique_extensions(self) -> list[str]:
        return sorted(self.supported_extensions)

    def is_extension_supported(self, extension: str) -> bool:
        """Checks if a given file extension is supported."""
        return extension in self.supported_extensions

    def get_mime_type_for_extension(self, extension: str) -> str | None:
        """Get the MIME type for a supported extension."""
        return self._extension_to_mime_map.get(extension)
