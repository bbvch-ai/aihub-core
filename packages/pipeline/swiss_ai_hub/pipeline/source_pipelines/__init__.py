from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import (
        AbstractStructuredSourceAdapter,
    )
    from swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config import RcloneSyncConfig
    from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

__all__ = ["AbstractStructuredSourceAdapter", "RcloneSyncConfig", "StructuredSyncConfig"]

_LAZY_IMPORTS = {
    "AbstractStructuredSourceAdapter": "swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter",
    "RcloneSyncConfig": "swiss_ai_hub.pipeline.source_pipelines.rclone_sync_config",
    "StructuredSyncConfig": "swiss_ai_hub.pipeline.source_pipelines.structured_sync_config",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
