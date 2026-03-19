from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
    from swiss_ai_hub.pipeline.types.document_with_figure_info import DocumentWithFigureInfo
    from swiss_ai_hub.pipeline.types.figure_metadata import FigureMetadata
    from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile, RcloneFile
    from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
    from swiss_ai_hub.pipeline.types.share_point_file import MinimalSharePointFile, SharePointFile
    from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile, SourceFile

__all__ = [
    "DataLakeFile",
    "DocumentWithFigureInfo",
    "FigureMetadata",
    "MinimalRcloneFile",
    "MinimalSharePointFile",
    "MinimalSourceFile",
    "RcloneFile",
    "RefDocDocument",
    "SharePointFile",
    "SourceFile",
]

_LAZY_IMPORTS: dict[str, str] = {
    "DataLakeFile": "swiss_ai_hub.pipeline.types.data_lake_file",
    "DocumentWithFigureInfo": "swiss_ai_hub.pipeline.types.document_with_figure_info",
    "FigureMetadata": "swiss_ai_hub.pipeline.types.figure_metadata",
    "MinimalRcloneFile": "swiss_ai_hub.pipeline.types.rclone_file",
    "MinimalSharePointFile": "swiss_ai_hub.pipeline.types.share_point_file",
    "MinimalSourceFile": "swiss_ai_hub.pipeline.types.source_file",
    "RcloneFile": "swiss_ai_hub.pipeline.types.rclone_file",
    "RefDocDocument": "swiss_ai_hub.pipeline.types.ref_doc_document",
    "SharePointFile": "swiss_ai_hub.pipeline.types.share_point_file",
    "SourceFile": "swiss_ai_hub.pipeline.types.source_file",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
