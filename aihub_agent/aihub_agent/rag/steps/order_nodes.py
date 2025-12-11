from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from llama_index.core.schema import NodeWithScore

from aihub_agent.rag.events import InOrderNodeCombinerEvent


async def execute_order_nodes_by_documents(
    nodes: list[NodeWithScore],
    t: LocaleHandler,
    displayer: EventDisplayer,
    context_prompt: LocaleString | None = None,
) -> InOrderNodeCombinerEvent:
    """
    Orders the retrieved nodes based on their source documents.
    """
    await displayer.display_thought(t("agent.thought.searching_knowledge"))
    ordered_nodes = combine_nodes_in_order(
        context_nodes=nodes,
        t=t,
        context_prompt=context_prompt,
    )
    return InOrderNodeCombinerEvent(context_message=ordered_nodes)
