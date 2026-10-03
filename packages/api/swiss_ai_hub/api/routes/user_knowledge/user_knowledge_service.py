import asyncio
import posixpath
from collections.abc import Callable
from urllib.parse import quote

from bson import ObjectId
from fastapi import HTTPException, Response, UploadFile, status
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import ConversationAttachments, OpenTerminalClient, SandboxHomePath, trace_fn
from swiss_ai_hub.core.persistence import OpenWebuiAccountEntity, ThreadEntity

from swiss_ai_hub.api.routes.user_knowledge.dto.file_entry_dto import FileEntryDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.file_path_dto import FilePathDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.folder_listing_dto import FolderListingDTO


class UserKnowledgeService:
    """The signed-in user's own file space: their home in the code sandbox, where agents work for them.

    Paths are relative to that home and never leave it. Dotfiles stay hidden, being the sandbox's and tools' own.
    """

    CONVERSATIONS_FOLDER = "conversations"
    MAX_UPLOAD_BYTES = 100 * 1024 * 1024
    SHOWN_IN_PLACE = frozenset(
        {"application/pdf", "image/png", "image/jpeg", "image/gif", "image/webp", "text/plain", "text/csv"}
    )

    @staticmethod
    def client_for(user: UserIdentity) -> OpenTerminalClient:
        openwebui_id = OpenWebuiAccountEntity.openwebui_id_of(user.id)
        if openwebui_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Your file space is set up with your chat account; open the chat once to create it.",
            )
        return OpenTerminalClient(openwebui_id)

    @staticmethod
    @trace_fn
    async def list_folder(user: UserIdentity, folder: str) -> FolderListingDTO:
        relative = SandboxHomePath.shown(folder)
        listing = await UserKnowledgeService.client_for(user).list_files(relative)
        entries = [entry for entry in listing.get("entries", []) if not entry["name"].startswith(".")]
        titles = (
            UserKnowledgeService._conversation_titles(user, [entry["name"] for entry in entries])
            if relative == UserKnowledgeService.CONVERSATIONS_FOLDER
            else {}
        )
        dtos = [FileEntryDTO.from_entry(relative, entry, titles.get(entry["name"])) for entry in entries]
        parent, name = posixpath.split(relative)
        folder_title = (
            UserKnowledgeService._conversation_titles(user, [name]).get(name)
            if parent == UserKnowledgeService.CONVERSATIONS_FOLDER
            else None
        )
        return FolderListingDTO(
            folder=relative,
            entries=sorted(dtos, key=lambda dto: (dto.kind != "folder", dto.name)),
            folder_title=folder_title,
        )

    @staticmethod
    @trace_fn
    async def file_content(user: UserIdentity, path: str, download: bool) -> Response:
        """Agents write these files, so only types a browser cannot run script from are shown in place.

        An HTML or SVG file shown inline would run its script on the API's origin; every other type is sent as a
        download, and the response forbids sniffing and scripting either way.
        """
        relative = SandboxHomePath.shown(path)
        content, content_type = await UserKnowledgeService.client_for(user).view(relative)
        media_type = content_type.split(";")[0].strip().lower()
        shown = not download and media_type in UserKnowledgeService.SHOWN_IN_PLACE
        filename = quote(posixpath.basename(relative))
        return Response(
            content=content,
            media_type=media_type if shown else "application/octet-stream",
            headers={
                "Content-Disposition": f"{'inline' if shown else 'attachment'}; filename*=UTF-8''{filename}",
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "sandbox; default-src 'none'",
            },
        )

    @staticmethod
    @trace_fn
    async def upload(user: UserIdentity, folder: str, file: UploadFile) -> FilePathDTO:
        relative = SandboxHomePath.shown(folder)
        name = SandboxHomePath.name(file.filename or "")
        path = SandboxHomePath.shown(name, relative)
        content = await UserKnowledgeService._read_bounded(file)
        await UserKnowledgeService.client_for(user).upload(relative, name, content)
        return FilePathDTO(path=path)

    @staticmethod
    @trace_fn
    async def create_folder(user: UserIdentity, path: str) -> FilePathDTO:
        relative = UserKnowledgeService._below_top(path)
        await UserKnowledgeService.client_for(user).mkdir(relative)
        return FilePathDTO(path=relative)

    @staticmethod
    @trace_fn
    async def move(user: UserIdentity, source: str, destination: str) -> FilePathDTO:
        relative_destination = UserKnowledgeService._below_top(destination)
        SandboxHomePath.name(posixpath.basename(relative_destination))
        await UserKnowledgeService.client_for(user).move(UserKnowledgeService._below_top(source), relative_destination)
        return FilePathDTO(path=relative_destination)

    @staticmethod
    @trace_fn
    async def delete(user: UserIdentity, path: str) -> FilePathDTO:
        relative = UserKnowledgeService._below_top(path)
        await UserKnowledgeService.client_for(user).delete(relative)
        return FilePathDTO(path=relative)

    @staticmethod
    @trace_fn
    async def place_attachment(
        user: UserIdentity, thread_id: str, file_id: str, filename: str, read: Callable[[], bytes]
    ) -> FilePathDTO | None:
        """A file attached in a chat also lands in that conversation's folder, once: the chat client validates it on
        every turn, and a file the user has since deleted or changed there is theirs to keep that way. A user without
        a file space yet has none to place it in."""
        openwebui_id = OpenWebuiAccountEntity.openwebui_id_of(user.id)
        if openwebui_id is None:
            return None
        attachments = ConversationAttachments(OpenTerminalClient(openwebui_id), thread_id)
        placed = await attachments.place(
            {file_id: SandboxHomePath.name(filename)}, lambda _file_id, _filename: asyncio.to_thread(read)
        )
        return FilePathDTO(path=placed[file_id])

    @staticmethod
    async def _read_bounded(file: UploadFile) -> bytes:
        """The upload's bytes, refused once past the limit, so an oversized body is never held in memory whole."""
        too_large = HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The file is too large.")
        if file.size is not None and file.size > UserKnowledgeService.MAX_UPLOAD_BYTES:
            raise too_large
        content = await file.read(UserKnowledgeService.MAX_UPLOAD_BYTES + 1)
        if len(content) > UserKnowledgeService.MAX_UPLOAD_BYTES:
            raise too_large
        return content

    @staticmethod
    def _below_top(path: str) -> str:
        """A path inside the file space other than its top, which is not renamed, moved or deleted."""
        relative = SandboxHomePath.shown(path)
        if relative == ".":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The top folder cannot be changed.")
        return relative

    @staticmethod
    def _conversation_titles(user: UserIdentity, folder_names: list[str]) -> dict[str, str]:
        """Conversation folders are named by thread id; only threads the user takes part in give their title."""
        ids = [ObjectId(name) for name in folder_names if ObjectId.is_valid(name)]
        threads = ThreadEntity.objects(id__in=ids, users__user_id=user.id).only("id", "name")
        return {str(thread.id): thread.name for thread in threads}
