from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.imap.unread_mail_summary import UnreadMailSummary
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class UnreadMailListedEvent(ControlAndDisplayEvent):
    """Carries the unread messages found in the configured inbox folder."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.unread_mail_listed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.unread_mail_listed_event.description"
    )

    messages: Annotated[
        list[UnreadMailSummary],
        Field(default_factory=list, description="Header summaries of the unread messages in the inbox."),
    ]
