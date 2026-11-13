from pydantic import BaseModel
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModManifest


class OpenWebuiModUploadPreview(BaseModel):
    manifest: OpenWebuiModManifest
    installed_version: str | None
