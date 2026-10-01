from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile


class ReadAttachedFilesEvent(ControlEvent):
    """
    Asks the attached-files capability for the text of the files the user attached, sized to fit the prompt.

    Built with `AttachedFiles.read(...)`; answered with `AttachedFilesReadEvent`, empty when nothing readable is
    attached. It carries the history the files will be composed into, since that is what decides how much room
    the files have.
    """

    files: Annotated[list[UserUploadedFile], Field(description="The files attached to the current branch.")] = []
    history: Annotated[
        list[ChatMessage], Field(description="The history the files will be composed into, for sizing them.")
    ] = []
    query: Annotated[
        str, Field(description="The turn's query, for picking the relevant sections of a file too large to fit.")
    ] = ""
    reserve_tokens: Annotated[
        int,
        Field(
            description="Room the caller still needs after composing, e.g. for retrieved knowledge, which the files "
            "must leave free.",
            ge=0,
        ),
    ] = 0
    cite_sources: Annotated[
        bool,
        Field(description="Whether the model is told to cite the files by id, off where citations cannot resolve."),
    ] = True
