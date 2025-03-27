from openai import AsyncAzureOpenAI, AsyncOpenAI

from aihub_bot.bots.BaseChatBot import BaseChatBot
from aihub_bot.bots.openai.OpenaiCompletionHandler import OpenaiCompletionHandler


class OpenaiChatBot(BaseChatBot):
    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        path: str,
    ):
        super().__init__(
            path=path,
            completion_handler=OpenaiCompletionHandler(),
            handler_kwargs={
                "model_name": model_name,
                "client": client,
            },
        )
