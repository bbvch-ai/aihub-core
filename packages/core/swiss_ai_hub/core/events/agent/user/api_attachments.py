from typing import Any

from llama_index.core.base.llms.types import ChatMessage
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from swiss_ai_hub.core.events.agent.user.inline_file import InlineFile
from swiss_ai_hub.core.events.agent.user.stored_image import StoredImage
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.events.api_payload_context import ApiPayloadContext


class ApiAttachments:
    """What an API caller attaches to a message, files and images, kept out of the event.

    Every attachment of a request is checked before the first is stored, so a refused request leaves nothing behind,
    and the event carries references only.
    """

    @staticmethod
    def files_field(files_field: FieldInfo) -> tuple[Any, FieldInfo]:
        """The API input shape of an event's `files`: uploaded references and inline files, mixed freely."""
        return list[UserUploadedFile | InlineFile] | None, FieldInfo.merge_field_infos(
            files_field,
            description="Files for the agent. Each is either the reference of a file uploaded beforehand, or a "
            "file sent inline as base64, which the API stores before the agent receives its reference.",
        )

    @staticmethod
    async def event_data(api_input: BaseModel, context: ApiPayloadContext) -> dict[str, Any]:
        """An event's data with its inline files and images stored and replaced by references, in the caller's
        order."""
        messages: list[ChatMessage] = getattr(api_input, "messages", [])
        files: list[UserUploadedFile | InlineFile] | None = getattr(api_input, "files", None)
        images = StoredImage.checked_all(messages, context)
        stored_files = await InlineFile.store_all(
            [file for file in files or [] if isinstance(file, InlineFile)], context
        )
        await StoredImage.store_all(images, context)

        event_data = api_input.model_dump(mode="json", exclude_unset=True, exclude={"files", "messages"})
        if "messages" in api_input.model_fields_set:
            event_data["messages"] = [message.model_dump(mode="json") for message in messages]
        if files is not None:
            stored = iter(stored_files)
            event_data["files"] = [
                (next(stored) if isinstance(file, InlineFile) else file).model_dump(mode="json") for file in files
            ]
        return event_data
