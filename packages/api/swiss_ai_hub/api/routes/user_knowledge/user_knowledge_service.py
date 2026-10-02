import posixpath
from urllib.parse import quote

from bson import ObjectId
from fastapi import HTTPException, Response, UploadFile, status
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import OpenTerminalClient, SandboxHomePath, trace_fn
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
        relative = SandboxHomePath.of(folder)
        listing = await UserKnowledgeService.client_for(user).list_files(relative)
        entries = [entry for entry in listing.get("entries", []) if not entry["name"].startswith(".")]
        titles = (
            UserKnowledgeService._conversation_titles(user, [entry["name"] for entry in entries])
            if relative == UserKnowledgeService.CONVERSATIONS_FOLDER
            else {}
        )
        dtos = [FileEntryDTO.from_entry(relative, entry, titles.get(entry["name"])) for entry in entries]
        return FolderListingDTO(folder=relative, entries=sorted(dtos, key=lambda dto: (dto.kind != "folder", dto.name)))

    @staticmethod
    @trace_fn
    async def file_content(user: UserIdentity, path: str, download: bool) -> Response:
        relative = SandboxHomePath.of(path)
        content, content_type = await UserKnowledgeService.client_for(user).view(relative)
        disposition = "attachment" if download else "inline"
        filename = quote(posixpath.basename(relative))
        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f"{disposition}; filename*=UTF-8''{filename}"},
        )

    @staticmethod
    @trace_fn
    async def upload(user: UserIdentity, folder: str, file: UploadFile) -> FilePathDTO:
        relative = SandboxHomePath.of(folder)
        name = SandboxHomePath.name(file.filename or "")
        content = await file.read()
        if len(content) > UserKnowledgeService.MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The file is too large.")
        await UserKnowledgeService.client_for(user).upload(relative, name, content)
        return FilePathDTO(path=posixpath.normpath(posixpath.join(relative, name)))

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
        await UserKnowledgeService.client_for(user).move(
            UserKnowledgeService._below_top(source), relative_destination
        )
        return FilePathDTO(path=relative_destination)

    @staticmethod
    @trace_fn
    async def delete(user: UserIdentity, path: str) -> FilePathDTO:
        relative = UserKnowledgeService._below_top(path)
        await UserKnowledgeService.client_for(user).delete(relative)
        return FilePathDTO(path=relative)

    @staticmethod
    def _below_top(path: str) -> str:
        """A path inside the file space other than its top, which is not renamed, moved or deleted."""
        relative = SandboxHomePath.of(path)
        if relative == ".":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The top folder cannot be changed.")
        return relative

    @staticmethod
    def _conversation_titles(user: UserIdentity, folder_names: list[str]) -> dict[str, str]:
        """Conversation folders are named by thread id; only threads the user takes part in give their title."""
        ids = [ObjectId(name) for name in folder_names if ObjectId.is_valid(name)]
        threads = ThreadEntity.objects(id__in=ids, users__user_id=user.id).only("id", "name")
        return {str(thread.id): thread.name for thread in threads}
