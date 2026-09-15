from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.core.form.constraints import MinLen
from swiss_ai_hub.core.form.elements.input_text import InputText
from swiss_ai_hub.core.form.elements.knowledge_collection_selector import KnowledgeCollectionSelector
from swiss_ai_hub.core.form.elements.textarea import Textarea
from swiss_ai_hub.core.form.elements.toggle_switch import ToggleSwitch
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class MailCategory(Form):
    """One mail category: a name, the folder its mail is filed into, what belongs in it, and whether it gets a reply.

    The description is what makes classification work. A model cannot reliably choose between `information_request`
    and `support_request` from folder names alone, but it can from "we can resolve this by providing information"
    versus "this requires an action from our team". Categories are configuration, not a fixed taxonomy, so a customer
    adds or renames one without a deployment.

    `draft_reply` is per category because the value of a drafted reply is: a `complaint` usually warrants one, a
    `thanking` mail rarely does. Mail no category fitted goes to the fallback folder and is therefore never drafted —
    the opt-in lives on the category, and uncategorised mail has none.

    `knowledge_namespaces` is what keeps a grounded reply precise. Whether replies are grounded at all is the
    profile's knowledge agent to decide; what a category decides is how far retrieval is narrowed. Left off, the
    reply is answered from everything that agent retrieves from. Turned on, it is answered from the collections named
    here and no others — which is what lets a `support_request` retrieve support material and nothing else, selected
    by the category verdict.
    """

    category: Annotated[
        str | InputText,
        Field(description="Category name, e.g. 'support_request'. Must be unique within the agent."),
        MinLen(1),
    ]
    imap_folder: Annotated[
        str | InputText,
        Field(description="Mailbox folder messages in this category are filed into. Created if it does not exist."),
        MinLen(1),
    ]
    description: Annotated[
        str | Textarea,
        Field(description="What belongs in this category — this is what the model classifies on."),
        MinLen(1),
    ]
    draft_reply: Annotated[
        bool | ToggleSwitch,
        Field(
            default=False,
            description="Draft a reply for mail filed under this category and leave it in the drafts folder for a "
            "human to review and send. Mail is never sent.",
        ),
    ]
    knowledge_namespaces: Annotated[
        list[BucketNamespacePair] | KnowledgeCollectionSelector | None,
        Field(
            default=None,
            description="Knowledge collections this category's replies are answered from. Left off, the reply is "
            "answered from every collection the profile's knowledge agent retrieves from; turned on, retrieval is "
            "narrowed to the collections named here and no others.",
        ),
    ] = None

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            category=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.category_name.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.category_name.help"),
            ),
            imap_folder=InputText(
                label=LocaleString.from_i18n_path("lib.imap.config.category_folder.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.category_folder.help"),
            ),
            description=Textarea(
                label=LocaleString.from_i18n_path("lib.imap.config.category_description.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.category_description.help"),
                rows=3,
                auto_resize=True,
            ),
            draft_reply=ToggleSwitch(
                label=LocaleString.from_i18n_path("lib.imap.config.category_draft_reply.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.category_draft_reply.help"),
            ),
            knowledge_namespaces=KnowledgeCollectionSelector(
                label=LocaleString.from_i18n_path("lib.imap.config.category_knowledge_namespaces.label"),
                help=LocaleString.from_i18n_path("lib.imap.config.category_knowledge_namespaces.help"),
                placeholder=LocaleString.from_i18n_path("lib.imap.config.category_knowledge_namespaces.placeholder"),
                # Only ever evaluated while the enable toggle is on, since the toggle unmounts the field: switched
                # on and left empty is the one state that reads like narrowing and silently retrieves everything, so
                # it is rejected in the form rather than by the run that would have been answered too widely.
                additional_validation_rules="required",
            ),
        )
