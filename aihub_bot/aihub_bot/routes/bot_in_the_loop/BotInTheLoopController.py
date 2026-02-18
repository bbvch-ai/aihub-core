from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_agent_event_distributor import (
    use_external_agent_event_distributor,
)
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Request, Response
from microsoft_agents.activity import Activity
from microsoft_agents.hosting.aiohttp import CloudAdapter
from nats.aio.client import Client as NATS

from aihub_bot.bots.bot_in_the_loop.BotInTheLoopBot import BotInTheLoopBot
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler
from aihub_bot.routes.RoutesService import RoutesService


class BotInTheLoopController(Controller):
    name = LocaleString(en="Bot In The Loop Bot")
    description = LocaleString(en="Bot In The Loop Bot")

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = BotInTheLoopHandler.CONTROLLER_PATH,
        additionally_required_permission: str | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def bot_in_the_loop_response(self, route: str = BotInTheLoopHandler.ENDPOINT_PATH) -> Self:
        @self.router.post(route, tags=self.tags)
        async def bot_in_the_loop_chat(
            request: Request,
            _: Annotated[Activity, Body],  # openapi request body
            nc: Annotated[NATS, Depends(use_nats)],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            bot_in_the_loop_handler: Annotated[
                BotInTheLoopHandler, Depends(BotInTheLoopHandler.use_bot_in_the_loop_handler)
            ],
        ) -> Response:
            path: str = RoutesService.get_path(request)
            bot_in_the_loop_handler.path = path
            chat_bot: BotInTheLoopBot = BotInTheLoopBot(
                nc=nc,
                external_agent_event_distributor=external_agent_event_distributor,
                bot_in_the_loop_handler=bot_in_the_loop_handler,
            )
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
