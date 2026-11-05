from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt, MinLen
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.imap.mail_category import MailCategory

_DEFAULT_CLASSIFICATION_PROMPT = (
    "You are a mailroom clerk. Read the message and decide which single category it belongs to, using the category "
    "descriptions as your only criteria. Judge the sender's intent, not individual keywords. If no category clearly "
    "fits, say so instead of guessing — misfiled mail costs more than uncategorised mail."
)

_DEFAULT_FALLBACK_FOLDER = "Uncategorised"
_DEFAULT_FAILURE_FOLDER = "Classification failed"

_KEEP_UNCATEGORISED_REF = "classification_keep_uncategorised"


class EmailClassificationSettings(StepConfig):
    """Category taxonomy and classifier behaviour for the email classification agent.

    Grouped in the form as one 'Email classification' section. The classifier model is optional: left empty it falls
    back to the agent's main model, mirroring how `task_llm` falls back to `llm` elsewhere.
    """

    categories: Annotated[
        list[MailCategory],
        Field(
            default_factory=list,
            title="Categories",
            description="Categories mail is sorted into. Each needs a folder and a description of what belongs in it.",
        ),
    ]

    keep_uncategorised_in_inbox: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Leave mail that fits no category unread in the inbox instead of moving it to the fallback "
            "folder. It is remembered as processed by an inbox watermark, not by a flag, because Microsoft 365 "
            "accepts no custom IMAP keywords.",
        ),
    ]
    fallback_folder: Annotated[
        str | InputText,
        Field(
            default=_DEFAULT_FALLBACK_FOLDER,
            description="Folder for mail the model is not confident about, never guessed into a category. Unused "
            "while uncategorised mail is kept in the inbox.",
        ),
        MinLen(1),
    ]
    failure_folder: Annotated[
        str | InputText,
        Field(
            default=_DEFAULT_FAILURE_FOLDER,
            description="Folder for mail the classifier could not reach a verdict on at all — a model or gateway "
            "failure, not a decline. Kept apart from the fallback folder so an operator can find and retry it, and "
            "so one unclassifiable message cannot sit unread in the inbox blocking every run behind it.",
        ),
        MinLen(1),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(
            default=8192,
            description="Input-token budget for the classification prompt. The message body is trimmed to fit it. "
            "Far smaller than the drafting budget is enough: classification reads the sender, the subject and the "
            "opening of the body, not the whole thread.",
        ),
        Gt(0),
    ]
    model_name: Annotated[
        str | ModelSelect,
        Field(default="", description="Chat model used to classify. Leave empty to use the agent's main model."),
    ]
    classification_prompt: Annotated[
        str | Textarea,
        Field(default=_DEFAULT_CLASSIFICATION_PROMPT, description="Instructions steering how the model classifies."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            categories=[MailCategory.as_form()],
            keep_uncategorised_in_inbox=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.keep_uncategorised_in_inbox.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.keep_uncategorised_in_inbox.help"),
                ref=_KEEP_UNCATEGORISED_REF,
            ),
            fallback_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.help"),
                condition_if=f"$get({_KEEP_UNCATEGORISED_REF}).value !== true",
            ),
            failure_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.failure_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.failure_folder.help"),
            ),
            number_of_input_tokens=InputNumber(
                label=LocaleString.from_i18n_path("lib.imap.config.classification_input_tokens.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.classification_input_tokens.help"),
                min=1024,
                step=1024,
            ),
            model_name=ModelSelect(
                label=LocaleString.from_i18n_path("lib.imap.config.classification_model.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.classification_model.help"),
                mode="chat",
            ),
            classification_prompt=Textarea(
                label=LocaleString.from_i18n_path("lib.imap.config.classification_prompt.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.classification_prompt.help"),
                rows=6,
                auto_resize=True,
            ),
        )
