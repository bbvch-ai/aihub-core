from pydantic import BaseModel, JsonValue, computed_field
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModManifest


class OpenWebuiModCatalogEntry(BaseModel):
    source_revision: str
    manifest: OpenWebuiModManifest
    builtin: bool

    @computed_field
    @property
    def settings_form(self) -> list[dict[str, JsonValue]]:
        return self.manifest.settings_form()
