import aiohttp
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SlackIds(BaseModel):
    """Slack identification information returned from auth.test API."""

    bot_id: str
    team_id: str


class SlackUtils:
    """Utility functions for Slack API operations."""

    @staticmethod
    async def get_slack_ids(slack_token: str) -> SlackIds:
        """Use the Slack auth.test API to retrieve the bot ID and team ID."""
        if not slack_token:
            raise ValueError("No Slack token provided")

        try:
            headers = {"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.post("https://slack.com/api/auth.test", headers=headers) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to call auth.test API: {response.status}")

                    data = await response.json()
                    if not data.get("ok", False):
                        raise ValueError(f"auth.test API error: {data.get('error', 'Unknown error')}")

                    # Extract the bot_id and team_id from the response
                    bot_id = data.get("bot_id")
                    team_id = data.get("team_id")

                    if not bot_id or not team_id:
                        raise ValueError(f"Missing bot_id or team_id in auth.test response")

                    logger.info(f"Successfully retrieved Slack IDs - Bot ID: {bot_id}, Team ID: {team_id}")
                    return SlackIds(bot_id=bot_id, team_id=team_id)

        except Exception as e:
            logger.exception(f"Error calling Slack auth.test API")
            raise
