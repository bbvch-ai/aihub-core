from typing import Annotated, ClassVar

from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.user import UserMessageEvent
from pydantic import Field


class NamespaceAwareUserMessageEvent(UserMessageEvent):
    """User message event for RAG agent that includes pre-selected namespaces.

    This event extends UserMessageEvent to carry namespace selection information
    to the RAG agent. The selected_namespaces field contains a list of bucket-namespace
    pairs specifying which namespace to use for each bucket.
    """

    _display_name: ClassVar[LocaleString] = LocaleString(
        en="Namespace-Aware User Message Event",
        de="Namespace-bewusste Benutzernachricht",
        fr="Événement de message utilisateur avec namespace",
        it="Evento di messaggio utente con namespace",
    )
    _display_description: ClassVar[LocaleString] = LocaleString(
        en="A user message event with pre-selected namespaces for RAG retrieval.",
        de="Ein Benutzernachricht-Event mit vorausgewählten Namespaces für RAG-Retrieval.",
        fr="Un événement de message utilisateur avec des namespaces présélectionnés pour la récupération RAG.",
        it="Un evento di messaggio utente con namespace preselezionati per il recupero RAG.",
    )

    selected_namespaces: Annotated[
        list[BucketNamespacePair],
        Field(description="List of bucket-namespace pairs for RAG retrieval filtering."),
    ]
