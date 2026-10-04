from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler


class AttachedFilesToolArguments(BaseModel):
    """What the model passes when it chooses to read the files the user attached."""

    files: Annotated[
        list[str] | None, Field(description="Which attached files to read, by id; all of them when omitted.")
    ] = None
    query: Annotated[
        str, Field(description="What the model looks for, so a file too large to read whole keeps the sections on it.")
    ] = ""

    @staticmethod
    def schema_for(file_ids: list[str], t: LocaleHandler) -> dict[str, Any]:
        """The schema the model sees, the attached files spelled out so it can only pick among them."""
        return {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {"type": "string", "enum": file_ids},
                    "description": t("agent.attached_files.tool.files"),
                },
                "query": {"type": "string", "description": t("agent.attached_files.tool.query")},
            },
        }
