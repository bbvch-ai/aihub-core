from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_publication_entity import OpenWebuiModPublicationEntity
    from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_revision_entity import OpenWebuiModRevisionEntity

__all__ = ["OpenWebuiModRevisionEntity", "OpenWebuiModPublicationEntity"]


def __getattr__(name: str) -> object:
    if name == "OpenWebuiModPublicationEntity":
        from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_publication_entity import OpenWebuiModPublicationEntity

        globals()[name] = OpenWebuiModPublicationEntity
        return OpenWebuiModPublicationEntity
    if name == "OpenWebuiModRevisionEntity":
        from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_revision_entity import OpenWebuiModRevisionEntity

        globals()[name] = OpenWebuiModRevisionEntity
        return OpenWebuiModRevisionEntity
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
