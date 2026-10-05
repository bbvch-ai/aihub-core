import posixpath
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, Field


class FileEntryDTO(BaseModel):
    name: Annotated[str, Field(description="The file or folder name.")]
    path: Annotated[str, Field(description="Its path relative to the user's file space.")]
    kind: Annotated[Literal["file", "folder"], Field(description="Whether it is a file or a folder.")]
    size: Annotated[int | None, Field(description="The file's size in bytes; none for a folder.")] = None
    modified: Annotated[float, Field(description="When it last changed, as seconds since the epoch.")]
    conversation_title: Annotated[
        str | None, Field(description="The title of the chat a conversation folder belongs to.")
    ] = None

    @classmethod
    def from_entry(cls, folder: str, entry: dict[str, Any], conversation_title: str | None = None) -> Self:
        folder_kind = entry["type"] == "directory"
        return cls(
            name=entry["name"],
            path=posixpath.normpath(posixpath.join(folder, entry["name"])),
            kind="folder" if folder_kind else "file",
            size=None if folder_kind else entry.get("size"),
            modified=entry.get("modified", 0),
            conversation_title=conversation_title,
        )
