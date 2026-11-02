from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlAndDisplayEvent
from swiss_ai_hub.core.generative_ai import IngestedNode

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class InOrderNodeCombinerEvent(ControlAndDisplayEvent):
    """
    Order the retrieved nodes by document source and combine them into a single chat message.

    Displayed because `grounding_nodes` is the one list of documents the model is handed, carried prior-turn ones
    included, so a chat client lists and numbers exactly the sources the answer can cite.
    """

    _display_name: ClassVar = AgentLocaleString.from_i18n_path("agent.events.in_order_node_combiner.name")
    _display_description: ClassVar = AgentLocaleString.from_i18n_path("agent.events.in_order_node_combiner.description")

    context_message: Annotated[
        ChatMessage, Field(description="The message including the context nodes information in order.")
    ]
    grounding_nodes: Annotated[
        list[IngestedNode] | None,
        Field(
            default=None,
            description="Nodes (fresh retrieval plus carried prior-turn nodes) that ground this turn's answer.",
        ),
    ] = None
