from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_entity import OpenWebuiModEntity

__all__ = ["OpenWebuiModEntity"]


def __getattr__(name: str) -> object:
    if name == "OpenWebuiModEntity":
        from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_entity import OpenWebuiModEntity

        globals()[name] = OpenWebuiModEntity
        return OpenWebuiModEntity
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
