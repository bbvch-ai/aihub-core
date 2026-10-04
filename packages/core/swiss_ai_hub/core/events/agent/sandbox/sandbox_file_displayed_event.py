from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class SandboxFileDisplayedEvent(DisplayEvent):
    """The agent showed the user a file from their code sandbox, copied into our storage so it outlives the sandbox.

    Chat clients attach it to the answer: OpenWebUI registers it as one of the message's files.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.sandbox_file_displayed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.sandbox_file_displayed_event.description"
    )

    path: Annotated[str, Field(description="Where the file lies in the user's sandbox home.")]
    filename: Annotated[str, Field(description="The file's name, as the attachment shows it.")]
    content_type: Annotated[str, Field(description="The file's MIME type.")]
    size: Annotated[int, Field(description="The file's size in bytes.", ge=0)]
    bucket: Annotated[str, Field(description="The bucket holding the copy.")]
    key: Annotated[str, Field(description="The copy's key within the bucket.")]
