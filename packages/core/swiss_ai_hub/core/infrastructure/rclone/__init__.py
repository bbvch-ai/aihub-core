from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.rclone.rclone_pipeline_settings import RclonePipelineSettings
    from swiss_ai_hub.core.infrastructure.rclone.rclone_settings import RcloneSettings
    from swiss_ai_hub.core.infrastructure.rclone.rclone_source_config import RcloneBackendType, RcloneSourceConfig

__all__ = ["RcloneBackendType", "RclonePipelineSettings", "RcloneSettings", "RcloneSourceConfig"]

_LAZY_IMPORTS = {
    "RcloneBackendType": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_config",
    "RclonePipelineSettings": "swiss_ai_hub.core.infrastructure.rclone.rclone_pipeline_settings",
    "RcloneSettings": "swiss_ai_hub.core.infrastructure.rclone.rclone_settings",
    "RcloneSourceConfig": "swiss_ai_hub.core.infrastructure.rclone.rclone_source_config",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
