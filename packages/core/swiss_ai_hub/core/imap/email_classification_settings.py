from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.agents.agent_config import StepConfig
from swiss_ai_hub.core.form.constraints import Gt, MinLen
from swiss_ai_hub.core.form.elements.input_number import InputNumber
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.knowledge_database_selector import KnowledgeDatabaseSelector
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
_DEFAULT_FAILURE_FOLDER = "Classification failed"


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
    knowledge_databases: Annotated[
        list[str] | KnowledgeDatabaseSelector,
        Field(
            default_factory=list,
            title="Knowledge databases",
            description="Databases the categories' collections are looked up in. Needed only when a category names a "
            "collection: a collection name alone does not identify a database, and the RAG agent's retrievers are "
            "keyed by database.",
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
            knowledge_databases=KnowledgeDatabaseSelector(
                label=LocaleString.from_i18n_path("lib.imap.config.knowledge_databases.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.knowledge_databases.help"),
            ),
            fallback_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.fallback_folder.help"),
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
