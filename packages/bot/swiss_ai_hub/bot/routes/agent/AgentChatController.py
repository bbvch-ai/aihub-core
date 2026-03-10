import logging
from typing import Annotated, Self

from fastapi import Body, Depends, Path, Request, Response
from microsoft_agents.activity import Activity
from microsoft_agents.hosting.aiohttp import CloudAdapter
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.dependencies.use_nats import use_nats
from swiss_ai_hub.core.nats.distributor.dependencies.use_external_agent_event_distributor import (
    use_external_agent_event_distributor,
)
from swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.routes.Controller import Controller

from swiss_ai_hub.bot.bots.chat.agent.AgentChatBot import AgentChatBot
from swiss_ai_hub.bot.bots.chat.agent.StreamAgentChatBot import StreamAgentChatBot
from swiss_ai_hub.bot.routes.RoutesService import RoutesService

logger = logging.getLogger(__name__)


class AgentChatController(Controller):
    name = LocaleString(en="Agent Chat")
    description = LocaleString(en="Chat with agents")
    icon = "mage:we-chat"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/agent/chat", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    @staticmethod
    async def _process_agent_chat_request(
        request: Request,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        agent_class: str,
        agent_id: str,
        bot_class: type[AgentChatBot] | type[StreamAgentChatBot],
        typing_timeout_seconds: int,
    ) -> Response:
        logger.info(f"Starting agent chat completion for {agent_class}/{agent_id}")

        path: str = RoutesService.get_path(request)
        chat_bot = bot_class(
            nc,
            external_agent_event_distributor,
            agent_class,
            agent_id,
            path,
            typing_timeout_seconds=typing_timeout_seconds,
        )
        adapter: CloudAdapter = RoutesService.get_adapter(path)

        result = await adapter.process(request, chat_bot)
        logger.info("Agent chat completion successful")
        return result

    def completions_json(
        self,
        route: str = "/completions/{agent_class}/{agent_id}/json",
        typing_timeout_seconds: int = 60,
    ) -> Self:
        @self.router.post(
            route,
            summary="Synchronous chat completions",
            description="Handles chat completions by sending a single response Activity to the Azure Bot Service.",
            tags=self.tags,
            response_model=None,
            responses={
                200: {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {}},
                            "example": {},
                        }
                    },
                },
            },
        )
        async def json_chat(
            request: Request,
            _: Annotated[Activity, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
        ) -> Response:
            return await self._process_agent_chat_request(
                request=request,
                nc=nc,
                external_agent_event_distributor=external_agent_event_distributor,
                agent_class=agent_class,
                agent_id=agent_id,
                bot_class=AgentChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

        return self

    def completions_stream(
        self,
        route: str = "/completions/{agent_class}/{agent_id}/stream",
        typing_timeout_seconds: int = 60,
    ) -> Self:
        @self.router.post(
            route,
            summary="Asynchronous chat completions",
            description="Handles chat completions by updating the response Activity as responses are produced.",
            tags=self.tags,
            response_model=None,
            responses={
                200: {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {}},
                            "example": {},
                        }
                    },
                },
            },
        )
        async def stream_chat(
            request: Request,
            _: Annotated[Activity, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
        ) -> Response:
            return await self._process_agent_chat_request(
                request=request,
                nc=nc,
                external_agent_event_distributor=external_agent_event_distributor,
                agent_class=agent_class,
                agent_id=agent_id,
                bot_class=StreamAgentChatBot,
                typing_timeout_seconds=typing_timeout_seconds,
            )

        return self
