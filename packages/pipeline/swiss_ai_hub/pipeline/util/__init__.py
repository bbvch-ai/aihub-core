from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.util.id_utils import uri_to_id
    from swiss_ai_hub.pipeline.util.rag_definitions_util import rag_pipeline_definitions
    from swiss_ai_hub.pipeline.util.partition_utils import replace_partition_keys

__all__ = [
    "rag_pipeline_definitions",
    "replace_partition_keys",
    "uri_to_id",
]

_LAZY_IMPORTS: dict[str, str] = {
    "rag_pipeline_definitions": "swiss_ai_hub.pipeline.util.rag_definitions_util",
    "replace_partition_keys": "swiss_ai_hub.pipeline.util.partition_utils",
    "uri_to_id": "swiss_ai_hub.pipeline.util.id_utils",
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
