from pydantic import BaseModel
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModConfiguration

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_worker_state import OpenWebuiModWorkerState


class OpenWebuiModGlobalState(BaseModel):
    configuration: OpenWebuiModConfiguration
    active_version: int
    boot_id: str
    expected_workers: int
    restart_required: bool
    workers: list[OpenWebuiModWorkerState]
