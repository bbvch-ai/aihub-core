from pydantic import BaseModel
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModManifest


class OpenWebuiModCatalogEntry(BaseModel):
    source_revision: str
    manifest: OpenWebuiModManifest
    builtin: bool
