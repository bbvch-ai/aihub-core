from botbuilder.core import ActivityHandler, TurnContext
from openai import AsyncAzureOpenAI, AsyncOpenAI
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
    async def on_message_activity(self, turn_context: TurnContext):
        OpenaiChatService.add_user_message_to_conversation(turn_context)

        if turn_context.activity.channel_id == "slack":
            turn_context = OpenaiChatService.update_slack_turn_context(turn_context)

        OpenaiChatService.get_system_message(
            turn_context=turn_context,
            path=self.path,
        )

        response = await OpenaiChatService.json_chat_completion(
            turn_context=turn_context,
            path=self.path,
            model_name=self.model_name,
            client=self.client,
        )

        OpenaiChatService.add_bot_message_to_conversation(
            turn_context=turn_context,
            message=response,
        )

        return await turn_context.send_activity(response)
