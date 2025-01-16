import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from llama_index.core.base.llms.types import ChatMessage
from aihub_lib.persistence.rag.vectors.node_metadata import SECTION_START_LINE, SOURCE

scenarios("./features/agent_description_guard.feature")


@given("a locale handler", target_fixture="the_locale_handler")
def _():
    return LocaleHandler(locale="en")


@given(parsers.parse('a user query: "{query}"'))
def _(query: str):
    context_nodes = []
    for row in datatable[1:]:
        src = row[0]
        start_line = int(row[1])
        text = row[2]
        score = float(row[3])
        metadata = {}
        if src:
            metadata[SOURCE] = src
        metadata[SECTION_START_LINE] = start_line
        context_nodes.append(
            Document(id=f"{src or 'missing'}-{start_line}", score=score, content=text, metadata=metadata)
        )
    return context_nodes
