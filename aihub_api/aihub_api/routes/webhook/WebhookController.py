"""Receives webhooks from OpenWebUI and triggers provisioner sync."""

import asyncio
import hmac
import json
import logging
from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.infrastructure.openwebui.OpenWebuiSettings import OpenWebuiSettings
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Query
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class OpenWebuiWebhookPayload(BaseModel):
    action: str
    message: str = ""
    user: Annotated[dict, Field(default_factory=dict)]

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
        expected_secret = OpenWebuiSettings().WEBHOOK_SECRET.get_secret_value()

        @self.router.post("/openwebui", tags=self.tags)
        async def receive_openwebui_webhook(
            payload: OpenWebuiWebhookPayload,
            token: Annotated[str, Query(description="Webhook authentication token")],
        ) -> dict[str, str]:
            if not hmac.compare_digest(token, expected_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook token")

            if payload.action != "signup":
                return {"status": "ignored"}

            email = payload.user.get("email", "unknown")
            logger.info(f"OpenWebUI webhook: new user '{email}' — triggering provisioner sync")
            asyncio.create_task(OpenWebuiProvisioner().sync_access())

            return {"status": "ok"}

        return self
