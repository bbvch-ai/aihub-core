from typing import Annotated, __all__

from typing_extensions import override

from aihub_bot.bots.hitl.HitlBot import HitlBot
from aihub_bot.routes.hitl.HitlHandler import HitlHandler
from aihub_bot.runners.BotRunner import BotRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.events import BaseEvent, HumanInTheLoopRequestEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics import AgentTopic
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Depends, Path, Request, Response, FastAPI
from nats.aio.client import Client as NATS

from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.RoutesService import RoutesService


class HitlController(Controller):
    name = LocaleString(en="Human In The Loop Bot")
    description = LocaleString(en="Human In The Loop Bot")

    def __init__(self, route: str = "/hitl", is_admin_only=False):
        super().__init__(route, is_admin_only=is_admin_only)

    def hitl_response(self, route: str = "/response") -> "HitlController":
        @self.router.post(
            route,
            summary="Human In The Loop Response",
            description="Handles Human In The Loop responses by publishing them to the NATS server.",
            tags=self.tags,
            response_model=None,
        )
        async def hitl_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            nc: Annotated[NATS, Depends(use_nats)],
            external_event_distributor: Annotated[ExternalEventDistributor, Depends(use_external_event_distributor)],
            hitl_handler: Annotated[HitlHandler, Depends(HitlHandler.use_hitl_handler)],
        ) -> Response:
            path: str = RoutesService.get_path(request)
            chat_bot: HitlBot = HitlBot(
                nc=nc,
                external_event_distributor=external_event_distributor,
                hitl_handler=hitl_handler,
            )
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
