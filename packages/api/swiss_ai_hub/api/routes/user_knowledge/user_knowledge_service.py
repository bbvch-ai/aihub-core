import asyncio
import posixpath
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

from bson import ObjectId
from fastapi import HTTPException, Response, UploadFile, status
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai import DocumentExtractor, MarkItDownLoader
from swiss_ai_hub.core.infrastructure import (
    ConversationAttachments,
    OpenTerminalClient,
    OpenTerminalError,
    SandboxHomePath,
    trace_fn,
)
from swiss_ai_hub.core.persistence import OpenWebuiAccountEntity, ThreadEntity

from swiss_ai_hub.api.routes.user_knowledge.dto.file_entry_dto import FileEntryDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.file_path_dto import FilePathDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.file_preview_dto import FilePreviewDTO
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
    # The office formats the agent reads through MarkItDown; mail is left out, and the web lists the same set.
    PREVIEWED_AS_MARKDOWN = frozenset(f".{extension}" for extension in MarkItDownLoader.SUPPORTED_EXTENSIONS) - {
        ".msg",
        ".eml",
    }
    # A preview is for glancing at a file, and a large workbook converts to far more text than a browser renders
    # comfortably; the download keeps the whole of it.
    MAX_PREVIEW_CHARS = 200_000
    # The conversion runs in the API process and holds the whole document several times over while it does, so a
    # file past this is offered as a download instead of converted.
    MAX_PREVIEW_BYTES = 20 * 1024 * 1024

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
        parent, name = posixpath.split(relative)
        folder_title = (
            (await UserKnowledgeService._conversation_titles(user, [name])).get(name)
            if parent == UserKnowledgeService.CONVERSATIONS_FOLDER
            else None
        )
        listing = await UserKnowledgeService._listing(user, relative, folder_title is not None)
        entries = [entry for entry in listing.get("entries", []) if not entry["name"].startswith(".")]
        titles = (
            await UserKnowledgeService._conversation_titles(user, [entry["name"] for entry in entries])
            if relative == UserKnowledgeService.CONVERSATIONS_FOLDER
            else {}
        )
        dtos = [FileEntryDTO.from_entry(relative, entry, titles.get(entry["name"])) for entry in entries]
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
        media_type = UserKnowledgeService._media_type(content_type)
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
    async def preview(user: UserIdentity, path: str) -> FilePreviewDTO:
        """Office documents a browser cannot show, converted the way an agent reads them, so both see the same text."""
        relative = SandboxHomePath.shown(path)
        filename = posixpath.basename(relative)
        if posixpath.splitext(filename)[1].lower() not in UserKnowledgeService.PREVIEWED_AS_MARKDOWN:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="This file type has no preview."
            )
        content, content_type = await UserKnowledgeService.client_for(user).view(relative)
        if len(content) > UserKnowledgeService.MAX_PREVIEW_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="This file is too large to preview; download it instead.",
            )
        document = await DocumentExtractor.extract_from_bytes(
            content=content, filename=filename, content_type=UserKnowledgeService._media_type(content_type)
        )
        truncated = len(document.content) > UserKnowledgeService.MAX_PREVIEW_CHARS
        return FilePreviewDTO(
            path=relative,
            markdown=UserKnowledgeService._shortened(document.content) if truncated else document.content,
            truncated=truncated,
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
    async def place_attachments(
        user: UserIdentity, thread_id: str, files: dict[str, str], read: Callable[[str, str], bytes]
    ) -> list[FilePathDTO]:
        """The files attached in a chat, by file id to name, also land in that conversation's folder, each once: the
        chat client validates them on every turn, and a file the user has since deleted or changed there is theirs to
        keep that way. A user without a file space yet has none to place them in."""
        openwebui_id = OpenWebuiAccountEntity.openwebui_id_of(user.id)
        if openwebui_id is None:
            return []
        attachments = ConversationAttachments(OpenTerminalClient(openwebui_id), thread_id)
        placed = await attachments.place(
            {file_id: SandboxHomePath.name(filename) for file_id, filename in files.items()},
            lambda file_id, filename: asyncio.to_thread(read, file_id, filename),
        )
        return [FilePathDTO(path=path) for path in placed.values()]

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
    def _media_type(content_type: str) -> str:
        return content_type.split(";")[0].strip().lower()

    @staticmethod
    def _shortened(markdown: str) -> str:
        """Cut at the last whole line, closing a table the cut lands in, so the last row and table still render."""
        head = markdown[: UserKnowledgeService.MAX_PREVIEW_CHARS]
        last_line_end = head.rfind("\n")
        if last_line_end != -1:
            head = head[: last_line_end + 1]
        if head.rfind("<table>") > head.rfind("</table>"):
            head += "</table>"
        return head

    @staticmethod
    def _below_top(path: str) -> str:
        """A path inside the file space other than its top, which is not renamed, moved or deleted."""
        relative = SandboxHomePath.shown(path)
        if relative == ".":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The top folder cannot be changed.")
        return relative

    @staticmethod
    async def _listing(user: UserIdentity, relative: str, is_own_conversation: bool) -> dict[str, Any]:
        """A conversation's folder only exists once a file lands in it, yet the user's own chat is theirs to open."""
        try:
            return await UserKnowledgeService.client_for(user).list_files(relative)
        except OpenTerminalError as error:
            if is_own_conversation and error.status_code == status.HTTP_404_NOT_FOUND:
                return {"entries": []}
            raise

    @staticmethod
    async def _conversation_titles(user: UserIdentity, folder_names: list[str]) -> dict[str, str]:
        """Conversation folders are named by thread id; only threads the user takes part in give their title."""
        ids = [ObjectId(name) for name in folder_names if ObjectId.is_valid(name)]
        threads = await ThreadEntity.find({"_id": {"$in": ids}, "users.user_id": user.id}).to_list()
        return {str(thread.id): thread.name for thread in threads}
