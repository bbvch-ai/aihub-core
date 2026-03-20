from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.io.azure_data_lake_io_manager import AzureDataLakeIOManager
    from swiss_ai_hub.pipeline.io.doc_store_io_manager import DocStoreIOManager
    from swiss_ai_hub.pipeline.io.local_file_system_io_manager import LocalFileSystemIOManager
    from swiss_ai_hub.pipeline.io.rclone_io_manager import RcloneIOManager
    from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
    from swiss_ai_hub.pipeline.io.share_point_io_manager import SharePointIoManager
    from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager

__all__ = [
    "AzureDataLakeIOManager",
    "DocStoreIOManager",
    "LocalFileSystemIOManager",
    "RcloneIOManager",
    "S3DataLakeIOManager",
    "SharePointIoManager",
    "VectorStoreIOManager",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AzureDataLakeIOManager": "swiss_ai_hub.pipeline.io.azure_data_lake_io_manager",
    "DocStoreIOManager": "swiss_ai_hub.pipeline.io.doc_store_io_manager",
    "LocalFileSystemIOManager": "swiss_ai_hub.pipeline.io.local_file_system_io_manager",
    "RcloneIOManager": "swiss_ai_hub.pipeline.io.rclone_io_manager",
    "S3DataLakeIOManager": "swiss_ai_hub.pipeline.io.s3_data_lake_io_manager",
    "SharePointIoManager": "swiss_ai_hub.pipeline.io.share_point_io_manager",
    "VectorStoreIOManager": "swiss_ai_hub.pipeline.io.vector_store_io_manager",
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
