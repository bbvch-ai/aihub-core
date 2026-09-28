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
