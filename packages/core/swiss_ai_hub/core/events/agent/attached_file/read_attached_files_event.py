from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ReadAttachedFilesEvent(ControlAndDisplayEvent):
    """
    Asks the attached-files capability for the text of the files the user attached, sized to fit the prompt.

    Built with `AttachedFiles.read(...)`; answered with `AttachedFilesReadEvent`, empty when nothing readable is
    attached. It carries the history the files will be composed into, since that is what decides how much room
    the files have.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.read_attached_files_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.read_attached_files_event.description"
    )

    files: Annotated[list[UserUploadedFile], Field(description="The files attached to the current branch.")] = []
    history: Annotated[
        list[ChatMessage], Field(description="The history the files will be composed into, for sizing them.")
    ] = []
    query: Annotated[
        str, Field(description="The turn's query, for picking the relevant sections of a file too large to fit.")
    ] = ""
    first_page: Annotated[
        int | None,
        Field(description="The first page to read when the question is about certain pages; any page otherwise.", ge=1),
    ] = None
    last_page: Annotated[
        int | None,
        Field(description="The last page to read; `first_page` alone when none.", ge=1),
    ] = None
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
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose it in a tool loop; none otherwise."),
    ] = None
