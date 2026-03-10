from swiss_ai_hub.bot.bots.chat.BaseChatBot import BaseChatBot
from swiss_ai_hub.bot.bots.chat.openai.OpenaiCompletionHandler import OpenaiCompletionHandler


class OpenaiChatBot(BaseChatBot):
    def __init__(
        self,
        model_name: str,
        path: str,
        typing_timeout_seconds: int = 60,
    ):
        super().__init__(
            path=path,
            completion_handler=OpenaiCompletionHandler(),
            handler_kwargs={
                "model_name": model_name,
            },
            typing_timeout_seconds=typing_timeout_seconds,
        )
