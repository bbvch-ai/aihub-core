import asyncio
import base64
import logging
import re
from asyncio import Task
from typing import AsyncGenerator, List, Optional, Tuple, cast

import httpx
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, Entity, ActivityTypes, ErrorResponseException, Attachment
from fastapi import Request

from aihub_bot.persistence.entities.ConversationEntity import ConversationEntity, Message, Content
from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity
from aihub_lib.routes.chat.ChatService import ChatService

logger = logging.getLogger(__name__)


class Service(ChatService):
    """
    ### What
    - Shared functionality for all ChatControllers and ChatBots.
    """

    @staticmethod
    def get_path(request: Request) -> str:
        """
        ### What
        - Returns the path/endpoint of the request.

        ### Why
        - Each endpoint can be configured in the database.
        - The path is the key to access this configuration.
        - See `PathEntity`.
        """
        return str(request.url).replace(str(request.base_url), "/")

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        """
        ### What
        - Returns the adapter for the given path.

        ### Why
        - Each path has a unique set of credentials.
        - The credential is needed to verify that requests are coming from the correct bot service.
        """
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))

    @staticmethod
    def get_system_message(turn_context: TurnContext, path: str) -> Optional[Message]:
        """
        ### What
        - Returns the configured system message for the given path.
        - Replaces the placeholder `{username}` with the given username.
        - Replaces the placeholder `{assistant_name}` with the given assistant name.

        ### Why
        - The system message can be configured in the database.
        - The LLM and Agents should get instructions on how to interact with the user.
        - The instructions should be personalized with the user's name.
        """
        system_message: Optional[str] = PathEntity.get_system_message_by_path(path)
        if system_message is None:
            return None
        username = turn_context.activity.from_property.name
        assistant_name = turn_context.activity.recipient.name
        system_message = system_message.format(username=username)
        system_message = system_message.format(assistant_name=assistant_name)
        return Message(
            user_id="system",
            content=[Content(text=system_message, type="text")],
            role="system",
            name="system",
        )

    @staticmethod
    def handle_slack_message(turn_context: TurnContext) -> Optional[TurnContext]:
        is_direct_message = Service.is_slack_direct_message(turn_context)
        is_channel_message = Service.is_slack_channel_message(turn_context)
        is_mentioned = Service.is_bot_mentioned(turn_context)
        is_bot_thread = Service.is_mentioned_in_conversation(turn_context)

        if is_channel_message:
            turn_context = Service.update_slack_turn_context(turn_context)
            if is_mentioned:
                Service.mark_conversation_as_mentioned(turn_context)
        if not is_direct_message and not is_mentioned and not is_bot_thread:
            return None

        return turn_context

    @staticmethod
    def is_slack_channel_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+$")
        return channel_id_regex.match(conversation_id) is not None

    @staticmethod
    def is_slack_direct_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        dm_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:D[0-9A-Z]+:\d+[.]\d+$")
        return dm_id_regex.match(conversation_id) is not None

    @staticmethod
    def is_bot_mentioned(turn_context: TurnContext) -> bool:
        mentions: List[Entity] = turn_context.activity.get_mentions()
        return any(
            mention.additional_properties["mentioned"]["id"] == turn_context.activity.recipient.id
            for mention in mentions
        )

    @staticmethod
    def update_slack_turn_context(turn_context: TurnContext):
        """
        ### What
        1. Change the conversation id to refer to the message *thread* in Slack.
        2. Fetch all messages from the channel and add them to the context.

        ### Why
        1. The Bot should always respond in the same thread as the user's message.
        2. The Bot should have all channel messages to understand the conversation context.
        """
        channel_conversation_id: str = turn_context.activity.conversation.id
        channel_data = turn_context.activity.channel_data
        ts: str = channel_data["SlackMessage"]["event"]["ts"]
        turn_context.activity.conversation.id = channel_conversation_id + f":{ts}"
        parent_messages: List[Message] = Service.get_messages_by_conversation_id(channel_conversation_id)
        Service.add_messages_to_conversation(turn_context, parent_messages)
        return turn_context

    @staticmethod
    def mark_conversation_as_mentioned(turn_context: TurnContext):
        conversation_id: str = turn_context.activity.conversation.id
        ConversationEntity.set_conversation_is_mentioned(conversation_id=conversation_id, is_mentioned=True)

    @staticmethod
    def is_mentioned_in_conversation(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        return ConversationEntity.get_conversation_is_mentioned(conversation_id)

    @staticmethod
    def add_user_message_to_conversation(path: str, turn_context: TurnContext) -> ConversationEntity:
        """
        ### What
        - Add the user message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=Service._activity_to_content(path=path, activity=turn_context.activity),
            role=turn_context.activity.from_property.role or "user",
            name=turn_context.activity.from_property.name,
        )
        return Service.add_messages_to_conversation(turn_context, user_message)

    @staticmethod
    def _activity_to_content(path: str, activity: Activity) -> List[Content]:
        content: List[Content] = []

        if activity.text:
            content.append(Content(text=activity.text, type="text"))

        attachments_handled = False
        if isinstance(activity.channel_data, dict):
            files = activity.channel_data.get("SlackMessage", {}).get("event", {}).get("files")
            if files:
                slack_token = PathEntity.get_slack_token_by_path(path)
                if slack_token:
                    content.extend(Service._slack_files_to_content(files, slack_token))
                    attachments_handled = True

        if not attachments_handled and activity.attachments and len(activity.attachments) > 0:
            content.extend(Service._attachments_to_content(activity.attachments))

        if len(content) == 0:
            logger.warning(f"Activity has no content: {activity}")
            content.append(Content(text="<no-content></no-content>", type="text"))

        return content

    @staticmethod
    def _slack_files_to_content(
        files: List[dict],
        slack_token: str,
    ) -> List[Content]:
        content: List[Content] = []
        for file in files:

            if file.get("mimetype", "").startswith("image/"):
                response = httpx.get(
                    file["url_private_download"],
                    headers={"Authorization": f"Bearer {slack_token}"},
                )
                response.raise_for_status()
                image_bytes: bytes = response.content
                image_base64: str = base64.b64encode(image_bytes).decode("utf-8")
                content.append(
                    Content(text=f"data:{response.headers['content-type']};base64,{image_base64}", type="image_url")
                )
            elif file.get("mimetype") == "text/plain":
                response = httpx.get(
                    file["url_private_download"],
                    headers={"Authorization": f"Bearer {slack_token}"},
                )
                response.raise_for_status()
                content.append(Service._text_file_content(file_name=file["name"], text=response.text))
        return content

    @staticmethod
    def _attachments_to_content(attachments: List[Attachment]) -> List[Content]:
        content: List[Content] = []
        for attachment in attachments:
            url = attachment.content_url
            if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                content.append(Service._handle_teams_file_attachment(attachment))
            elif attachment.content_type.startswith("image/"):
                content.append(Content(text=url, type="image_url"))
            elif attachment.content_type == "text/plain":
                content.append(Service._text_file_attachment_to_content(url, attachment.name))
            elif attachment.content_type == "text/html":
                logger.info(
                    f"Ignoring HTML attachment. This is probably a Teams message. Teams messages always have a text/html attachment with the message content. Attachment: {attachment}"
                )
            else:
                logger.warning(f"Attachment has unsupported content type: {attachment.content_type}.")
                content.append(
                    Content(
                        text=f"<file name='{attachment.name}'>Unsupported content type: {attachment.content_type}</file>",
                        type="text",
                    )
                )
        return content

    @staticmethod
    def _handle_teams_file_attachment(attachment: Attachment) -> Content:
        IMAGE_FILE_TYPES = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"]
        TEXT_FILE_TYPES = ["txt", "log", "md", "csv", "json", "xml", "yaml", "yml", "html", "htm", "css", "js"]
        teams_content: dict = cast(dict, attachment.content)
        teams_url: str = teams_content["downloadUrl"]
        teams_file_type: str = teams_content["fileType"]
        if teams_file_type in IMAGE_FILE_TYPES:
            return Content(text=teams_url, type="image_url")
        elif teams_file_type in TEXT_FILE_TYPES:
            return Service._text_file_attachment_to_content(teams_url, attachment.name)
        else:
            logger.warning(f"File {attachment.name} has unsupported file type {teams_file_type}.")
            return Content(
                text=f"<file name='{attachment.name}'>Unsupported file type: {teams_file_type}</file>", type="text"
            )

    @staticmethod
    def _text_file_attachment_to_content(url: str, file_name: str) -> Content:
        response = httpx.get(url)
        response.raise_for_status()
        return Service._text_file_content(file_name=file_name, text=response.text)

    @staticmethod
    def _text_file_content(file_name: str, text: str) -> Content:
        return Content(text=f"<file name='{file_name}'>{text}</file>", type="text")

    @staticmethod
    def add_bot_message_to_conversation(
        path: str,
        turn_context: TurnContext,
        message: str,
    ) -> ConversationEntity:
        """
        ### What
        - Add the bot message to the persisted conversation.

        ### Why
        - See `add_messages_to_conversation`.
        """
        bot_message = Message(
            user_id=turn_context.activity.recipient.id,
            content=Service._activity_to_content(path=path, activity=Activity(text=message)),
            role=turn_context.activity.recipient.role or "bot",
            name=turn_context.activity.recipient.name,
        )
        return Service.add_messages_to_conversation(turn_context, bot_message)

    @staticmethod
    def add_messages_to_conversation(
        turn_context: TurnContext,
        messages: List[Message] | Message,
    ) -> ConversationEntity:
        """
        ### What
        - Add the given messages to the persisted conversation.

        ### Why
        - The conversation must be persisted to keep the context, because past messages cannot be retrieved
        using from the Bot Framework.
        """
        conversation_id = turn_context.activity.conversation.id
        messages = messages if isinstance(messages, list) else [messages]
        return ConversationEntity.add_messages_to_conversation(
            conversation_id=conversation_id,
            messages=messages,
        )

    @staticmethod
    def get_messages_by_conversation_id(
        conversation_id: str,
    ) -> List[Message]:
        """
        ### What
        - Get all messages from the persisted conversation.

        ### Why
        - To add the messages to the context of the conversation.
        """
        return list(ConversationEntity.get_messages_by_conversation_id(conversation_id) or [])

    @staticmethod
    async def send_response_stream(
        turn_context: TurnContext,
        response_generator: AsyncGenerator[str, None],
    ) -> str:
        """
        ### What
        - Send an initial Activity with the first chunk of the response.
        - Update the Activity with the next chunks of the response.

        ### Why
        - The response can be very long and should be sent in chunks.
        - The user can see the response while it is being generated.
        """

        async def _send_text(
            _turn_context: TurnContext,
            _buffer: str,
            _activity: Optional[Activity] = None,
            _sent_text: str = "",
        ) -> Tuple[Optional[Activity], str]:
            if not _buffer:
                return _activity, _sent_text
            if _activity is None:
                _response = await _turn_context.send_activity(_buffer)
                return Activity(id=_response.id, text=_buffer, type=ActivityTypes.message), ""

            _activity.text = _buffer
            try:
                await _turn_context.update_activity(_activity)
                return _activity, ""
            except ErrorResponseException as e:
                if "msg_too_long" in str(e):
                    new_text = _buffer.replace(_sent_text, "", 1)
                    _response = await _turn_context.send_activity(new_text)
                    return Activity(id=_response.id, text=new_text, type=ActivityTypes.message), _sent_text
                raise e

        response = await anext(response_generator, "No response from the agent.")
        task: Task = asyncio.create_task(_send_text(turn_context, response))

        buffer = response
        sent_text = response
        async for chunk in response_generator:
            if chunk is None:
                break
            buffer += chunk
            response += chunk
            if task.done():
                activity, used_buffer = task.result()
                buffer = buffer.replace(used_buffer, "", 1)
                task = asyncio.create_task(_send_text(turn_context, buffer, activity, sent_text))
                sent_text = buffer

        await task
        activity, used_buffer = task.result()
        buffer = buffer.replace(used_buffer, "", 1)
        await _send_text(turn_context, buffer, activity, sent_text)

        return response
