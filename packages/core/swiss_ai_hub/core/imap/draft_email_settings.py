from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n.locale_string import LocaleString

_DEFAULT_DRAFT_PROMPT = (
    "You draft concise, polite email replies for a human to review before sending. "
    "Reply in the same language as the original message, keep a professional tone, "
    "and never invent facts. Output only the reply body, without a subject line or signature."
)

_DRAFT_ENABLED_REF = "draft_reply_enabled"
_VISIBLE_WHEN_ENABLED = f"$get({_DRAFT_ENABLED_REF}).value"


class DraftEmailSettings(StepConfig):
    """Configuration for the reply-drafting step — which model drafts the reply and where the draft lands. Grouped in
    the form as a single 'Draft email settings' section; the chat-LLM default parameters (temperature, timeout, …) are
    deliberately not exposed here.

    Drafting is an independent capability triggered by its own start event: it reads a batch of not-yet-drafted
    messages from `source_folder` (located and de-duplicated by an IMAP flag), drafts a reply for each, and leaves the
    source mail unread."""

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
    ]
    model_name: Annotated[
        str | ModelSelect,
        Field(default="", description="Chat LLM used to draft the reply body."),
    ]
    draft_prompt: Annotated[
        str | Textarea,
        Field(default=_DEFAULT_DRAFT_PROMPT, description="Instructions steering how the LLM drafts the reply body."),
    ]

    @property
    def llm(self) -> LLMConfig:
        """The drafting LLM built from the selected model with default chat parameters (not form-configurable)."""
        return LLMConfig(model_name=self.model_name)

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
        )
