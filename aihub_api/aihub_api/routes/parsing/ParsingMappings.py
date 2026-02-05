"""
File format and MIME type mappings for document parsing.

Provides utilities for detecting file formats from extensions and MIME types.
"""

from enum import StrEnum


class InputFormat(StrEnum):
    """Supported input document formats."""

    # MinerU formats
    PDF = "pdf"
    IMAGE = "image"

    # MarkItDown formats
    DOCX = "docx"
    PPTX = "pptx"
    XLSX = "xlsx"
    XLS = "xls"
    OUTLOOK = "outlook"

    # Text formats (existing loaders)
    TXT = "txt"
    MARKDOWN = "md"


# Map formats to file extensions
FormatToExtensions: dict[InputFormat, list[str]] = {
    InputFormat.PDF: ["pdf"],
    InputFormat.IMAGE: ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff", "jp2"],
    InputFormat.DOCX: ["docx"],
    InputFormat.PPTX: ["pptx"],
    InputFormat.XLSX: ["xlsx"],
    InputFormat.XLS: ["xls"],
    InputFormat.OUTLOOK: ["msg", "eml"],
    InputFormat.TXT: ["txt"],
    InputFormat.MARKDOWN: ["md"],
}

# Map formats to MIME types
FormatToMimeType: dict[InputFormat, list[str]] = {
    InputFormat.PDF: ["application/pdf"],
    InputFormat.IMAGE: [
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/bmp",
        "image/webp",
        "image/tiff",
        "image/jp2",
    ],
    InputFormat.DOCX: [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
    InputFormat.PPTX: [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ],
    InputFormat.XLSX: [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ],
    InputFormat.XLS: ["application/vnd.ms-excel"],
    InputFormat.OUTLOOK: ["application/vnd.ms-outlook", "message/rfc822"],
    InputFormat.TXT: ["text/plain"],
    InputFormat.MARKDOWN: ["text/markdown"],
}

# Reverse mapping: MIME type to formats
MimeTypeToFormat: dict[str, list[InputFormat]] = {}
for fmt, mime_types in FormatToMimeType.items():
    for mime_type in mime_types:
        if mime_type not in MimeTypeToFormat:
            MimeTypeToFormat[mime_type] = []
        MimeTypeToFormat[mime_type].append(fmt)

# Extension to format mapping
ExtensionToFormat: dict[str, InputFormat] = {}
for fmt, extensions in FormatToExtensions.items():
    for ext in extensions:
        ExtensionToFormat[ext] = fmt


def get_format_from_extension(extension: str) -> InputFormat | None:
    """Get the input format for a file extension."""
    ext = extension.lower().lstrip(".")
    return ExtensionToFormat.get(ext)


def get_format_from_mime_type(mime_type: str) -> InputFormat | None:
    """Get the input format for a MIME type."""
    formats = MimeTypeToFormat.get(mime_type.lower(), [])
    return formats[0] if formats else None


def get_extension(filename: str, content_type: str = "") -> str:
    """
    Extract file extension from filename or infer from content type.

    Returns lowercase extension without the leading dot.
    """
    # Try to get extension from filename
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext:
            return ext

    # Fall back to content type
    if content_type:
        fmt = get_format_from_mime_type(content_type)
        if fmt:
            extensions = FormatToExtensions.get(fmt, [])
            if extensions:
                return extensions[0]

    # Default to pdf
    return "pdf"
