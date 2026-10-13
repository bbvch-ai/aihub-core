import asyncio
import posixpath
import uuid
from typing import Self

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import SandboxFileDisplayedEvent, UserUploadedFile
from swiss_ai_hub.core.infrastructure import (
    ConversationAttachments,
    OpenTerminalClient,
    OpenTerminalError,
    SandboxHomePath,
    create_s3_client,
)
from swiss_ai_hub.core.persistence import OpenWebuiAccountEntity
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext


class SandboxWorkspace:
    """Where a run's sandbox tools work: the asking user's sandbox home, in a folder of its own per conversation.

    The folder holds the files attached to the conversation, so code can work on them without the user attaching
    them again, and relative paths resolve against it. Every write goes through the sandbox's API, never around it.
    """

    def __init__(self, client: OpenTerminalClient, topic: AgentInstanceTopic, files: list[UserUploadedFile]) -> None:
        self.client = client
        self._topic = topic
        self._files = files
        self.folder = ConversationAttachments(client, topic.thread_id).folder

    @classmethod
    def of(cls, context: ToolContext) -> Self:
        return cls.for_user(context.user, context.topic, context.files)

    @classmethod
    def for_user(
        cls, user: UserIdentity | None, topic: AgentInstanceTopic | None, files: list[UserUploadedFile]
    ) -> Self:
        """The user's workspace in this conversation, for a step running code without a tool loop as much as a tool."""
        if user is None or topic is None:
            raise OpenTerminalError("The code sandbox needs a signed-in user in a conversation.")
        openwebui_id = OpenWebuiAccountEntity.openwebui_id_of(user.id)
        if openwebui_id is None:
            raise OpenTerminalError("This user has no code sandbox yet; it is set up with their chat account.")
        return cls(OpenTerminalClient(openwebui_id), topic, files)

    def path(self, path: str) -> str:
        """A path as the sandbox resolves it, relative to the home: given relative to the conversation folder, or as
        `~/…` relative to the home; anything outside the home is refused."""
        return SandboxHomePath.of(path, self.folder)

    async def prepare(self) -> None:
        """Place the conversation's attached files in its folder, each once, before the code works on them."""
        files = {file.file_id: file.filename for file in self._files}
        await ConversationAttachments(self.client, self._topic.thread_id).place(files, self._read)

    async def keep(self, path: str) -> SandboxFileDisplayedEvent:
        """Copy a sandbox file into our storage, so what the user was shown outlives the sandbox."""
        content, content_type = await self.client.view(self.path(path))
        filename = posixpath.basename(path.rstrip("/"))
        kept = UserUploadedFile(filename=filename, file_type=content_type, file_id=str(uuid.uuid4()))
        bucket, key = kept.resolve_s3_location(self._topic.agent_class, self._topic.agent_id)
        await asyncio.to_thread(
            create_s3_client().put_object, Bucket=bucket, Key=key, Body=content, ContentType=content_type
        )
        return SandboxFileDisplayedEvent(
            path=self.path(path),
            filename=filename,
            content_type=content_type,
            size=len(content),
            bucket=bucket,
            key=key,
        )

    async def _read(self, file_id: str, _filename: str) -> bytes:
        file = next(file for file in self._files if file.file_id == file_id)
        bucket, key = file.resolve_s3_location(self._topic.agent_class, self._topic.agent_id)
        return await asyncio.to_thread(self._download, bucket, key)

    @staticmethod
    def _download(bucket: str, key: str) -> bytes:
        return create_s3_client().get_object(Bucket=bucket, Key=key)["Body"].read()
