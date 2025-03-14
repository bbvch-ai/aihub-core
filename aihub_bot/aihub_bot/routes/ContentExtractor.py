import base64
from enum import Enum
from typing import Dict, List, Optional

import httpx
from botbuilder.schema import Activity, Attachment
from botframework.connector import Channels
from pydantic import BaseModel, Field

from aihub_bot.persistence.entities.ConversationEntity import Content
from aihub_bot.persistence.entities.PathEntity import PathEntity
from aihub_lib.testing.logging.logger import enable_logging

logger = enable_logging()


class FileSource(Enum):
    SLACK = Channels.slack
    TEAMS = Channels.ms_teams
    GENERIC = "generic"


class FileInfo(BaseModel):
    """Normalized file information across different platforms."""

    name: str = Field(..., description="Name of the file")
    content_type: str = Field(..., description="MIME type of the file")
    url: str = Field(..., description="URL of the file")
    content_bytes: Optional[bytes] = Field(None, description="Content of the file in bytes")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers for the file")
    source: FileSource = Field(FileSource.GENERIC, description="Source of the file (e.g., Slack, Teams, etc.)")


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
                try:
                    if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                        file_info = ContentExtractor._from_teams_file(attachment)
                    elif (
                        activity.channel_id == Channels.ms_teams
                        and attachment.content_url is None
                        and attachment.content_type == "text/html"
                    ):
                        # Teams always sends an HTML attachment with the message content
                        # We skip this as it is not a file and already handled
                        continue
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
