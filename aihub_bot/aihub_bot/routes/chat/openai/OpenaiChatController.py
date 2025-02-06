import logging
from typing import Annotated, Any, Callable, List

from fastapi import Body, Query
from llama_index.llms.openai import OpenAI
from openai import AsyncOpenAI, AsyncAzureOpenAI
from starlette.requests import Request
from starlette.responses import JSONResponse

from aihub_bot.bots.chat.openai.JsonOpenaiChatBot import JsonOpenaiChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.generative_ai.llms.models.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.routes.Controller import Controller

logger = logging.getLogger(__name__)


class OpenaiChatController(Controller):
    def __init__(
        self,
        route: str = "/openai/chat",
        auth: Callable[..., Any] = None,
        chat_models: List[ChatLLMConfig] = None,
    ):
        super().__init__(route, auth)
        self.chat_models = chat_models or []

        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def chat_completion(self, route: str = "/completions/json", ) -> "OpenaiChatController":
        @self.router.post(route)
        async def chat_completion(
            request: Request,
            _: Annotated[ActivityModel, Body],
            model_name: Annotated[str, Query(title="Model Name")],
        ) -> JSONResponse:
            models = [model for model in self.chat_models if model.name == model_name]
            if len(models) == 0:
                raise ValueError(f"Model {model_name} not found.")
            chat_model_config = models[0]

            chat_model, _ = chat_model_config.to_llama_index()
            client: AsyncOpenAI | AsyncAzureOpenAI = chat_model._get_aclient()

            chat_bot = JsonOpenaiChatBot(model_name, client)
            return await ChatService.ADAPTER.process(request, chat_bot)

        return self
