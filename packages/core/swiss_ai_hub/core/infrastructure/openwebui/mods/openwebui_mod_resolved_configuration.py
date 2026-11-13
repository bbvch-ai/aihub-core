from pydantic import BaseModel

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_activation import OpenWebuiModActivation


class OpenWebuiModResolvedConfiguration(BaseModel):
    version: int
    mods: list[OpenWebuiModActivation]
