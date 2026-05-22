import base64
import logging
from enum import StrEnum
from typing import Annotated

import httpx
from microsoft_agents.activity import Activity, Attachment, Channels
from pydantic import BaseModel, Field

from swiss_ai_hub.bot.persistence.entities.conversation_entity import Content
from swiss_ai_hub.bot.persistence.entities.path_entity import PathEntity

logger = logging.getLogger(__name__)


class FileSource(StrEnum):
    SLACK = Channels.slack
    TEAMS = Channels.ms_teams
    GENERIC = "generic"


class FileInfo(BaseModel):
    """Normalized file information across different platforms."""

    name: Annotated[str, Field(description="Name of the file")]
    content_type: Annotated[str | None, Field(description="MIME type of the file")] = None
    url: Annotated[str, Field(description="URL of the file")]
    content_bytes: Annotated[bytes | None, Field(description="Content of the file in bytes")] = None
    headers: Annotated[dict[str, str], Field(description="HTTP headers for the file")] = {}
    source: Annotated[FileSource, Field(description="Source of the file (e.g., Slack, Teams, etc.)")] = (
        FileSource.GENERIC
    )


class ContentExtractor:
    """Unified handler for file processing from various sources."""

    @staticmethod
    def extract_content_from_activity(path: str, activity: Activity) -> list[Content]:
        """Extract all content (text and files) from an activity."""
        content = []

        content.extend(ContentExtractor._extract_text_content(activity))
        content.extend(ContentExtractor._extract_slack_files(path, activity))
        content.extend(ContentExtractor._extract_attachments(activity))

        # Ensure we have at least some content
        if not content:
            logger.warning(f"Activity has no content: {activity}")
            content.append(Content(text="<no-content></no-content>", type="text"))

        return content

    @staticmethod
    def _extract_text_content(activity: Activity) -> list[Content]:
        """Extract text content from activity."""
        text = activity.text or ""

        # For Teams, use HTML content if available (contains emojis in correct positions)
        if activity.channel_id == Channels.ms_teams and activity.attachments:
            for attachment in activity.attachments:
                if attachment.content_type == "text/html" and attachment.content:
                    # Use the HTML directly - LLMs can parse it and extract emojis from alt attributes
                    text = attachment.content
                    break

        if not text:
            return []

        logger.debug(f"Text content (repr): {repr(text)}")
        return [Content(text=text, type="text")]

    @staticmethod
    def _extract_slack_files(path: str, activity: Activity) -> list[Content]:
        """Extract files from Slack channel data."""
        content = []

        if not isinstance(activity.channel_data, dict):
            return content

        slack_files = activity.channel_data.get("SlackMessage", {}).get("event", {}).get("files", [])
        if not slack_files:
            return content

        slack_token = PathEntity.get_slack_token_by_path(path)
        if not slack_token:
            return content

        for file in slack_files:
            try:
                file_info = ContentExtractor._from_slack_file(file, slack_token)
                content.append(ContentExtractor._to_content(file_info))
            except Exception as e:
                logger.exception(f"Error processing Slack file: {e}")

        return content

    @staticmethod
    def _extract_attachments(activity: Activity) -> list[Content]:
        """Extract files from activity attachments."""
        content = []

        if not activity.attachments:
            return content

        for attachment in activity.attachments:
            # Skip Teams HTML content that's not a real file (already extracted from activity.text)
            if (
                activity.channel_id == Channels.ms_teams
                and attachment.content_url is None
                and attachment.content_type == "text/html"
            ):
                continue

            # Skip emoji image attachments without names (unicode is already in activity.text)
            if not attachment.name or not attachment.content_url:
                logger.debug(
                    f"Skipping attachment without name or URL (likely emoji): "
                    f"name={attachment.name}, url={attachment.content_url}, type={attachment.content_type}"
                )
                continue

            try:
                if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                    file_info = ContentExtractor._from_teams_file(attachment)
                else:
                    file_info = ContentExtractor._from_generic_attachment(attachment)

                content.append(ContentExtractor._to_content(file_info))
            except Exception as e:
                logger.exception(f"Error processing attachment: {e}")
                content.append(
                    Content(
                        text=f"<file name='{attachment.name or 'unknown'}'>Error processing file: {str(e)}</file>",
                        type="text",
                    )
                )

        return content

    @staticmethod
    def _from_slack_file(file: dict, slack_token: str) -> FileInfo:
        """Create FileInfo from a Slack file."""
        return FileInfo(
            name=file["name"],
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
            url=attachment.content["downloadUrl"],
            source=FileSource.TEAMS,
        )

    @staticmethod
    def _from_generic_attachment(attachment: Attachment) -> FileInfo:
        """Create FileInfo from a generic attachment."""
        if not attachment.name or not attachment.content_url:
            raise ValueError("Invalid generic attachment: missing name or URL")

        return FileInfo(
            name=attachment.name,
            url=attachment.content_url,
            source=FileSource.GENERIC,
        )

    @staticmethod
    def _fetch_file(file_info: FileInfo) -> FileInfo:
        try:
            response = httpx.get(file_info.url, headers=file_info.headers)
            response.raise_for_status()

            file_info.content_bytes = response.content
            file_info.content_type = response.headers.get("content-type")

        except Exception as e:
            logger.exception(f"Error fetching file {file_info.name}: {e}")
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

        if file_info.content_type and file_info.content_type.startswith("image/"):
            data_url = ContentExtractor._to_base64_data_url(file_info)
            return Content(text=data_url, type="image_url")

        elif file_info.content_type == "application/pdf":
            # PDF files are not supported, return a placeholder
            return Content(text=f"<file name='{file_info.name}'>PDF files are not supported yet</file>", type="text")

        elif file_info.content_type and file_info.content_type.startswith(("text/", "application/")):
            try:
                text = file_info.content_bytes.decode("utf-8", errors="replace")
                return Content(text=f"<file name='{file_info.name}'>{text}</file>", type="text")
            except Exception as e:
                logger.exception(f"Error decoding file {file_info.name}: {e}")

        # Default case for unsupported types
        logger.warning(f"Unsupported file type: {file_info.content_type}")
        return Content(
            text=f"<file name='{file_info.name}'>Unsupported file type: {file_info.content_type}</file>", type="text"
        )
