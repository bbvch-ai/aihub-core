from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.imap.drafted_reply_ref import DraftedReplyRef
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MailBatchDraftedEvent(ControlAndDisplayEvent):
    """Records that a batch of reply drafts was appended to the Drafts folder for a human to review and send.

    The agent never sends — the drafts sitting in Drafts are the human handoff. Each source message is left unread and
    marked as drafted so it is not drafted again on the next run.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.mail_batch_drafted_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.mail_batch_drafted_event.description"
    )

    source_folder: Annotated[str, Field(description="Folder the drafted messages were read from.")]
    count: Annotated[int, Field(description="Number of reply drafts created in this run.")]
    per_category: Annotated[
        dict[str, int],
        Field(
            default_factory=dict,
            description="How many drafts were created for each category, when drafting followed a classification "
            "run. Empty when the drafting blueprint does not classify.",
        ),
    ]
    skipped_count: Annotated[
        int,
        Field(
            default=0,
            description="Messages in the batch that got no draft: usually because their category was not opted in, "
            "or no category fitted them at all.",
        ),
    ]
    drafted: Annotated[
        list[DraftedReplyRef],
        Field(default_factory=list, description="Per-message references to the created reply drafts."),
    ]
