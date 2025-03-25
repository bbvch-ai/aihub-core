import asyncio
from asyncio import Task, Event

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from botframework.connector import Channels
from openai import AsyncAzureOpenAI, AsyncOpenAI, BadRequestError
from typing_extensions import override

from aihub_bot.routes.openai.OpenaiChatService import OpenaiChatService


class OpenaiChatBot(ActivityHandler):
    """
    ### What
    - Handle incoming chat messages directed at an LLM.
    - Responds with a single `Activity` containing the answer of the LLM.

    ### Why
    - The LLM can be reached over multiple channels (e.g. Slack, Teams, ...).
    """

    def __init__(
        self,
        model_name: str,
        client: AsyncOpenAI | AsyncAzureOpenAI,
        path: str,
    ):
        self.model_name = model_name
        self.client = client
        self.path = path

    @override
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        if (
            turn_context.activity.channel_id == Channels.ms_teams
            and turn_context.activity.members_added is not None
            and turn_context.activity.recipient.id in [member.id for member in turn_context.activity.members_added]
        ):
            OpenaiChatService.delete_conversation_if_exists(turn_context=turn_context)

        return super().on_conversation_update_activity(turn_context)

    @override
    async def on_message_activity(self, turn_context: TurnContext):
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
            response = await OpenaiChatService.json_chat_completion(
                turn_context=turn_context,
                path=self.path,
                model_name=self.model_name,
                client=self.client,
            )

            typing_stop_signal.set()
            await typing
            await turn_context.send_activity(response)
        except BadRequestError as e:
            response = e.body["message"]
            await typing
            await turn_context.send_activity(response)

        OpenaiChatService.add_bot_message_to_conversation(
            path=self.path,
            turn_context=turn_context,
            message=response,
        )
