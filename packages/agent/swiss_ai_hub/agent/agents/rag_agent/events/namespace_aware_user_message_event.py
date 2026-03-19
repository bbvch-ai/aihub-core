from typing import Annotated, ClassVar

from pydantic import Field
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.generative_ai import BucketNamespacePair

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


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
