import json
import posixpath
from collections.abc import Awaitable, Callable
from http import HTTPStatus

from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_client import OpenTerminalClient
from swiss_ai_hub.core.infrastructure.open_terminal.open_terminal_error import OpenTerminalError


class ConversationAttachments:
    """The files attached in one conversation, placed in its folder of the user's sandbox home, each once.

    Both the API, when a file is uploaded, and an agent, before its first sandbox call, place them here. Placed files
    are recorded by id in the folder, so a file the user or the code deleted, renamed or changed is never put back, and
    a later file with a taken name is placed beside the first instead of over it.
    """

    CONVERSATIONS_FOLDER = "conversations"
    RECORD = ".attached_files.json"

    def __init__(self, client: OpenTerminalClient, thread_id: str) -> None:
        self._client = client
        self.folder = posixpath.join(self.CONVERSATIONS_FOLDER, thread_id)

    async def place(self, files: dict[str, str], read: Callable[[str, str], Awaitable[bytes]]) -> dict[str, str]:
        """Place the files, given as file id to name, that are not placed yet; `read` fetches one by id and name.

        Returns where each placed file lies, by file id, relative to the home."""
        if not files:
            return {}
        placed = await self._placed()
        new_files = {file_id: name for file_id, name in files.items() if file_id not in placed}
        if new_files:
            taken = await self._present_names() | set(placed.values())
            for file_id, filename in new_files.items():
                name = self._free_name(filename, taken)
                await self._client.upload(self.folder, name, await read(file_id, filename))
                placed[file_id] = name
                taken.add(name)
            await self._client.write_file(posixpath.join(self.folder, self.RECORD), json.dumps(placed))
        return {file_id: posixpath.join(self.folder, placed[file_id]) for file_id in files}

    async def _placed(self) -> dict[str, str]:
        try:
            content, _ = await self._client.view(posixpath.join(self.folder, self.RECORD))
        except OpenTerminalError as error:
            if error.status_code == HTTPStatus.NOT_FOUND:
                return {}
            raise
        return json.loads(content)

    async def _present_names(self) -> set[str]:
        try:
            listing = await self._client.list_files(self.folder)
        except OpenTerminalError as error:
            if error.status_code == HTTPStatus.NOT_FOUND:
                return set()
            raise
        return {entry["name"] for entry in listing.get("entries", [])}

    @staticmethod
    def _free_name(filename: str, taken: set[str]) -> str:
        stem, extension = posixpath.splitext(filename)
        name, number = filename, 1
        while name in taken:
            number += 1
            name = f"{stem} ({number}){extension}"
        return name
