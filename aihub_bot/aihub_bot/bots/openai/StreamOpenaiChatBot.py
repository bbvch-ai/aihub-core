import asyncio
from asyncio import Event, Task
from typing import AsyncGenerator

from botbuilder.core import TurnContext
from openai import BadRequestError
from typing_extensions import override

from aihub_bot.bots.openai.OpenaiChatBot import OpenaiChatBot
from aihub_bot.routes.openai.OpenaiChatService import OpenaiChatService


class StreamOpenaiChatBot(OpenaiChatBot):
    """
    See `OpenaiChatBot` for more information.

    ### What
    - Responds with an initial `Activity`, which is then asynchronously updated with the OpenAI's responses.

    ### Why
    - Compared to the `OpenaiChatBot`, the user can see the OpenAI's response as it is being generated.
    """

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.channel_id == "webchat":
            return await super().on_message_activity(turn_context)

        typing_stop_signal = Event()
        typing: Task = asyncio.create_task(
            OpenaiChatService.send_typing_activity(
                turn_context=turn_context,
                signal=typing_stop_signal,
            )
        )

        OpenaiChatService.add_user_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
        )

        if turn_context.activity.channel_id == "slack":
            turn_context = OpenaiChatService.handle_slack_message(turn_context)
            if turn_context is None:
                return

        try:
            response_generator: AsyncGenerator[str, None] = await OpenaiChatService.stream_chat_completion(
                turn_context=turn_context,
                path=self.path,
                model_name=self.model_name,
                client=self.client,
            )

            typing_stop_signal.set()
            await typing
            response = await OpenaiChatService.send_response_stream(
                turn_context=turn_context,
                response_generator=response_generator,
            )
        except BadRequestError as e:
            response = e.body["message"]
            await typing
            await turn_context.send_activity(response)

        OpenaiChatService.add_bot_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
            message=response,
        )
