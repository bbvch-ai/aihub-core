import asyncio
import json
import posixpath
import uuid
from http import HTTPStatus
from typing import Self

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import SandboxFileDisplayedEvent, UserUploadedFile
from swiss_ai_hub.core.infrastructure import OpenTerminalClient, OpenTerminalError, create_s3_client
from swiss_ai_hub.core.persistence import OpenWebuiAccountEntity
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext


class SandboxWorkspace:
    """Where a run's sandbox tools work: the asking user's sandbox home, in a folder of its own per conversation.

    The folder holds the files attached to the conversation, so code can work on them without the user attaching
    them again, and relative paths resolve against it. Every write goes through the sandbox's API, never around it.
    """

    CONVERSATIONS_FOLDER = "conversations"
    STAGED_FILES = ".attached_files.json"

    def __init__(self, client: OpenTerminalClient, topic: AgentInstanceTopic, files: list[UserUploadedFile]) -> None:
        self.client = client
        self._topic = topic
        self._files = files
        self.folder = posixpath.join(self.CONVERSATIONS_FOLDER, topic.thread_id)

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
        `~/…` relative to the home. Anything outside the home is refused, whatever the sandbox would allow."""
        if "\0" in path:
            raise OpenTerminalError("A path must not contain NUL characters.")
        if path == "~" or path.startswith("~/"):
            relative = posixpath.normpath(path.removeprefix("~").removeprefix("/") or ".")
        elif path.startswith("/"):
            raise OpenTerminalError(
                f"{path} is an absolute path; use a path inside your home, e.g. ~/{path.lstrip('/')}."
            )
        else:
            relative = posixpath.normpath(posixpath.join(self.folder, path))
        if relative == ".." or relative.startswith("../"):
            raise OpenTerminalError(f"{path} lies outside your home.")
        return relative

    async def prepare(self) -> None:
        """Place each file attached to the conversation in its folder once, under a name no other file there has.

        Staged files are recorded by id in the folder, so a file the code deleted or changed is not put back on the
        next call, and a later file with the same name is added beside the first instead of being skipped."""
        if not self._files:
            return
        staged = await self._staged()
        new_files = [file for file in self._files if file.file_id not in staged]
        if not new_files:
            return
        taken = await self._present_names() | set(staged.values())
        for file in new_files:
            if file.file_id in staged:
                continue
            name = self._free_name(file.filename, taken)
            bucket, key = file.resolve_s3_location(self._topic.agent_class, self._topic.agent_id)
            content = await asyncio.to_thread(self._download, bucket, key)
            await self.client.upload(self.folder, name, content)
            staged[file.file_id] = name
            taken.add(name)
        await self.client.write_file(self.path(self.STAGED_FILES), json.dumps(staged))

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

    @staticmethod
    def _download(bucket: str, key: str) -> bytes:
        return create_s3_client().get_object(Bucket=bucket, Key=key)["Body"].read()

    async def _staged(self) -> dict[str, str]:
        try:
            content, _ = await self.client.view(self.path(self.STAGED_FILES))
        except OpenTerminalError as error:
            if error.status_code == HTTPStatus.NOT_FOUND:
                return {}
            raise
        return json.loads(content)

    @staticmethod
    def _free_name(filename: str, taken: set[str]) -> str:
        stem, extension = posixpath.splitext(filename)
        name, number = filename, 1
        while name in taken:
            number += 1
            name = f"{stem} ({number}){extension}"
        return name

    async def _present_names(self) -> set[str]:
        try:
            listing = await self.client.list_files(self.folder)
        except OpenTerminalError:
            return set()
        return {entry["name"] for entry in listing.get("entries", [])}
