from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class SlackMessage:
    """Represents a message received from Slack"""

    text: str
    user: str
    username: str
    channel: str
    ts: str
    thread_ts: str | None = None


class SlackDirectClient:
    """
    Direct Slack Web API client for posting messages and receiving responses.
    Uses the official Slack Web API without Bot Framework dependency.
    """

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://slack.com/api"
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def post_message(self, channel: str, text: str, thread_ts: str | None = None) -> dict[str, Any]:
        """
        Post a message to a Slack channel using chat.postMessage API

        Args:
            channel: Channel ID (e.g., "C1234567890")
            text: Message text to send
            thread_ts: Optional timestamp to reply in thread

        Returns:
            Slack API response dict

        Raises:
            httpx.HTTPError: If request fails
            ValueError: If Slack API returns error
        """
        payload = {"channel": channel, "text": text}

        if thread_ts:
            payload["thread_ts"] = thread_ts

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/chat.postMessage", headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            if not data.get("ok", False):
                raise ValueError(f"Slack API error: {data.get('error', 'unknown error')}")

            return data

    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """
        Get user information using users.info API

        Args:
            user_id: Slack user ID

        Returns:
            User information dict
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/users.info", headers=self.headers, params={"user": user_id})
            response.raise_for_status()

            data = response.json()
            if not data.get("ok", False):
                raise ValueError(f"Slack API error: {data.get('error', 'unknown error')}")

            return data["user"]

    async def get_channel_history(
        self, channel: str, oldest: str | None = None, latest: str | None = None, limit: int = 100
    ) -> dict[str, Any]:
        """
        Get channel message history using conversations.history API

        Args:
            channel: Channel ID
            oldest: Only messages after this timestamp
            latest: Only messages before this timestamp
            limit: Maximum number of messages to return

        Returns:
            Channel history response dict
        """
        params = {"channel": channel, "limit": limit}

        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/conversations.history", headers=self.headers, params=params)
            response.raise_for_status()

            data = response.json()
            if not data.get("ok", False):
                raise ValueError(f"Slack API error: {data.get('error', 'unknown error')}")

            return data

    async def get_thread_replies(self, channel: str, ts: str) -> dict[str, Any]:
        """
        Get replies to a thread using conversations.replies API

        Args:
            channel: Channel ID
            ts: Timestamp of parent message

        Returns:
            Thread replies response dict
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/conversations.replies", headers=self.headers, params={"channel": channel, "ts": ts}
            )
            response.raise_for_status()

            data = response.json()
            if not data.get("ok", False):
                raise ValueError(f"Slack API error: {data.get('error', 'unknown error')}")

            return data
