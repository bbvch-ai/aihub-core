"""
These mappings are copied from docling.datamodel.base_models.
We do not want to import docling here because it is very heavy.
"""

from enum import StrEnum


class InputFormat(StrEnum):
    """A document format supported by document backend parsers."""

    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    IMAGE = "image"
    PDF = "pdf"
    ASCIIDOC = "asciidoc"
    MD = "md"
    CSV = "csv"
    XLSX = "xlsx"
    XML_USPTO = "xml_uspto"
    XML_JATS = "xml_jats"
    METS_GBS = "mets_gbs"
    JSON_DOCLING = "json_docling"
    AUDIO = "audio"
    VTT = "vtt"


class OutputFormat(StrEnum):
    MARKDOWN = "md"
    JSON = "json"
    HTML = "html"
    HTML_SPLIT_PAGE = "html_split_page"
    TEXT = "text"
    DOCTAGS = "doctags"


FormatToExtensions: dict[InputFormat, list[str]] = {
    InputFormat.DOCX: ["docx", "dotx", "docm", "dotm"],
    InputFormat.PPTX: ["pptx", "potx", "ppsx", "pptm", "potm", "ppsm"],
    InputFormat.PDF: ["pdf"],
    InputFormat.MD: ["md"],
    InputFormat.HTML: ["html", "htm", "xhtml"],
    InputFormat.XML_JATS: ["xml", "nxml"],
    InputFormat.IMAGE: ["jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp"],
    InputFormat.ASCIIDOC: ["adoc", "asciidoc", "asc"],
    InputFormat.CSV: ["csv"],
    InputFormat.XLSX: ["xlsx", "xlsm"],
    InputFormat.XML_USPTO: ["xml", "txt"],
    InputFormat.METS_GBS: ["tar.gz"],
    InputFormat.JSON_DOCLING: ["json"],
    InputFormat.AUDIO: ["wav", "mp3", "m4a", "aac", "ogg", "flac", "mp4", "avi", "mov"],
    InputFormat.VTT: ["vtt"],
}

FormatToMimeType: dict[InputFormat, list[str]] = {
    InputFormat.DOCX: [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    ],
    InputFormat.PPTX: [
        "application/vnd.openxmlformats-officedocument.presentationml.template",
        "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ],
    InputFormat.HTML: ["text/html", "application/xhtml+xml"],
    InputFormat.XML_JATS: ["application/xml"],
    InputFormat.IMAGE: [
        "image/png",
        "image/jpeg",
        "image/tiff",
        "image/gif",
        "image/bmp",
        "image/webp",
    ],
    InputFormat.PDF: ["application/pdf"],
    InputFormat.ASCIIDOC: ["text/asciidoc"],
    InputFormat.MD: ["text/markdown", "text/x-markdown"],
    InputFormat.CSV: ["text/csv"],
    InputFormat.XLSX: ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    InputFormat.XML_USPTO: ["application/xml", "text/plain"],
    InputFormat.METS_GBS: ["application/mets+xml"],
    InputFormat.JSON_DOCLING: ["application/json"],
    InputFormat.AUDIO: [
        "audio/x-wav",
        "audio/mpeg",
        "audio/wav",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/aac",
        "audio/ogg",
        "audio/flac",
        "audio/x-flac",
        "video/mp4",
        "video/avi",
        "video/x-msvideo",
        "video/quicktime",
    ],
    InputFormat.VTT: ["text/vtt"],
}

MimeTypeToFormat: dict[str, list[InputFormat]] = {
    mime: [fmt for fmt in FormatToMimeType if mime in FormatToMimeType[fmt]]
    for value in FormatToMimeType.values()
    for mime in value
}
