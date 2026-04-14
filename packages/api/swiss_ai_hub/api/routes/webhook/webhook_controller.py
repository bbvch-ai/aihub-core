import asyncio
import hmac
import logging
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Query
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import AuthHandler
from swiss_ai_hub.core.infrastructure import OpenWebuiProvisioner, OpenWebuiSettings, use_redis
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.webhook.dto.openwebui_webhook_payload import OpenWebuiWebhookPayload
from swiss_ai_hub.api.routes.webhook.dto.webhook_response import WebhookResponse

logger = logging.getLogger(__name__)
_background_tasks: set[asyncio.Task] = set()


class WebhookController(Controller):
    name = ApiLocaleString.from_i18n_path("api.controllers.webhook.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.webhook.description")
    icon = "mdi:webhook"

    def __init__(self, *, auth: AuthHandler, route: str = "/webhook"):
        super().__init__(auth=auth, route=route)

    def openwebui(self) -> Self:
        @self.router.post("/openwebui", tags=self.tags)
        async def receive_openwebui_webhook(
            payload: OpenWebuiWebhookPayload,
            token: Annotated[str, Query(description="Webhook authentication token")],
            redis: Annotated[Redis, Depends(use_redis)],
        ) -> WebhookResponse:
            expected_secret = OpenWebuiSettings().WEBHOOK_SECRET.get_secret_value()
            if not hmac.compare_digest(token, expected_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook token")

            if payload.action != "signup":
                return WebhookResponse(status="ignored")

            logger.info("OpenWebUI webhook: new user signup — triggering provisioner sync")
            task = asyncio.create_task(OpenWebuiProvisioner(redis=redis).sync_access())
            _background_tasks.add(task)
            task.add_done_callback(_background_tasks.discard)

            return WebhookResponse(status="ok")

        return self
