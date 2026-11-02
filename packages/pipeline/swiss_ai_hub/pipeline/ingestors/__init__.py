from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig

__all__ = ["DocumentIngestionConfig"]

_LAZY_IMPORTS: dict[str, str] = {
    "DocumentIngestionConfig": "swiss_ai_hub.pipeline.ingestors.document_ingestion_config",
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
