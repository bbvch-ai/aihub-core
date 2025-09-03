from functools import cached_property

from pydantic import BaseModel, Field


class FileType(BaseModel):
    mime_type: str = Field(..., description="The MIME type string.")
    extensions: list[str] = Field(..., description="A list of valid file extensions, including the dot (e.g., '.pdf').")


class FileTypeConfig(BaseModel):
    file_types: list[FileType]

    def get_unique_extensions(self) -> list[str]:
        all_extensions = [ext for file_type in self.file_types for ext in file_type.extensions]
        return sorted(list(set(all_extensions)))

    def get_all_mime_types(self) -> list[str]:
        return [file_type.mime_type for file_type in self.file_types]

    @cached_property
    def _mime_map(self) -> dict[str, FileType]:
        """Internal, fast lookup from MIME type to the full FileType object."""
        return {ft.mime_type: ft for ft in self.file_types}

    @cached_property
    def _extension_map(self) -> dict[str, list[str]]:
        """Internal, fast lookup from an extension to a list of valid MIME types."""
        ext_map: dict[str, list[str]] = {}
        for ft in self.file_types:
            for ext in ft.extensions:
                if ext not in ext_map:
                    ext_map[ext] = []
                ext_map[ext].append(ft.mime_type)
        return ext_map

    def is_mime_type_supported(self, mime_type: str) -> bool:
        """Checks if a given MIME type is supported."""
        return mime_type in self._mime_map

    def is_extension_supported(self, extension: str) -> bool:
        """Checks if a given file extension is supported."""
        return extension in self._extension_map

    def get_allowed_extensions_for_mime(self, mime_type: str) -> list[str] | None:
        """Returns the valid extensions for a given MIME type."""
        file_type = self._mime_map.get(mime_type)
        return file_type.extensions if file_type else None

    def is_pair_consistent(self, extension: str, mime_type: str) -> bool:
        """Checks if a given file extension is valid for a given MIME type."""
        allowed_extensions = self.get_allowed_extensions_for_mime(mime_type)
        return bool(allowed_extensions and extension in allowed_extensions)


SUPPORTED_FILE_TYPES_CONFIG = FileTypeConfig(
    file_types=[
        # Text documents
        FileType(mime_type="text/plain", extensions=[".txt", ".asc"]),
        FileType(mime_type="text/markdown", extensions=[".md", ".markdown"]),
        FileType(mime_type="text/x-markdown", extensions=[".md", ".markdown"]),
        FileType(mime_type="text/csv", extensions=[".csv"]),
        FileType(mime_type="text/html", extensions=[".html", ".htm", ".xhtml"]),
        FileType(mime_type="application/xhtml+xml", extensions=[".xhtml"]),
        FileType(mime_type="text/asciidoc", extensions=[".adoc", ".asciidoc", ".asc"]),
        FileType(mime_type="text/x-asciidoc", extensions=[".adoc", ".asciidoc", ".asc"]),
        # PDF
        FileType(mime_type="application/pdf", extensions=[".pdf"]),
        # Microsoft Office documents (Word)
        FileType(
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", extensions=[".docx"]
        ),
        FileType(
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.template", extensions=[".dotx"]
        ),
        FileType(mime_type="application/vnd.ms-word.document.macroenabled.12", extensions=[".docm"]),
        FileType(mime_type="application/vnd.ms-word.template.macroenabled.12", extensions=[".dotm"]),
        # Microsoft Office documents (PowerPoint)
        FileType(
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", extensions=[".pptx"]
        ),
        FileType(
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.template", extensions=[".potx"]
        ),
        FileType(
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.slideshow", extensions=[".ppsx"]
        ),
        FileType(mime_type="application/vnd.ms-powerpoint.presentation.macroenabled.12", extensions=[".pptm"]),
        FileType(mime_type="application/vnd.ms-powerpoint.template.macroenabled.12", extensions=[".potm"]),
        FileType(mime_type="application/vnd.ms-powerpoint.slideshow.macroenabled.12", extensions=[".ppsm"]),
        # Microsoft Office documents (Excel)
        FileType(mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", extensions=[".xlsx"]),
        FileType(mime_type="application/vnd.ms-excel.sheet.macroenabled.12", extensions=[".xlsm"]),
        # Data formats
        FileType(mime_type="application/json", extensions=[".json"]),
        FileType(mime_type="application/xml", extensions=[".xml", ".nxml"]),
        FileType(mime_type="text/xml", extensions=[".xml", ".nxml"]),
        # Images
        FileType(mime_type="image/jpeg", extensions=[".jpg", ".jpeg"]),
        FileType(mime_type="image/png", extensions=[".png"]),
        FileType(mime_type="image/tiff", extensions=[".tif", ".tiff"]),
        FileType(mime_type="image/bmp", extensions=[".bmp"]),
        FileType(mime_type="image/webp", extensions=[".webp"]),
        # Audio
        FileType(mime_type="audio/wav", extensions=[".wav"]),
        FileType(mime_type="audio/wave", extensions=[".wav"]),
        FileType(mime_type="audio/x-wav", extensions=[".wav"]),
        FileType(mime_type="audio/mpeg", extensions=[".mp3"]),
        FileType(mime_type="audio/mp3", extensions=[".mp3"]),
    ]
)
