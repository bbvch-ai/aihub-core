from typing import Annotated, Literal, Self
from zoneinfo import available_timezones

from pydantic import Field, model_validator

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt, MinLen
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.select import Select
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

_DEFAULT_DRAFT_PROMPT = (
    "You draft concise, polite email replies for a human to review before sending. "
    "Reply in the same language as the original message, keep a professional tone, "
    "and never invent facts. Output only the reply body, without a subject line or signature. "
    "You may format it with Markdown (bold, lists); wrap text in ==double equals== only when asked to highlight it."
)

# Grounded drafting never leaves a message without a draft. That is not politeness: filing is this blueprint's only
# dedup, so a message that got no draft is filed, unflagged and never looked at again — it would fall between "drafted"
# and "untouched" and nothing would ever pick it back up. Two texts rather than one because the two situations are not
# the same fact: "we have nothing on file that answers this" is a true statement about the knowledge base, while a
# delegate that crashed tells the reviewer nothing except that the machinery broke, and reporting an outage as an
# absence of knowledge is how a broken deployment gets read as a working one.
_DEFAULT_NO_INFORMATION_DRAFT = (
    "Thank you for your message. We could not find reliable information in our documentation to answer it, so this "
    "draft has deliberately been left without an answer. Please reply personally."
)
_DEFAULT_GROUNDING_FAILED_DRAFT = (
    "Thank you for your message. This reply could not be prepared automatically because the knowledge lookup failed. "
    "Please reply personally, and let IT know if you see this repeatedly."
)

_DRAFT_ENABLED_REF = "draft_reply_enabled"
_VISIBLE_WHEN_ENABLED = f"$get({_DRAFT_ENABLED_REF}).value"
_QUOTE_ENABLED_REF = "draft_quote_original"
_VISIBLE_WHEN_QUOTING = f"{_VISIBLE_WHEN_ENABLED} && $get({_QUOTE_ENABLED_REF}).value"
_QUOTE_LOCALE_OPTIONS = [
    {"label": "Deutsch", "value": "de"},
    {"label": "English", "value": "en"},
    {"label": "Français", "value": "fr"},
    {"label": "Italiano", "value": "it"},
]
_DEFAULT_QUOTE_TIMEZONE = "Europe/Zurich"
_QUOTE_TIMEZONE_OPTIONS = sorted(available_timezones())

# Attachment parsing has its own switch nested under the section's: the caps below are meaningless unless
# attachments are being read at all, and showing five fields to an admin who left the toggle off is noise.
_ATTACHMENTS_ENABLED_REF = "draft_include_attachments"
_VISIBLE_WHEN_ATTACHMENTS_ENABLED = f"{_VISIBLE_WHEN_ENABLED} && $get({_ATTACHMENTS_ENABLED_REF}).value"


