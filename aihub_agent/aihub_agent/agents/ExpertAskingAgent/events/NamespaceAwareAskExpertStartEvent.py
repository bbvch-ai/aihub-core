from typing import Annotated

from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from pydantic import Field

from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent


class NamespaceAwareAskExpertStartEvent(AskExpertStartEvent):
    """Event representing a namespace-aware request to experts.

    Extends AskExpertStartEvent with namespace context for insight storage.
    When the expert provides a sufficient answer, the insight will be stored
    with the selected namespaces.
    """

    selected_namespaces: Annotated[
        list[BucketNamespacePair],
        Field(description="Selected namespaces for storing the resulting insight"),
    ]
