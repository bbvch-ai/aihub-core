from typing import Annotated, ClassVar

from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from aihub_lib.nats.events.user import UserMessageEvent
from pydantic import Field

from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class NamespaceAwareUserMessageEvent(UserMessageEvent):
    """User message event for RAG agent that includes pre-selected namespaces.

    This event extends UserMessageEvent to carry namespace selection information
    to the RAG agent. The selected_namespaces field contains a list of bucket-namespace
    pairs specifying which namespace to use for each bucket.
    """

    _display_name: ClassVar = AgentLocaleString.from_i18n_path("agent.events.namespace_aware_user_message.name")
    _display_description: ClassVar = AgentLocaleString.from_i18n_path(
        "agent.events.namespace_aware_user_message.description"
    )

    selected_namespaces: Annotated[
        list[BucketNamespacePair],
        Field(description="List of bucket-namespace pairs for RAG retrieval filtering."),
    ]
