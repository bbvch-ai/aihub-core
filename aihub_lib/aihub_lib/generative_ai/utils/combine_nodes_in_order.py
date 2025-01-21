from collections import defaultdict
from typing import List

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.vectors.node_metadata import H1, H2, H3, H4, H5, H6, SECTION_START_LINE, SOURCE

_headers_in_order = [H6, H5, H4, H3, H2, H1]


def combine_nodes_in_order(
    context_nodes: List[Document],
    locale_handler: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document = defaultdict(list)
    for context_node in context_nodes:
        if not context_node.metadata or SOURCE not in context_node.metadata:
            raise ValueError(f"Context node must contain metadata {SOURCE}")
        key = context_node.metadata.get(SOURCE)
        nodes_per_document[key].append(context_node)

    documents = []
    for key, nodes in nodes_per_document.items():
        text_parts = [f"<DOC START: {key}>\n\n"]
        sorted_nodes = sorted(nodes, key=lambda x: x.metadata.get(SECTION_START_LINE, 0))
        for n in sorted_nodes:
            text_parts.append(f"{n.content}\n\n")
        text_parts.append(f"<DOC END: {key}>\n")
        text_parts.append("\n---\n")
        documents.append("".join(text_parts))

    if context_prompt:
        context_prompt_locale = LocaleHandler(locale_handler.locale).extract(context_prompt, locale_handler.locale)
    else:
        context_prompt_locale = locale_handler("agent.prompt.rag_agent.context_prompt")
    return ChatMessage(
        role=MessageRole.SYSTEM,
        content=context_prompt_locale.format(context_str="".join(documents)),
    )
