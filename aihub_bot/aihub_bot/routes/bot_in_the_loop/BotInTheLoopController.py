from typing import Annotated

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Depends, Request, Response
from nats.aio.client import Client as NATS

from aihub_bot.bots.bot_in_the_loop.BotInTheLoopBot import BotInTheLoopBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler
from aihub_bot.routes.RoutesService import RoutesService


class BotInTheLoopController(Controller):
    name = LocaleString(en="Human In The Loop Bot")
    description = LocaleString(en="Human In The Loop Bot")

    def __init__(self, route: str = "/bot_in_the_loop", is_admin_only=False):
        super().__init__(route, is_admin_only=is_admin_only)

    def bot_in_the_loop_response(self, route: str = "/response") -> "BotInTheLoopController":
        @self.router.post(
            route,
            summary="Human In The Loop Response",
            description="Handles Human In The Loop responses by publishing them to the NATS server.",
            tags=self.tags,
            response_model=None,
        )
        async def bot_in_the_loop_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            nc: Annotated[NATS, Depends(use_nats)],
            external_event_distributor: Annotated[ExternalEventDistributor, Depends(use_external_event_distributor)],
            bot_in_the_loop_handler: Annotated[
                BotInTheLoopHandler, Depends(BotInTheLoopHandler.use_bot_in_the_loop_handler)
            ],
        ) -> Response:
            path: str = RoutesService.get_path(request)
            chat_bot: BotInTheLoopBot = BotInTheLoopBot(
                nc=nc,
                external_event_distributor=external_event_distributor,
                bot_in_the_loop_handler=bot_in_the_loop_handler,
            )
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
