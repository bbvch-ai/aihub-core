from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.attached_file.attached_file_status import AttachedFileStatus
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class AttachedFileEvent(DisplayEvent):
    """
    One file the user attached to the conversation, as the agent read it for this turn.

    Chat clients render it as a source on the answer, so the user sees which files the answer drew on and whether
    all of each file fit, and the trace shows exactly what the model read. `file_id` is the agent-side upload id; a
    client that uploaded the file maps it back to its own record. `citation_id` is what the answer cites.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.attached_file_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.attached_file_event.description"
    )

    file_id: Annotated[str, Field(description="The agent-side id of the uploaded file.")]
    filename: Annotated[str, Field(description="The file's name as the user uploaded it.")]
    status: Annotated[AttachedFileStatus, Field(description="Whether the file was read whole, in part, or not.")]
    number_of_pages: Annotated[int | None, Field(description="Pages in the document, when the parser knows.")] = None
    citation_id: Annotated[str, Field(description="The id the answer cites this file by, as [id].")] = ""
    content: Annotated[
        str, Field(description="The text of the file as the model received it: whole, excerpts, or its beginning.")
    ] = ""
    error: Annotated[str | None, Field(description="Why the file could not be read, for a failed file.")] = None
