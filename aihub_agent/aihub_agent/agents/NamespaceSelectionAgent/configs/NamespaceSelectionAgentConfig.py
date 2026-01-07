from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from pydantic import Field

from aihub_agent.agents.NamespaceSelectionAgent.configs.RAGDelegationConfig import RAGDelegationConfig


class NamespaceSelectionAgentConfig(AgentConfig):
    """Configuration for NamespaceSelectionAgent.

    This agent prompts users to select namespaces from configured buckets
    on first interaction, stores the selection, and delegates subsequent
    queries to a configured RAG agent with the namespace selection.
    """

    bucket_names: Annotated[
        list[str],
        Field(description="List of bucket names to fetch namespaces from.", min_length=1),
    ]

    rag_delegation: Annotated[
        RAGDelegationConfig,
        Field(description="Configuration for delegating queries to the RAG agent."),
    ]

    selection_prompt: Annotated[
        LocaleString,
        Field(description="Message shown when asking user to select namespaces."),
    ] = LocaleString(
        en="Please select a namespace from each category below to focus your search:",
        de="Bitte wählen Sie einen Namespace aus jeder Kategorie aus, um Ihre Suche zu fokussieren:",
        fr="Veuillez sélectionner un namespace dans chaque catégorie ci-dessous pour cibler votre recherche :",
        it="Seleziona un namespace da ogni categoria qui sotto per focalizzare la tua ricerca:",
    )

    selection_confirmed_message: Annotated[
        LocaleString,
        Field(description="Message shown after namespace selection is stored."),
    ] = LocaleString(
        en="Your namespace selection has been saved. You can now ask your questions.",
        de="Ihre Namespace-Auswahl wurde gespeichert. Sie können jetzt Ihre Fragen stellen.",
        fr="Votre sélection de namespace a été enregistrée. Vous pouvez maintenant poser vos questions.",
        it="La tua selezione del namespace è stata salvata. Ora puoi fare le tue domande.",
    )
