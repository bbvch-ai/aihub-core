import asyncio
from datetime import datetime, timedelta
from typing import Any

from .SlackDirectClient import SlackDirectClient, SlackMessage


class SlackResponsePoller:
    """
    Polls Slack channels for responses to messages.
    Implements a simple polling mechanism to check for new messages in threads.
    """

    def __init__(self, client: SlackDirectClient, poll_interval: int = 5):
        self.client = client
        self.poll_interval = poll_interval
        self.active_polls: dict[str, dict[str, Any]] = {}

    async def wait_for_response(self, channel: str, message_ts: str, timeout: int = 300) -> list[SlackMessage]:
        """
        Wait for responses to a specific message in a thread.

        Args:
            channel: Channel ID where message was posted
            message_ts: Timestamp of the original message
            timeout: Maximum time to wait in seconds (default 5 minutes)

        Returns:
            List of SlackMessage objects representing responses

        Raises:
            TimeoutError: If no response received within timeout
        """
        poll_key = f"{channel}:{message_ts}"
        end_time = datetime.now() + timedelta(seconds=timeout)

        self.active_polls[poll_key] = {
            "channel": channel,
            "message_ts": message_ts,
            "start_time": datetime.now(),
            "seen_messages": set(),
        }

        try:
            while datetime.now() < end_time:
                responses = await self._check_for_responses(channel, message_ts)
                if responses:
                    return responses

                await asyncio.sleep(self.poll_interval)

            raise TimeoutError(f"No response received within {timeout} seconds")

        finally:
            self.active_polls.pop(poll_key, None)

    async def _check_for_responses(self, channel: str, message_ts: str) -> list[SlackMessage]:
        """
        Check for new responses in a thread.

        Args:
            channel: Channel ID
            message_ts: Original message timestamp

        Returns:
            List of new SlackMessage objects
        """
        poll_key = f"{channel}:{message_ts}"
        poll_data = self.active_polls.get(poll_key)

        if not poll_data:
            return []

        try:
            # Get thread replies
            thread_data = await self.client.get_thread_replies(channel, message_ts)
            messages = thread_data.get("messages", [])

            new_messages = []
            for msg in messages:
                msg_ts = msg.get("ts")

                # Skip the original message and already seen messages
                if msg_ts == message_ts or msg_ts in poll_data["seen_messages"]:
                    continue

                # Skip bot messages (messages without user field or with bot_id)
                if not msg.get("user") or msg.get("bot_id"):
                    continue

                # Get user info for display name
                try:
                    user_info = await self.client.get_user_info(msg["user"])
                    username = (
                        user_info.get("real_name")
                        or user_info.get("display_name")
                        or user_info.get("name", "Unknown User")
                    )
                except Exception:
                    username = "Unknown User"

                slack_msg = SlackMessage(
                    text=msg.get("text", ""),
                    user=msg["user"],
                    username=username,
                    channel=channel,
                    ts=msg_ts,
                    thread_ts=msg.get("thread_ts"),
                )

                new_messages.append(slack_msg)
                poll_data["seen_messages"].add(msg_ts)

            return new_messages

        except Exception as e:
            # Log error but don't break polling
            print(f"Error checking for responses: {e}")
            return []

    def stop_polling(self, channel: str, message_ts: str):
        """
        Stop polling for responses to a specific message.

        Args:
            channel: Channel ID
            message_ts: Message timestamp
        """
        poll_key = f"{channel}:{message_ts}"
        self.active_polls.pop(poll_key, None)
