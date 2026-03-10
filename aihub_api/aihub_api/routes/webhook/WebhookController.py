"""Receives webhooks from OpenWebUI and triggers provisioner sync."""

import asyncio
import json
import logging
from typing import Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.routes.Controller import Controller
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class OpenWebuiWebhookPayload(BaseModel):
    """Matches OpenWebUI's default webhook payload: {action, message, user}."""

    action: str
    message: str = ""
    user: dict = {}

    @field_validator("user", mode="before")
    @classmethod
    def parse_user_json(cls, v: str | dict) -> dict:
        """OpenWebUI sends user as a JSON string via model_dump_json()."""
        if isinstance(v, str):
            return json.loads(v)
        return v


class WebhookController(Controller):
    name = LocaleString(en="Webhooks", de="Webhooks", fr="Webhooks", it="Webhooks")
    description = LocaleString(
        en="Webhook receivers for external services",
        de="Webhook-Empfänger für externe Dienste",
        fr="Récepteurs de webhooks pour services externes",
        it="Ricevitori webhook per servizi esterni",
    )
    icon = "mdi:webhook"

    def __init__(self, *, auth: AuthHandler, route: str = "/webhook"):
        super().__init__(auth=auth, route=route)

    def openwebui(self) -> Self:
        @self.router.post("/openwebui", tags=self.tags)
        async def receive_openwebui_webhook(payload: OpenWebuiWebhookPayload) -> dict[str, str]:
            """Receives OpenWebUI webhooks. On signup, triggers provisioner group sync."""
            if payload.action != "signup":
                return {"status": "ignored"}

            email = payload.user.get("email", "unknown")
            logger.info(f"OpenWebUI webhook: new user '{email}' — triggering provisioner sync")
            asyncio.create_task(OpenWebuiProvisioner().sync_access())

            return {"status": "ok"}

        return self
