from typing import List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from nats.aio.client import Client as NATS


class EchoBot(ActivityHandler):
    nc: NATS = None

    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        return await turn_context.send_activity(f"I heard you say: {turn_context.activity.text}")
