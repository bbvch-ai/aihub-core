import asyncio
import base64
import binascii
import math
import uuid
from typing import Annotated, Any

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo

from swiss_ai_hub.core.events.agent.user.inline_file_settings import InlineFileSettings
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.events.api_payload_context import ApiPayloadContext


class InlineFile(BaseModel):
    """A file sent inside the request instead of being uploaded first.

    The API stores it in the agent's file bucket before the agent is called, and the agent receives its reference like
    any uploaded file. The bytes never travel in an event: NATS limits a message to one or two megabytes, and every
    event is persisted.
    """

    model_config = ConfigDict(extra="forbid")

    filename: Annotated[
        str,
        Field(
            pattern=r"^[^/\\]+$",
            max_length=255,
            description="The name of the file, including the extension. Must not contain path separators.",
        ),
    ]
    file_type: Annotated[str, Field(description="The MIME type of the file.", examples=["application/pdf"])]
    content: Annotated[
        str,
        Field(description="The file content, base64-encoded.", json_schema_extra={"contentEncoding": "base64"}),
    ]

    @staticmethod
    def accepting_field(files_field: FieldInfo) -> tuple[Any, FieldInfo]:
        """The API input shape of an event's `files`: uploaded references and inline files, mixed freely."""
        return list[UserUploadedFile | InlineFile] | None, FieldInfo.merge_field_infos(
            files_field,
            description="Files for the agent. Each is either the reference of a file uploaded beforehand, or a "
            "file sent inline as base64, which the API stores before the agent receives its reference.",
        )

    @staticmethod
    async def event_data_with_stored_files(api_input: BaseModel, context: ApiPayloadContext) -> dict[str, Any]:
        """An event's data with its inline files stored and replaced by their references, in the caller's order."""
        event_data = api_input.model_dump(mode="json", exclude_unset=True, exclude={"files"})
        files: list[UserUploadedFile | InlineFile] | None = getattr(api_input, "files", None)
        if files is not None:
            stored = iter(await InlineFile.store_all([file for file in files if isinstance(file, InlineFile)], context))
            event_data["files"] = [
                (next(stored) if isinstance(file, InlineFile) else file).model_dump(mode="json") for file in files
            ]
        return event_data

    @staticmethod
    async def store_all(files: list["InlineFile"], context: ApiPayloadContext) -> list[UserUploadedFile]:
        """Every file is checked before the first is stored, so a request with one bad file leaves nothing behind."""
        settings = InlineFileSettings()
        if len(files) > settings.MAX_FILES_PER_REQUEST:
            raise HTTPException(
                status.HTTP_413_CONTENT_TOO_LARGE,
                f"A request may carry at most {settings.MAX_FILES_PER_REQUEST} inline files, got {len(files)}.",
            )
        decoded = [(file, file._checked_bytes(settings)) for file in files]
        return [await file._store(data, context) for file, data in decoded]

    def _checked_bytes(self, settings: InlineFileSettings) -> bytes:
        self._check_type()
        if len(self.content) > 4 * math.ceil(settings.MAX_FILE_BYTES / 3):
            raise self._too_large(settings)
        try:
            data = base64.b64decode(self.content, validate=True)
        except binascii.Error as decode_error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, f"The content of '{self.filename}' is not valid base64."
            ) from decode_error
        if len(data) > settings.MAX_FILE_BYTES:
            raise self._too_large(settings)
        return data

    def _check_type(self) -> None:
        # The loader stack takes seconds to import, and every service imports the events.
        from swiss_ai_hub.core.generative_ai.document.extraction.document_extractor import DocumentExtractor

        if self.file_type.startswith("image/"):
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"'{self.filename}' is an image. Send images as image_url content parts instead.",
            )
        if not DocumentExtractor.can_extract(self.filename, self.file_type):
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"'{self.filename}' has a type agents cannot read ({self.file_type}).",
            )

    def _too_large(self, settings: InlineFileSettings) -> HTTPException:
        return HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"'{self.filename}' is larger than the {settings.MAX_FILE_BYTES} bytes an inline file may have.",
        )

    async def _store(self, data: bytes, context: ApiPayloadContext) -> UserUploadedFile:
        reference = UserUploadedFile(filename=self.filename, file_type=self.file_type, file_id=str(uuid.uuid4()))
        bucket, key = reference.resolve_s3_location(context.agent_class, context.agent_id)
        await asyncio.to_thread(
            context.s3_client.put_object, Bucket=bucket, Key=key, Body=data, ContentType=self.file_type
        )
        return reference
