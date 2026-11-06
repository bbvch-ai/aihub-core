import logging

import httpx
from cachetools import TTLCache
from microsoft_agents.activity import Channels
from pydantic import BaseModel

from swiss_ai_hub.bot.bots.chat.unverified_bot_user_error import UnverifiedBotUserError

logger = logging.getLogger(__name__)


class SlackIds(BaseModel):
    """Slack identification information returned from auth.test API."""

    bot_id: str
    team_id: str


class SlackUser(BaseModel):
    """What Slack itself holds about a user: the workspace they belong to and the email it vouches for."""

    id: str
    team_id: str
    email: str | None


class SlackUtils:
    """Utility functions for Slack API operations."""

    SLACK_IDS_CACHE_TTL_SECONDS = 60 * 60 * 24 * 30
    _slack_ids_cache: TTLCache = TTLCache(maxsize=100, ttl=SLACK_IDS_CACHE_TTL_SECONDS)

    @staticmethod
    async def get_slack_ids(slack_token: str) -> SlackIds:
        """Bot and team ID of a token via Slack's auth.test, cached because they never change for a token."""
        if not slack_token:
            raise ValueError("No Slack token provided")
        if slack_token in SlackUtils._slack_ids_cache:
            return SlackUtils._slack_ids_cache[slack_token]

        headers = {"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post("https://slack.com/api/auth.test", headers=headers)
        if response.status_code != 200:
            raise ValueError(f"Failed to call auth.test API: {response.status_code}")

        data = response.json()
        if not data.get("ok", False):
            raise ValueError(f"auth.test API error: {data.get('error', 'Unknown error')}")

        bot_id = data.get("bot_id")
        team_id = data.get("team_id")

        if not bot_id or not team_id:
            raise ValueError("Missing bot_id or team_id in auth.test response")

        logger.info(f"Successfully retrieved Slack IDs - Bot ID: {bot_id}, Team ID: {team_id}")
        slack_ids = SlackIds(bot_id=bot_id, team_id=team_id)
        SlackUtils._slack_ids_cache[slack_token] = slack_ids
        return slack_ids

    @staticmethod
    async def get_user(slack_token: str, slack_user_id: str) -> SlackUser:
        """Look the user up in Slack itself, because the activity's display fields are chosen by the sender.

        Requires the `users:read` scope; without `users:read.email` Slack answers but leaves the email out.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://slack.com/api/users.info",
                params={"user": slack_user_id},
                headers={"Authorization": f"Bearer {slack_token}"},
            )
        response.raise_for_status()
        data = response.json()
        if data.get("error") == "missing_scope":
            raise UnverifiedBotUserError(
                Channels.slack, f"the Slack bot token lacks the {data.get('needed', 'users:read')} scope"
            )
        if not data.get("ok", False):
            raise ValueError(f"users.info API error: {data.get('error', 'Unknown error')}")
        user = data["user"]
        return SlackUser(id=user["id"], team_id=user["team_id"], email=user.get("profile", {}).get("email"))
