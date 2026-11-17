from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection import OpenWebuiModSelection


class OpenWebuiModActivation(OpenWebuiModSelection):
    publication: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    has_backend: bool