class DraftEmailSettings(StepConfig):
    """Configuration for the reply-drafting step — which model drafts the reply and where the draft lands. Grouped in
    the form as a single 'Draft email settings' section; the chat-LLM default parameters (temperature, timeout, …) are
    deliberately not exposed here.

    Two blueprints share these settings and each picks its own batch. `ImapAgent` drafts as an independent capability
    triggered by its own start event: it reads not-yet-drafted messages from `source_folder` (located and
    de-duplicated by an IMAP flag) and leaves the source mail unread. `EmailClassificationAgent` instead drafts the
    batch it has just classified, for the categories the admin opted into — there `source_folder` and `batch_size` are
    meaningless and are baked out of the rendered form, and filing rather than a flag is what stops a message being
    drafted twice.

    Either way the draft is appended to `drafts_folder` and nothing is ever sent; there is no SMTP path."""

    enable_draft: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Enable drafting a reply and appending it to the drafts folder. When off, the draft step is "
            "skipped.",
        ),
    ]
    source_folder: Annotated[
        str | InputText,
        Field(
            default="INBOX",
            description="Mailbox folder the drafter reads candidate messages from. Point it at the processed folder to "
            "draft mail filed there by the move step.",
        ),
    ]
    batch_size: Annotated[
        int | InputNumber,
        Field(default=5, description="Maximum number of messages drafted per run."),
        Gt(0),
    ]
    drafts_folder: Annotated[
        str | InputText,
        Field(
            default="Drafts",
            description="Mailbox folder reply drafts are appended to. If this name is not found on the server, its "
            "\\Drafts special-use folder (RFC 6154) is used instead.",
        ),
        MinLen(1),
    ]
    model_name: Annotated[
        str | ModelSelect,
        Field(default="", description="Chat LLM used to draft the reply body."),
    ]
    draft_prompt: Annotated[
        str | Textarea,
        Field(
            default=_DEFAULT_DRAFT_PROMPT,
            description="Instructions steering how the LLM drafts the reply body. The body is read as Markdown, with "
            "==text== highlighted in yellow, and rendered to sanitised HTML in the draft.",
        ),
    ]
    quote_original: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Quote the original message below the reply, with an Outlook-style header block. Added after "
            "the reply is generated, so the model never sees it twice and the reply does not change.",
        ),
    ]
    quote_locale: Annotated[
        Literal["de", "en", "fr", "it"] | Select,
        Field(
            default=LocaleHandler.DEFAULT_LOCALE,
            description="Language of the quoted header block's labels and date. Outlook writes them in the replier's "
            "language, which is the mailbox's, not the language a scheduled run happens to carry.",
        ),
    ]
    quote_timezone: Annotated[
        str | Select,
        Field(
            default=_DEFAULT_QUOTE_TIMEZONE,
            description="IANA timezone the quoted Sent date is shown in. Outlook shows it in the replier's zone, so a "
            "message sent at 15:05 +0700 reads 10:05 to a mailbox in Zurich, not the sender's wall-clock time.",
        ),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(
            default=32768,
            description="Input-token budget for the drafting prompt. The body is trimmed, and attachment extracts "
            "dropped, to stay within it.",
        ),
        Gt(0),
    ]
    no_information_draft: Annotated[
        str | Textarea,
        Field(
            default=_DEFAULT_NO_INFORMATION_DRAFT,
            description="Draft body used when retrieval found nothing that answers the message. Used verbatim — the "
            "model is never asked to write around an empty context, because an ungrounded reply that reads like a "
            "grounded one is worse than an honest blank.",
        ),
        MinLen(1),
    ]
    grounding_failed_draft: Annotated[
        str | Textarea,
        Field(
            default=_DEFAULT_GROUNDING_FAILED_DRAFT,
            description="Draft body used when the knowledge lookup itself failed or never answered. Kept apart from "
            "the no-information text so a reviewer can tell a gap in the documentation from a broken deployment.",
        ),
        MinLen(1),
    ]
    grounding_timeout_seconds: Annotated[
        int | InputNumber,
        Field(
            default=300,
            description="How long a knowledge lookup may take before the message is drafted with the failure text "
            "instead. A delegated agent that is offline or misconfigured never answers at all, and without a "
            "deadline the run waits for it forever — holding the mailbox and leaving a batch of already-filed mail "
            "with no drafts and no way to retry.",
        ),
        Gt(0),
    ]
    include_attachments: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Feed text extracted from the message's attachments into the drafting prompt. Off by "
            "default: parsing an attachment costs a document-parser round trip per attachment.",
        ),
    ]
    max_attachments_per_message: Annotated[
        int | InputNumber,
        Field(
            default=3,
            description="How many of a message's attachments are parsed, largest first. Bounds the parsing cost of a "
            "message carrying many files.",
        ),
        Gt(0),
    ]
    min_attachment_bytes: Annotated[
        int | InputNumber,
        Field(
            default=8192,
            description="Attachments smaller than this are not parsed at all. Signature logos and tracking pixels "
            "arrive as attachments; parsing them costs a round trip and yields nothing.",
        ),
        Gt(0),
    ]
    attachment_char_limit: Annotated[
        int | InputNumber,
        Field(
            default=20_000,
            description="Characters kept from a single attachment's extracted text, before the token budget applies.",
        ),
        Gt(0),
    ]

    @property
    def llm(self) -> LLMConfig:
        """The drafting LLM built from the selected model with default chat parameters (not form-configurable)."""
        return LLMConfig(model_name=self.model_name)

    @model_validator(mode="after")
    def _validate_quote_timezone(self) -> Self:
        """Reject an unknown zone when the profile is saved, not when a draft is first quoted with it."""
        if isinstance(self.quote_timezone, str) and self.quote_timezone not in available_timezones():
            raise ValueError(f"Unknown quote timezone: {self.quote_timezone!r}")
        return self

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            enable_draft=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.enable_draft.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.enable_draft.help"),
                ref=_DRAFT_ENABLED_REF,
            ),
            source_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.source_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.source_folder.help"),
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            batch_size=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.batch_size.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.batch_size.help"),
                min=1,
                step=1,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            drafts_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.drafts_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.drafts_folder.help"),
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.imap.config.draft_model.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.draft_model.help"),
                mode="chat",
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            draft_prompt=Textarea(
                label=LocaleString.from_i18n_path("lib.imap.config.draft_prompt.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.draft_prompt.help"),
                rows=6,
                auto_resize=True,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            quote_original=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.quote_original.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.quote_original.help"),
                ref=_QUOTE_ENABLED_REF,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            quote_locale=Select(
                label=LocaleString.from_i18n_path("lib.imap.config.quote_locale.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.quote_locale.help"),
                options=_QUOTE_LOCALE_OPTIONS,
                option_label="label",
                option_value="value",
                condition_if=_VISIBLE_WHEN_QUOTING,
            ),
            quote_timezone=Select(
                label=LocaleString.from_i18n_path("lib.imap.config.quote_timezone.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.quote_timezone.help"),
                options=_QUOTE_TIMEZONE_OPTIONS,
                filter=True,
                condition_if=_VISIBLE_WHEN_QUOTING,
            ),
            number_of_input_tokens=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.draft_input_tokens.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.draft_input_tokens.help"),
                min=1024,
                step=1024,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            no_information_draft=Textarea(
                label=LocaleString.from_i18n_path("lib.imap.config.no_information_draft.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.no_information_draft.help"),
                rows=4,
                auto_resize=True,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            grounding_failed_draft=Textarea(
                label=LocaleString.from_i18n_path("lib.imap.config.grounding_failed_draft.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.grounding_failed_draft.help"),
                rows=4,
                auto_resize=True,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            grounding_timeout_seconds=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.grounding_timeout_seconds.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.grounding_timeout_seconds.help"),
                min=1,
                step=30,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            include_attachments=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.include_attachments.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.include_attachments.help"),
                ref=_ATTACHMENTS_ENABLED_REF,
                condition_if=_VISIBLE_WHEN_ENABLED,
            ),
            max_attachments_per_message=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.max_attachments_per_message.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.max_attachments_per_message.help"),
                min=1,
                step=1,
                condition_if=_VISIBLE_WHEN_ATTACHMENTS_ENABLED,
            ),
            min_attachment_bytes=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.min_attachment_bytes.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.min_attachment_bytes.help"),
                min=1,
                step=1024,
                condition_if=_VISIBLE_WHEN_ATTACHMENTS_ENABLED,
            ),
            attachment_char_limit=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.attachment_char_limit.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.attachment_char_limit.help"),
                min=1,
                step=1000,
                condition_if=_VISIBLE_WHEN_ATTACHMENTS_ENABLED,
            ),
        )
