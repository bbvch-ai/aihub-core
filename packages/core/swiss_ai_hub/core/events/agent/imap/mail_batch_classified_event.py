from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.imap.mail_classification_ref import MailClassificationRef
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MailBatchClassifiedEvent(ControlAndDisplayEvent):
    """Summarises one classification run: how many messages were classified and where each was filed.

    One event per run rather than one per message, matching `MailBatchDraftedEvent` — the per-message detail rides in
    `classified`. Filing is what prevents reprocessing: every message leaves the source folder, so the next unread
    listing cannot see it again.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.mail_batch_classified_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.mail_batch_classified_event.description"
    )

    source_folder: Annotated[str, Field(description="Folder the classified messages were read from.")]
    count: Annotated[int, Field(description="Number of messages classified and filed in this run.")]
    per_category: Annotated[
        dict[str, int],
        Field(default_factory=dict, description="How many messages were filed under each configured category."),
    ]
    fallback_count: Annotated[
        int, Field(default=0, description="How many messages went to the fallback folder instead of a category.")
    ]
    failed_count: Annotated[
        int,
        Field(
            default=0,
            description="How many messages the classifier could not reach a verdict on at all. They are filed into "
            "the failure folder rather than left in the inbox, where they would be re-selected on every run forever.",
        ),
    ]
    classified: Annotated[
        list[MailClassificationRef],
        Field(default_factory=list, description="Per-message classification verdicts and filing destinations."),
    ]
