import asyncio
import hmac
import logging
from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import OpenWebuiProvisioner
from aihub_lib.infrastructure.openwebui.OpenWebuiSettings import OpenWebuiSettings
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Query

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.routes.webhook.dto.OpenWebuiWebhookPayload import OpenWebuiWebhookPayload
from aihub_api.routes.webhook.dto.WebhookResponse import WebhookResponse

logger = logging.getLogger(__name__)


class WebhookController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.webhook.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.webhook.description")
    icon = "mdi:webhook"

    def __init__(self, *, auth: AuthHandler, route: str = "/webhook"):
        super().__init__(auth=auth, route=route)

    _background_tasks: set[asyncio.Task] = set()

    def openwebui(self) -> Self:
        expected_secret = OpenWebuiSettings().WEBHOOK_SECRET.get_secret_value()

        @self.router.post("/openwebui", tags=self.tags)
        async def receive_openwebui_webhook(
            payload: OpenWebuiWebhookPayload,
            token: Annotated[str, Query(description="Webhook authentication token")],
        ) -> WebhookResponse:
            if not hmac.compare_digest(token, expected_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook token")

            if payload.action != "signup":
                return WebhookResponse(status="ignored")

            logger.info(f"OpenWebUI webhook: new user '{payload.user.email}' — triggering provisioner sync")
            task = asyncio.create_task(OpenWebuiProvisioner().sync_access())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            return WebhookResponse(status="ok")

        return self
