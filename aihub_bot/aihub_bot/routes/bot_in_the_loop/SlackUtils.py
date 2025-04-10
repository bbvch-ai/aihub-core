import aiohttp
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class SlackUtils:
    """Utility functions for Slack API operations."""

    @staticmethod
    async def get_slack_ids(slack_token: str) -> Optional[Tuple[str, str]]:
        """
        Use the Slack auth.test API to retrieve the bot ID and team ID.

        Args:
            slack_token: The Slack API token

        Returns:
            Tuple containing (bot_id, team_id) if successful, None otherwise
        """
        if not slack_token:
            logger.error("No Slack token provided")
            return None

        try:
            headers = {"Authorization": f"Bearer {slack_token}", "Content-Type": "application/json"}

            async with aiohttp.ClientSession() as session:
                async with session.post("https://slack.com/api/auth.test", headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to call auth.test API: {response.status}")
                        return None

                    data = await response.json()
                    if not data.get("ok", False):
                        logger.error(f"auth.test API error: {data.get('error', 'Unknown error')}")
                        return None

                    # Extract the bot_id and team_id from the response
                    bot_id = data.get("bot_id")
                    team_id = data.get("team_id")

                    if not bot_id or not team_id:
                        logger.error(f"Missing bot_id or team_id in auth.test response: {data}")
                        return None

                    logger.info(f"Successfully retrieved Slack IDs - Bot ID: {bot_id}, Team ID: {team_id}")
                    return (bot_id, team_id)

        except Exception as e:
            logger.exception(f"Error calling Slack auth.test API: {str(e)}")
            return None
