from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import Checkbox, InputText
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class KnowledgeDocumentConfig(Form):
    """Whether the model may work on whole knowledge documents, and on which part of each collection.

    The documents come from the collections the knowledge tool lists, narrowed to what the asking user may read; the
    glob limits them further, before anything reaches the model, so a model can only narrow it.
    """

    enabled: Annotated[
        bool | Checkbox,
        Field(description="Let the model list, search and read whole documents of the knowledge collections."),
    ] = False
    path_glob: Annotated[
        str | InputText | None,
        Field(description="Only documents whose path in its collection matches this glob, e.g. 'invoices/**'."),
    ] = None
    narrow_references: Annotated[
        bool,
        Field(description="Whether `#` references only pick among the configured collections instead of adding some."),
    ] = False
    semantic_search: Annotated[
        bool | Checkbox,
        Field(
            description="Also let the model rank the documents within the path filter by meaning (vector search "
            "grouped by document), which finds documents that do not use the request's words."
        ),
    ] = False

    @classmethod
    def as_form(cls) -> Self:
        """Without `semantic_search`: only a blueprint whose prompt leads the model through the ranking offers it, by
        adding `semantic_search_input()` to its own form."""
        return cls(
            enabled=Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.enabled.label"),
                help=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.enabled.help"),
            ),
            path_glob=cls.path_glob_input(),
        )

    @staticmethod
    def semantic_search_input() -> Checkbox:
        return Checkbox(
            label=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.semantic_search.label"),
            help=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.semantic_search.help"),
        )

    @staticmethod
    def path_glob_input() -> InputText:
        return InputText(
            label=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.path_glob.label"),
            help=AgentLocaleString.from_i18n_path("agent.knowledge_documents.config.path_glob.help"),
        )
