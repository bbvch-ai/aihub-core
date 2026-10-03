from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.user_knowledge.dto.file_entry_dto import FileEntryDTO


class FolderListingDTO(BaseModel):
    folder: Annotated[str, Field(description="The listed folder, relative to the user's file space; '.' is its top.")]
    entries: Annotated[list[FileEntryDTO], Field(description="Its folders first, then its files, each by name.")]
    folder_title: Annotated[
        str | None, Field(description="The title of the chat, when the folder is a conversation's own.")
    ] = None
