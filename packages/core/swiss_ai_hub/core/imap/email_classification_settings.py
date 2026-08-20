from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import MinLen
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.model_select import ModelSelect
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.imap.mail_category import MailCategory

_DEFAULT_CLASSIFICATION_PROMPT = (
    "You are a mailroom clerk. Read the message and decide which single category it belongs to, using the category "
    "descriptions as your only criteria. Judge the sender's intent, not individual keywords. If no category clearly "
    "fits, say so instead of guessing — misfiled mail costs more than uncategorised mail."
)

_DEFAULT_FALLBACK_FOLDER = "Uncategorised"


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
    fallback_folder: Annotated[
        str | InputText,
        Field(
            default=_DEFAULT_FALLBACK_FOLDER,
            description="Folder for mail the model is not confident about. Never left in the inbox, never guessed "
            "into a category.",
        ),
        MinLen(1),
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
            fallback_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.help"),
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
