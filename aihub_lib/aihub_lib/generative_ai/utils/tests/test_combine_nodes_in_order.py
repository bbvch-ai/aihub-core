import asyncio

import pytest
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.schema import NodeWithScore, TextNode
from pytest_bdd import given, scenarios, then, when

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    HEADING_LEVEL,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    SECTION_END_LINE,
    SECTION_START_LINE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION,
)

scenarios("./features/combine_nodes_in_order.feature")


@pytest.fixture
def locale_handler():
    class MockLocaleHandler(LocaleHandler):
        def __call__(self, key: str):
            if key == "agent.prompt.rag.context_prompt":
                return "Default prompt: {context_str}"
            return super().__call__(key)

    return MockLocaleHandler(locale="en")


@pytest.fixture
def no_context_prompt():
    return None


@pytest.fixture
def custom_prompt():
    return LocaleString(
        en="""Custom prompt: {% for block in context_blocks %}
{% if block.block_type == 'text' %}
{{ block.text }}
{% endif %}
{% if block.block_type == 'image' %}
{{ block.url.__str__() | image}}
{% endif %}
{% endfor %}
        """
    )


@given("a locale handler", target_fixture="the_locale_handler")
def _(locale_handler):
    return locale_handler


@given("no context prompt", target_fixture="the_context_prompt")
def _(no_context_prompt):
    return no_context_prompt


@given("a custom context prompt", target_fixture="the_context_prompt")
def _(custom_prompt):
    return custom_prompt


@given("the following context nodes:", target_fixture="the_context_nodes")
def _(datatable):
    context_nodes = []
    headers = datatable[0]
    metadata_fields = [
        DOCUMENT_ID,
        SOURCE,
        DOCUMENT_TITLE,
        NAMESPACE,
        TYPE,
        LANGUAGE,
        VERSION,
        CREATED_AT,
        UPDATED_AT,
        INSERTED_AT,
        SECTION_START_LINE,
        SECTION_END_LINE,
        HEADING_LEVEL,
        H1,
        H2,
        H3,
        H4,
        H5,
        H6,
    ]

    for row in datatable[1:]:
        metadata = {
            column: (
                int(row[index])
                if column
                in {VERSION, SECTION_START_LINE, SECTION_END_LINE, INSERTED_AT, UPDATED_AT, CREATED_AT, HEADING_LEVEL}
                else row[index]
            )
            for index, column in enumerate(headers)
            if row[index] and column in metadata_fields
        }

        text = row[headers.index("text")]
        score = None
        if "score" in headers:
            score_index = headers.index("score")
            if len(row) > score_index and row[score_index]:
                score = float(row[score_index])
        id_ = f"{metadata.get(SOURCE, 'missing')}-{metadata.get(SECTION_START_LINE, 0)}"
        context_nodes.append(
            IngestedNode.from_llama_index_node_with_score(
                NodeWithScore(
                    node=TextNode(text=text, metadata=metadata, id_=id_),
                    score=score,
                ),
            )
        )

    return context_nodes


@given("no context nodes", target_fixture="the_context_nodes")
def _():
    return []


@when("the combine_nodes_in_order function is called", target_fixture="the_result")
def _(the_context_nodes, the_locale_handler, the_context_prompt: LocaleString):
    try:
        return asyncio.run(
            combine_nodes_in_order(
                context_nodes=the_context_nodes, t=the_locale_handler, context_prompt=the_context_prompt
            )
        )
    except ValueError as e:
        return e


@then("it should return:")
def _(the_result, docstring):
    assert isinstance(the_result, ChatMessage)
    expected = "\n".join(line.rstrip() for line in docstring.strip().splitlines())
    actual = "\n".join(line.rstrip() for line in the_result.blocks[0].text.strip().splitlines())
    assert actual == expected, f"\nExpected:\n{expected}\n\nBut got:\n{actual}\n"
