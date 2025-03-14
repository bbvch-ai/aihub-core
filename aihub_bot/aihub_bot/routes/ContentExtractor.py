from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, List

import base64
import httpx
import logging

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, Attachment

from aihub_bot.persistence.entities.ConversationEntity import Content
from aihub_bot.persistence.entities.PathEntity import PathEntity

logger = logging.getLogger(__name__)


class FileSource(Enum):
    SLACK = "slack"
    TEAMS = "teams"
    GENERIC = "generic"


@dataclass
class FileInfo:
    """Normalized file information across different platforms."""

    name: str
    content_type: Optional[str] = None
    url: Optional[str] = None
    content_bytes: Optional[bytes] = None
    headers: Optional[Dict[str, str]] = None
    source: FileSource = FileSource.GENERIC

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class ContentExtractor:
    """Unified handler for file processing from various sources."""

    @staticmethod
    def extract_content_from_activity(path: str, activity: Activity) -> List[Content]:
        """Extract all content (text and files) from an activity."""
        content = []

        # Handle text content
        if activity.text:
            content.append(Content(text=activity.text, type="text"))

        # Handle Slack files
        if isinstance(activity.channel_data, dict):
            slack_files = activity.channel_data.get("SlackMessage", {}).get("event", {}).get("files", [])
            if slack_files:
                slack_token = PathEntity.get_slack_token_by_path(path)
                if slack_token:
                    for file in slack_files:
                        try:
                            file_info = ContentExtractor._from_slack_file(file, slack_token)
                            content.append(ContentExtractor._to_content(file_info))
                        except Exception as e:
                            logger.error(f"Error processing Slack file: {e}")

        # Handle attachments (Teams and generic)
        if activity.attachments:
            for attachment in activity.attachments:
                # Skip HTML attachments that are probably just Teams message content
                if attachment.content_type == "text/html":
                    logger.info("Ignoring HTML attachment from Teams message")
                    continue

                try:
                    # Process Teams file attachments
                    if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                        file_info = ContentExtractor._from_teams_file(attachment)
                    # Process generic attachments
                    else:
                        file_info = ContentExtractor._from_generic_attachment(attachment)

                    content.append(ContentExtractor._to_content(file_info))
                except Exception as e:
                    logger.error(f"Error processing attachment: {e}")
                    content.append(
                        Content(
                            text=f"<file name='{attachment.name or 'unknown'}'>Error processing file: {str(e)}</file>",
                            type="text",
                        )
                    )

        # Ensure we have at least some content
        if not content:
            logger.warning(f"Activity has no content: {activity}")
            content.append(Content(text="<no-content></no-content>", type="text"))

        return content

    @staticmethod
    def _from_slack_file(file: dict, slack_token: str) -> FileInfo:
        """Create FileInfo from a Slack file."""
        return FileInfo(
            name=file["name"],
            content_type=file.get("mimetype", "application/octet-stream"),
            url=file["url_private_download"],
            headers={"Authorization": f"Bearer {slack_token}"},
            source=FileSource.SLACK,
        )

    @staticmethod
    def _from_teams_file(attachment: Attachment) -> FileInfo:
        """Create FileInfo from a Teams file attachment."""
        if not isinstance(attachment.content, dict) or "downloadUrl" not in attachment.content:
            raise ValueError(f"Invalid Teams file attachment: {attachment}")

        return FileInfo(
            name=attachment.name,
            content_type=attachment.content_type,
            url=attachment.content["downloadUrl"],
            source=FileSource.TEAMS,
        )

    @staticmethod
    def _from_generic_attachment(attachment: Attachment) -> FileInfo:
        """Create FileInfo from a generic attachment."""
        return FileInfo(
            name=attachment.name,
            content_type=attachment.content_type,
            url=attachment.content_url,
            source=FileSource.GENERIC,
        )

    @staticmethod
    def _fetch_file(file_info: FileInfo) -> FileInfo:
        """Fetch file content if only URL is provided."""
        if file_info.content_bytes is None and file_info.url is not None:
            try:
                response = httpx.get(file_info.url, headers=file_info.headers)
                response.raise_for_status()

                # Update file info with fetched content
                file_info.content_bytes = response.content

                # Use server-provided content type if original wasn't specified
                if not file_info.content_type or file_info.content_type == "application/octet-stream":
                    file_info.content_type = response.headers.get("content-type", "application/octet-stream")

            except Exception as e:
                logger.error(f"Error fetching file {file_info.name}: {e}")
                raise

        return file_info

    @staticmethod
    def _to_base64_data_url(file_info: FileInfo) -> str:
        """Convert file content to a base64 data URL."""
        if file_info.content_bytes is None:
            raise ValueError("File content is missing")

        base64_str = base64.b64encode(file_info.content_bytes).decode("utf-8")
        return f"data:{file_info.content_type};base64,{base64_str}"

    @staticmethod
    def _to_content(file_info: FileInfo) -> Content:
        """Convert FileInfo to a Content object based on content type."""
        # Ensure we have the file content
        file_info = ContentExtractor._fetch_file(file_info)

        # Process by content type
        if file_info.content_type.startswith("image/"):
            data_url = ContentExtractor._to_base64_data_url(file_info)
            return Content(text=data_url, type="image_url")

        elif file_info.content_type.startswith("text/") or file_info.content_type.startswith("application/"):
            try:
                text = file_info.content_bytes.decode("utf-8", errors="replace")
                return Content(text=f"<file name='{file_info.name}'>{text}</file>", type="text")
            except Exception as e:
                logger.error(f"Error decoding file {file_info.name}: {e}")

        # Default case for unsupported types
        logger.warning(f"Unsupported file type: {file_info.content_type}")
        return Content(
            text=f"<file name='{file_info.name}'>Unsupported file type: {file_info.content_type}</file>", type="text"
        )
